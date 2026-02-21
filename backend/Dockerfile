# Берем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем библиотеки
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код бэкенда
COPY . .

# Открываем порт, на котором будет работать FastAPI
EXPOSE 8000

# Команда для запуска сервера (та самая!)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]