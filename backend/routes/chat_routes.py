import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage
from agents.agent_service import checkout_agent
from utils.websocket_manager import manager

router = APIRouter()

HEARTBEAT_INTERVAL_SECONDS = 20  # itni der tak koi message na aaye toh ek ping bhej do

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
            # Frontend se data receive karo — agar HEARTBEAT_INTERVAL_SECONDS tak kuch
            # nahi aaya, ek ping bhej do taaki koi bhi proxy/browser is connection ko
            # "idle" samajh kar khud band na kar de
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(), timeout=HEARTBEAT_INTERVAL_SECONDS
                )
            except asyncio.TimeoutError:
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
                continue
            
            try:
                parsed_data = json.loads(data)
                msg_type = parsed_data.get("type")
                cart_data = parsed_data.get("cart", [])
                
                # Sync frontend cart to backend DB
                from config.database import db_connection
                from models.user import User, UserRole
                from sqlmodel import select
                from repositories.cart_repository import cart_repository
                
                # Ensure the user exists in the DB (for guests) to satisfy the foreign key constraint
                async with db_connection.get_session() as session:
                    existing_user = await session.exec(select(User).where(User.id == user_id))
                    if not existing_user.first():
                        guest_user = User(id=user_id, name=f"Guest {user_id}", role=UserRole.CUSTOMER, identifier=f"guest_{user_id}@dukaan.local")
                        session.add(guest_user)
                        await session.commit()
                
                await cart_repository.clear_cart(user_id)
                for item in cart_data:
                    await cart_repository.add_item(
                        user_id=user_id,
                        product_id=int(item["id"]),
                        quantity=item.get("qty", 1),
                        size=item.get("size")
                    )
                
                # 1. Proactive Monitoring (Background Events)
                if msg_type == "monitoring_event":
                    event_name = parsed_data.get("event")
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
                                    "combo_offer": result.get("combo_offer", None),
                                    "suggested_products": result.get("suggested_products", [])
                                }, user_id)
                        except WebSocketDisconnect:
                            raise
                        except Exception as e:
                            print(f"[ERROR] Proactive suggestion failed: {e}")
                            import traceback
                            traceback.print_exc()
                            
                    continue
                    
                # 2. Direct User Chat (Negotiation, Search, etc.)
                elif msg_type == "chat":
                    chat_text = parsed_data.get("text", "")
                    human_msg = HumanMessage(content=chat_text)
                else:
                    continue
                    
            except json.JSONDecodeError:
                # Fallback for plain text just in case
                human_msg = HumanMessage(content=data)
            
            initial_state = {
                "messages": [human_msg],
                "user_id": user_id
            }
            
            try:
                result = await checkout_agent.ainvoke(initial_state, config=config)
                ai_reply = result.get("final_response", "Sorry, system error.")
                combo_offer = result.get("combo_offer", None)
                suggested_products = result.get("suggested_products", [])
                
                await manager.send_message({
                    "type": "chat_reply", 
                    "message": ai_reply,
                    "combo_offer": combo_offer,
                    "suggested_products": suggested_products
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
            
    except (WebSocketDisconnect, RuntimeError):
        manager.disconnect(user_id)
    except Exception as e:
        print(f"[ERROR] WebSocket loop exited with error: {e}")
        manager.disconnect(user_id)
