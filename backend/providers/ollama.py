import requests
import time
import logging
import json

# Настроим простой логгер, чтобы в консоли видеть время ответа
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class OllamaProvider:
    # При инициализации указываем адрес контейнера (ollama:11434) и имя модели
    def __init__(self, base_url: str = "http://ollama:11434", model: str = "qwen2.5:0.5b"):
        self.base_url = base_url
        self.model = model

    def generate(self, messages: list[dict], temperature: float = 0.7) -> str:
        """
        Метод принимает историю сообщений (контекст) и отправляет в Ollama.
        """
        if len(messages) > 20:
            messages = messages[-20:]
            
        total_length = sum(len(m.get("content", "")) for m in messages)
        if total_length > 8000:
            raise ValueError("Слишком длинный контекст сообщения. Превышен лимит в 8000 символов.")

        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        logger.info(f"Отправляем запрос в Ollama (модель: {self.model})...")
        start_time = time.time()

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()

            data = response.json()
            latency = time.time() - start_time
            logger.info(f"Ollama ответила за {latency:.2f} сек.")

            return data.get("message", {}).get("content", "")

        except Exception as e:
            logger.error(f"Ошибка при вызове Ollama API: {e}")
            raise e

    # ИСПРАВЛЕНИЕ: Теперь метод находится на правильном уровне внутри класса
    def generate_stream(self, messages: list[dict], temperature: float = 0.7):
        """
        Генерирует ответ потоком (стриминг).
        Возвращает генератор, который выдает текст по кусочкам.
        """
        if len(messages) > 20:
            messages = messages[-20:]
            
        total_length = sum(len(m.get("content", "")) for m in messages)
        if total_length > 8000:
            raise ValueError("Слишком длинный контекст сообщения. Превышен лимит в 8000 символов.")

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,  # НОВОЕ: Говорим Ollama отдавать по одному слову
            "options": {
                "temperature": temperature
            }
        }

        logger.info(f"Начинаем стриминг из Ollama (модель: {self.model})...")

        # ИСПРАВЛЕНИЕ: Тело функции сдвинуто вправо, как требует Python
        try:
            with requests.post(url, json=payload, stream=True, timeout=60) as response:
                response.raise_for_status()

                # Читаем ответ построчно по мере его поступления
                for line in response.iter_lines():
                    if line:
                        # Ollama присылает JSON-строку на каждый сгенерированный токен
                        chunk = json.loads(line)
                        text_piece = chunk.get("message", {}).get("content", "")

                        if text_piece:
                            # yield выплевывает кусочек текста наружу, но не завершает функцию!
                            yield text_piece
        except Exception as e:
            logger.error(f"Ошибка стриминга Ollama API: {e}")
            raise e