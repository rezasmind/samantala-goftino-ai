import requests
import logging

logger = logging.getLogger(__name__)

GOFTINO_API_KEY = "jklbljb23fl9snkj1j44f6el16fed1bdc36368a4dca6099eb2cc88a91ad7943e"
BASE_URL = "https://api.goftino.com/v1"

class GoftinoClient:
    def __init__(self):
        self.headers = {
            "goftino-key": GOFTINO_API_KEY,
            "Content-Type": "application/json"
        }
        self.operator_id = None

    def get_operator_id(self):
        if self.operator_id:
            return self.operator_id
        
        try:
            response = requests.get(f"{BASE_URL}/operators", headers=self.headers)
            response.raise_for_status()
            data = response.json()
            if data['status'] == 'success' and data['data']['operators']:
                # Pick the first operator. Ideally, this should be a specific bot operator.
                self.operator_id = data['data']['operators'][0]['operator_id']
                logger.info(f"Using operator ID: {self.operator_id}")
                return self.operator_id
            else:
                logger.error("No operators found or failed to fetch operators.")
                return None
        except Exception as e:
            logger.error(f"Error fetching operators: {e}")
            return None

    def send_message(self, chat_id, message):
        operator_id = self.get_operator_id()
        if not operator_id:
            logger.error("Cannot send message: No operator ID available.")
            return False

        payload = {
            "chat_id": chat_id,
            "operator_id": operator_id,
            "message": message
        }

        try:
            response = requests.post(f"{BASE_URL}/send_message", headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            if result['status'] == 'success':
                logger.info(f"Message sent to chat {chat_id}")
                return True
            else:
                logger.error(f"Failed to send message: {result}")
                return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    def get_chat_history(self, chat_id):
        try:
            # Fetch last 10 messages
            response = requests.get(f"{BASE_URL}/chat_data?chat_id={chat_id}&limit=10", headers=self.headers)
            response.raise_for_status()
            data = response.json()
            if data['status'] == 'success':
                messages = data['data']['messages']
                # Sort by date (oldest first)
                messages.sort(key=lambda x: x.get('date', ''))
                
                # We need to convert them to the format expected by GeminiClient: {'role': 'user'/'model', 'content': '...'}
                formatted_history = []
                for msg in messages:
                    # Determine role
                    # If sender is operator, it's the model. Otherwise it's the user.
                    sender_from = msg.get('sender', {}).get('from')
                    role = 'model' if sender_from == 'operator' else 'user'
                    
                    content = msg.get('content', '')
                    if msg.get('type') == 'text' and content:
                         formatted_history.append({'role': role, 'content': content})
                
                return formatted_history
            return []
        except Exception as e:
            logger.error(f"Error fetching chat history: {e}")
            return []

goftino_client = GoftinoClient()
