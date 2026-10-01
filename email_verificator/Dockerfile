FROM python:3.12-slim

WORKDIR /app

COPY email_verificator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY email_verificator/ .

EXPOSE 2345

CMD ["python", "main.py"]