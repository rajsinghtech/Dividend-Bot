FROM python:3.9-slim
WORKDIR /app
COPY ./main.py /app/main.py
RUN pip install --no-cache-dir requests tweepy datetime
CMD ["python3", "app.py"]