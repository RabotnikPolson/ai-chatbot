import requests
import time
import logging
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class OllamaProvider:
    def __init__(self, base_url: str = "http://ollama:11434", model: str = "qwen2.5:0.5b"):
        self.base_url = base_url
        self.model = model

    def generate(self, messages: list[dict], temperature: float = 0.7) -> str:

        if len(messages) > 20:
            messages = messages[-20:]
            
        total_length = sum(len(m.get("content", "")) for m in messages)
        if total_length > 8000:
            raise ValueError("Message context is too long. Limit is 8000 characters.")

        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        logger.info(f"Sending request to Ollama (model: {self.model})...")
        start_time = time.time()

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()

            data = response.json()
            latency = time.time() - start_time
            logger.info(f"Ollama replied in {latency:.2f}s.")

            return data.get("message", {}).get("content", "")

        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            raise e

    def generate_stream(self, messages: list[dict], temperature: float = 0.7):

        if len(messages) > 20:
            messages = messages[-20:]
            
        total_length = sum(len(m.get("content", "")) for m in messages)
        if total_length > 8000:
            raise ValueError("Message context is too long. Limit is 8000 characters.")

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }

        logger.info(f"Starting Ollama stream (model: {self.model})...")

        try:
            with requests.post(url, json=payload, stream=True, timeout=60) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        text_piece = chunk.get("message", {}).get("content", "")

                        if text_piece:
                            yield text_piece
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise e