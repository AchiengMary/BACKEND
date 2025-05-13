# email_utils.py

import aiosmtplib
from email.message import EmailMessage
from pydantic import EmailStr

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "achieng4024mary@gmail.com"      
SMTP_PASSWORD = "cyfr nbfz usao dduv"

async def send_verification_email(email: EmailStr, code: str):
    message = EmailMessage()
    message["From"] = SMTP_USER
    message["To"] = email
    message["Subject"] = "Your Verification Code"
    message.set_content(f"Your 2-step verification code is: {code}")

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        start_tls=True,
        username=SMTP_USER,
        password=SMTP_PASSWORD,
    )
