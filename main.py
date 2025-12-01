from fastapi import FastAPI, Request, BackgroundTasks
from pydantic import BaseModel
import logging
from gemini_client import gemini_client
from goftino_client import goftino_client
from system_prompt import SYSTEM_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class WebhookData(BaseModel):
    event: str
    data: dict

@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        logger.info(f"Received webhook: {payload}")
        
        event = payload.get('event')
        data = payload.get('data')

        if event == 'new_message':
            sender = data.get('sender', {})
            sender_from = sender.get('from')
            
            # Only reply if the message is NOT from an operator (to avoid loops)
            if sender_from != 'operator':
                chat_id = data.get('chat_id')
                content = data.get('content')
                
                if chat_id and content:
                    # Process in background to avoid blocking the webhook response
                    background_tasks.add_task(process_message, chat_id, content)
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}

def process_message(chat_id, user_message):
    logger.info(f"Processing message for chat {chat_id}: {user_message}")
    
    # 1. Fetch history (optional, but good for context)
    # For now, let's just use the current message + system prompt to ensure speed and simplicity first.
    # If we want history, we'd call goftino_client.get_chat_history(chat_id)
    # But we need to be careful about the order and formatting.
    
    # Let's try to get history.
    history = goftino_client.get_chat_history(chat_id)
    
    # Filter out the current message if it's already in history (it might be)
    # Goftino history might include the message that just triggered the webhook.
    # We'll just pass the history to Gemini. GeminiClient handles formatting.
    
    # If history is empty or failed, just use the current message.
    if not history:
        history = []
    
    # Check if the last message in history is the same as user_message
    if history and history[-1]['role'] == 'user' and history[-1]['content'] == user_message:
        history.pop()

    # Prepend System Prompt?
    # Gemini API usually takes system instructions separately or as the first 'user'/'model' exchange.
    # The google-generativeai library has a 'system_instruction' parameter in GenerativeModel, 
    # but our client initializes the model inside the method.
    # Let's modify GeminiClient to accept system prompt or prepend it to history.
    
    # For now, I'll prepend it to the prompt sent to the model, or as the first history item.
    # Best practice with this lib:
    # model = genai.GenerativeModel(MODEL_NAME, system_instruction=SYSTEM_PROMPT)
    
    # I need to update GeminiClient to support system_instruction.
    
    try:
        # We will update GeminiClient to take system_prompt.
        # For now, let's assume we pass it or handle it there.
        # Let's pass the system prompt as part of the context if the client doesn't support it yet.
        
        # Actually, let's update GeminiClient first to be cleaner.
        # But for now, I'll just call get_response.
        
        response_text = gemini_client.get_response(user_message, history=history, system_prompt=SYSTEM_PROMPT)
        
        if response_text:
            goftino_client.send_message(chat_id, response_text)
            
    except Exception as e:
        logger.error(f"Error generating/sending response: {e}")

@app.get("/")
def health_check():
    return {"status": "running"}
