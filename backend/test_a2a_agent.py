import asyncio
import httpx
import json

async def test_agent_interaction():
    start_url = "http://127.0.0.1:8000/a2a/start_session"
    interact_url = "http://127.0.0.1:8000/a2a/interact"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("🚀 Starting session...")
            start_res = await client.post(start_url)
            start_data = start_res.json()
            chat_token = start_data.get("chat_token")
            print(f"🔑 Received Chat Token: {chat_token}")
            
            payload = {
                "chat_token": chat_token,
                "intent": "I want to buy some jeans. What options do you have? Add the first one to my cart.",
                "context": {}
            }
            
            print(f"\n[Buyer Agent] Sending intent: '{payload['intent']}'")
            
            response = await client.post(interact_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                print("\n[Dukaan Agent] Reply Received:")
                print(json.dumps(data, indent=2))
            else:
                print(f"Error: Server returned status {response.status_code}")
                print(response.text)
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent_interaction())
