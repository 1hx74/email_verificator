import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from dotenv import load_dotenv


load_dotenv()

GMAIL = os.environ["GMAIL"]
APP_PASSWORD = os.environ["APP_PASSWORD"]


def send_email(to: str, subject: str, text: str):
    msg = MIMEText(text, "plain", "utf-8")
    msg["From"] = GMAIL
    msg["To"] = to
    msg["Subject"] = Header(subject, "utf-8")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL, APP_PASSWORD)
        smtp.send_message(msg)


if __name__ == "__main__":
    send_email(
        to="maryin.kolya2017@gmail.com",
        subject="Тест",
        text="gjrf! Это письмо отправлено автоматически из Python."
    )