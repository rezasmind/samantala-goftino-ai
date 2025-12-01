import google.generativeai as genai
import random
import time
import logging

# List of API keys provided
API_KEYS = [
    "AIzaSyCsTZRCyS3BZoIcQ778u5iUKUPyAFIEm4k",
    "AIzaSyBByNLJE3pT7IC04rhx48vkScN_jBoBAUc",
    "AIzaSyAkK8ayg4qoDAqx88UiwXYaW5HA6CmqGlk",
    "AIzaSyCFiB7kMJ9VWH5a4WNfP66MXi9YAbbpJBU",
    "AIzaSyBkVF6qbjxdN3zLhem2jFngtmAwxNrheqk"
]

MODEL_NAME = "models/gemini-flash-lite-latest"

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self.api_keys = API_KEYS.copy()
        random.shuffle(self.api_keys) # Shuffle initially

    def get_response(self, prompt, history=[], system_prompt=None):
        """
        Generates a response from Gemini, rotating keys on failure.
        """
        # Prepare chat history for Gemini
        # Gemini expects history in the format: [{'role': 'user', 'parts': ['...']}, {'role': 'model', 'parts': ['...']}]
        formatted_history = []
        for msg in history:
            role = "user" if msg['role'] == 'user' else "model"
            formatted_history.append({"role": role, "parts": [msg['content']]})

        # Try keys until one works or all fail
        tried_keys = 0
        while tried_keys < len(self.api_keys):
            current_key = self.api_keys[0]
            try:
                genai.configure(api_key=current_key)
                if system_prompt:
                    model = genai.GenerativeModel(MODEL_NAME, system_instruction=system_prompt)
                else:
                    model = genai.GenerativeModel(MODEL_NAME)
                
                chat = model.start_chat(history=formatted_history)
                response = chat.send_message(prompt)
                
                return response.text
            except Exception as e:
                logger.error(f"Error with API key ending in ...{current_key[-4:]}: {e}")
                # Rotate key to the end
                self.api_keys.append(self.api_keys.pop(0))
                tried_keys += 1
                time.sleep(1) # Brief pause before retry
        
        raise Exception("All Gemini API keys failed.")

gemini_client = GeminiClient()
