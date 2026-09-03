import json
import re
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from agents.merchant.agent_state import AgentState
from agents.merchant.agent_prompts import get_system_prompt, get_system_reminder

def _extract_text(res) -> str:
    if isinstance(res, tuple):
        res = res[0]
    if isinstance(res, list) and res and isinstance(res[0], dict) and "text" in res[0]:
        return res[0]["text"]
    if isinstance(res, str):
        return res
    return json.dumps(res, default=str)

def _safe_parse(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None

def create_agent_node(fast_llm):
    async def agent_node(state: AgentState):
        messages = list(state["messages"])

        sys_msg = SystemMessage(content=get_system_prompt(
            user_id=state.get("user_id", 0)
        ))

        mod_messages = [sys_msg] + messages + [SystemMessage(content=get_system_reminder())]
        response = await fast_llm.ainvoke(mod_messages)

        print(f"\n[MERCHANT AGENT] Generated response.")
        if response.tool_calls:
            print(f"[MERCHANT AGENT] Decided to execute {len(response.tool_calls)} tools: {[t['name'] for t in response.tool_calls]}")
        elif response.content:
            print(f"[MERCHANT AGENT] Sending text response back to merchant.")

        final_text = response.content if not response.tool_calls else ""
        if isinstance(final_text, list):
            final_text = "\n".join([str(x) if isinstance(x, str) else x.get("text", "") for x in final_text if isinstance(x, (str, dict))])
        elif not isinstance(final_text, str):
            final_text = str(final_text)

        if final_text:
            final_text = re.sub(r'<thought>.*?</thought>', '', final_text, flags=re.DOTALL).strip()

        updates = {"messages": [response], "final_response": final_text}
        return updates
    return agent_node

def create_tools_node(tools_dict):
    async def tools_node(state: AgentState):
        last_message = state["messages"][-1]
        tool_messages, updates = [], {}

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = dict(tool_call["args"])

            print(f"[TOOL START] Executing '{tool_name}' with args: {tool_args}")

            tool = tools_dict.get(tool_name)
            if tool is None:
                print(f"[TOOL ERROR] Unknown tool '{tool_name}'")
                tool_messages.append(ToolMessage(content='{"error": "Unknown tool"}', tool_call_id=tool_call["id"]))
                continue

            try:
                # MCP tools sometimes expect input_data wrappers or are fine with direct kwargs.
                raw_res = await tool.ainvoke(tool_args)
            except Exception as e:
                print(f"[TOOL ERROR] Exception in '{tool_name}': {str(e)}")
                tool_messages.append(ToolMessage(content=f'{{"error": "{str(e)}"}}', tool_call_id=tool_call["id"]))
                continue

            res_text = _extract_text(raw_res)
            
            # Print truncated result for logging
            log_res = res_text if len(res_text) < 300 else res_text[:300] + "... [TRUNCATED]"
            print(f"[TOOL FINISHED] '{tool_name}' returned: {log_res}")

            tool_messages.append(ToolMessage(content=res_text, tool_call_id=tool_call["id"]))

        updates["messages"] = tool_messages
        return updates
    return tools_node
