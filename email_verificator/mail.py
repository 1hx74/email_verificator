import os
import smtplib

from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from dotenv import load_dotenv


load_dotenv()

GMAIL = os.environ["GMAIL"]
APP_PASSWORD = os.environ["APP_PASSWORD"]

CODE_TTL = int(os.environ["CODE_TTL"])
HTML_FILE = Path(__file__).parent / "verification.html"
HTML_TEMPLATE = HTML_FILE.read_text(encoding="utf-8")


def send_email(to: str, code: str):
    ttl_minutes = str(int(CODE_TTL / 60))

    body = HTML_TEMPLATE.replace("{{CODE}}", code).replace("{{TTL}}", ttl_minutes)

    msg = MIMEMultipart("alternative")

    msg["From"] = GMAIL
    msg["To"] = to
    msg["Subject"] = Header("Код подтверждения", "utf-8")

    text = f"Ваш код подтверждения: {code}\nКод действителен {ttl_minutes} минут."

    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL, APP_PASSWORD)
        smtp.send_message(msg)