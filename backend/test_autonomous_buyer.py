import os
import time
import requests
import json
from dotenv import load_dotenv

# Import Langchain and our project's chatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from config.chatModel import chatModel

# Load environment variables
load_dotenv()

# We will use our own OpenRouter configuration
OPEN_ROUTER_KEY = os.getenv("OPEN_ROUTER_KEY")
if not OPEN_ROUTER_KEY:
    print("Error: Please set OPEN_ROUTER_KEY in your .env file.")
    exit(1)

# Ensure the env var is set for Langchain
os.environ["OPENROUTER_API_KEY"] = OPEN_ROUTER_KEY

# The URL of your Dukaan AI (Seller Agent)
SELLER_AI_URL = "https://dukaan-avbodh.onrender.com/a2a/interact/message:send"

def send_message_to_seller(text: str) -> str:
    """Sends an A2A JSON request to the Dukaan backend and returns the response text."""
    payload = {
        "message": {
            "role": "user",
            "parts": [{"text": text}]
        },
        "metadata": {
            "context_id": "test_autonomous_buyer_001"
        }
    }
    
    print(f"[📡 Sending API Request to Dukaan...]")
    response = requests.post(SELLER_AI_URL, json=payload)
    
    try:
        data = response.json()
        # Parse the standard A2A response
        parts = data.get("message", {}).get("parts", [])
        reply_text = ""
        for part in parts:
            if "text" in part:
                reply_text += part["text"] + " "
        return reply_text.strip()
    except Exception as e:
        return f"Error connecting to Dukaan: {e}"

def run_autonomous_buyer():
    print("🤖 Autonomous Buyer Agent Started...")
    print("Goal: Buy Blue Jeans, get a discount, and checkout.")
    print("---------------------------------------------------")
    
    # Initialize the Buyer's Brain using our project's ChatModel
    buyer_llm = chatModel.get_chat_model()
    
    # The persona and instructions for our Buyer AI
    system_prompt = """You are a smart Personal Shopping Assistant AI for a customer named Tanishq.
Tanishq has instructed you to buy a pair of Blue Jeans from an online store.
You are talking to the store's AI (Seller AI).

Your instructions:
1. Start by asking to see some blue jeans.
2. When the seller shows you options, pick one (e.g., GAP or LEVI's).
3. Specify the size (e.g. size 32).
4. Ask for a discount or combo offer.
5. Finally, ask to checkout.

Keep your messages very short, direct, and conversational (1-2 sentences max).
Do not break character. Do not talk to Tanishq, talk ONLY to the Seller AI."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="START CONVERSATION. Say hello and ask for what you need.")
    ]
    
    # Chat Loop: Let the AIs talk for a maximum of 6 turns
    for turn in range(6):
        print(f"\n--- Turn {turn + 1} ---")
        
        # 1. Buyer AI generates what to say using Langchain
        response = buyer_llm.invoke(messages)
        buyer_text = response.content.strip()
        
        # Log it in the conversation history
        print(f"🛒 [Buyer AI]: {buyer_text}")
        
        # 2. Send the Buyer AI's text to Dukaan's Seller AI via A2A API
        seller_reply = send_message_to_seller(buyer_text)
        print(f"🛍️ [Dukaan Seller AI]:\n{seller_reply}")
        
        # 3. Add both messages to the Buyer AI's memory so it knows how to reply next
        messages.append(AIMessage(content=buyer_text))
        messages.append(HumanMessage(content=f"Seller AI says: {seller_reply}"))
        
        # If the seller gives a checkout link or order confirmation, we can stop
        if "order" in seller_reply.lower() and "checkout" in seller_reply.lower():
            print("\n✅ Goal Achieved! Checkout complete.")
            break
            
        time.sleep(2) # Pause for 2 seconds to not spam the server

if __name__ == "__main__":
    run_autonomous_buyer()
