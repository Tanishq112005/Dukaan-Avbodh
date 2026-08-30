import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage
from agents.agent_service import checkout_agent
from utils.websocket_manager import manager

router = APIRouter()

@router.websocket("/ws/chat/{user_id}")
async def websocket_chat_endpoint(websocket: WebSocket, user_id: int):
    """
    Live WebSocket connection for Continuous AI Monitoring & Chat.
    Render (Free Tier) supports WebSockets perfectly for this hackathon!
    """
    await manager.connect(websocket, user_id)
    
    # LangGraph ki memory (MemorySaver) ko is thread_id se pta chalega ki yeh kiska chat history hai
    config = {"configurable": {"thread_id": str(user_id)}}
    
    try:
        while True:
            # Frontend se data receive karo
            data = await websocket.receive_text()
            
            # 1. Proactive Monitoring (Background Events)
            try:
                parsed_data = json.loads(data)
                if parsed_data.get("type") == "monitoring_event":
                    event_name = parsed_data.get("event")
                    cart_data = parsed_data.get("cart", [])
                    
                    if event_name in ["idle_timeout", "viewed_multiple_products", "viewed_checkout", "activity_threshold_reached"]:
                        hidden_msg = HumanMessage(content="PROACTIVE_SUGGESTION_TRIGGER")
                        
                        try:
                            result = await checkout_agent.ainvoke({
                                "messages": [hidden_msg],
                                "user_id": user_id
                            }, config=config)
                            
                            ai_reply = result.get("final_response")
                            if ai_reply:
                                await manager.send_message({
                                    "type": "proactive_suggestion",
                                    "message": ai_reply,
                                    "combo_offer": result.get("combo_offer", None) 
                                }, user_id)
                        except WebSocketDisconnect:
                            raise
                        except Exception as e:
                            print(f"[ERROR] Proactive suggestion failed: {e}")
                            import traceback
                            traceback.print_exc()
                            
                    continue
            except json.JSONDecodeError:
                pass
                
            # 2. Direct User Chat (Negotiation, Search, etc.)
            human_msg = HumanMessage(content=data)
            
            initial_state = {
                "messages": [human_msg],
                "user_id": user_id
            }
            
            try:
                result = await checkout_agent.ainvoke(initial_state, config=config)
                ai_reply = result.get("final_response", "Sorry, system error.")
                combo_offer = result.get("combo_offer", None)
                
                await manager.send_message({
                    "type": "chat_reply", 
                    "message": ai_reply,
                    "combo_offer": combo_offer
                }, user_id)
            except WebSocketDisconnect:
                raise
            except Exception as e:
                print(f"[ERROR] Chat agent failed: {e}")
                import traceback
                traceback.print_exc()
                try:
                    await manager.send_message({"type": "chat_reply", "message": "Sorry, something went wrong. Please try again!"}, user_id)
                except Exception:
                    pass
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
