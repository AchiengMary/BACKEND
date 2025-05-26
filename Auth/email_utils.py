import aiosmtplib
from email.message import EmailMessage
from pydantic import EmailStr
from datetime import datetime  # Added to format timestamp

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "achieng4024mary@gmail.com"
SMTP_PASSWORD = "cyfr nbfz usao dduv"

async def send_verification_email(email: EmailStr, code: str):
    message = EmailMessage()
    message["From"] = f"Davis & Shirtliff <{SMTP_USER}>"
    # message["From"] = SMTP_USER
    message["To"] = email
    # Use f-string to embed formatted timestamp
    message["Subject"] = f"Davis & Shirtliff Login: Your Verification Code - {datetime.utcnow().strftime('%m-%d %M:%S')}"

    # Plain text fallback
    message.set_content(
        f"Hello,\n\nUse the code below to log in to your Davis & Shirtliff account:\n\n{code}\n\nThis code expires in 2 minutes.\n\nDidn't request this code? Contact us at contactcenter@dayliff.com"
    )

    # HTML version
    message.add_alternative(f"""\
<html>
  <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 30px;">
    <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 10px; padding: 30px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
      <div style="text-align: center; margin-bottom: 20px;">
        <img src="https://www.davisandshirtliff.com/images/logo.png" alt="Davis & Shirtliff" width="150">
      </div>
      <h2 style="text-align: center; color: #333;">Hello,</h2>
      <p style="font-size: 16px; color: #555; text-align: center;">
        Use the code below to log in to your Davis & Shirtliff account.
      </p>
      <div style="text-align: center; margin: 30px 0;">
        <div style="display: inline-block; padding: 20px 30px; background-color: #f0f0f0; border-radius: 8px;">
          <span style="font-size: 32px; font-weight: bold; color: #333; letter-spacing: 4px;">{code}</span>
        </div>
      </div>
      <p style="text-align: center; color: #999;">This code expires in 2 minutes.</p>
      <p style="text-align: center; font-size: 14px;">
        Didn't request this code? <a href="mailto:contactcenter@dayliff.com">Contact us</a>.
      </p>
    </div>
  </body>
</html>
""", subtype="html")

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        start_tls=True,
        username=SMTP_USER,
        password=SMTP_PASSWORD,
    )
