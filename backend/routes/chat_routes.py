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
                    
                    # Agar user ne kuch time se interact nahi kiya ya naya page khola ya checkout/activity limit pahunchi:
                    if event_name in ["idle_timeout", "viewed_multiple_products", "viewed_checkout", "activity_threshold_reached"]:
                        # Hidden trigger to graph to run 'recommendNode' proactively
                        hidden_msg = HumanMessage(content="PROACTIVE_SUGGESTION_TRIGGER")
                        
                        # Graph run karo
                        result = await checkout_agent.ainvoke({
                            "messages": [hidden_msg],
                            "user_id": user_id,
                            "cart": cart_data
                        }, config=config)
                        
                        ai_reply = result.get("final_response")
                        if ai_reply:
                            await manager.send_message({
                                "type": "proactive_suggestion",
                                "message": ai_reply,
                                "combo_offer": result.get("combo_offer", None) 
                            }, user_id)
                            
                    continue # Wait for next message
            except json.JSONDecodeError:
                pass # Normal text chat hai, koi JSON event nahi
                
            # 2. Direct User Chat (Negotiation, Search, etc.)
            human_msg = HumanMessage(content=data)
            
            # TODO: Ideal case mein cart database se aayega. 
            # Abhi ke liye hum assume kar rahe hain state empty se shuru hogi, 
            # ya previous thread_id state use karegi.
            initial_state = {
                "messages": [human_msg],
                "user_id": user_id,
                "cart": [] # Fill this with actual cart items from DB in production
            }
            
            # Graph run karo
            result = await checkout_agent.ainvoke(initial_state, config=config)
            ai_reply = result.get("final_response", "Sorry, system error.")
            
            # User ko reply bhejo
            await manager.send_message({"type": "chat_reply", "message": ai_reply}, user_id)
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
