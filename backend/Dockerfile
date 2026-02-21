FROM python:3.11-slim

#  dir in container
WORKDIR /app

# copy files with dependinces
COPY requirements.txt .

# install all lib from file
RUN pip install --no-cache-dir -r requirements.txt

# copy all from "backend" folder
COPY . .

# open port where app work
EXPOSE 8000

# cl for execute
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]