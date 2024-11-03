FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN /bin/sh -c pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
