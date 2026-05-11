FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY order_server.py api_server.py ./
ENV DB_HOST=db
EXPOSE 8000
CMD ["python", "api_server.py"]
