import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-me'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/eventdb'

    # Add these lines with YOUR details:
    MAIL_FROM = 'tteddy2004bear@gmail.com'        # ← Your Gmail
    SMTP_HOST = 'smtp.gmail.com'
    SMTP_PORT = 587
    SMTP_TLS = True
    SMTP_USER = 'tteddy2004bear@gmail.com'        # ← Same Gmail
    SMTP_PASSWORD = 'xyzn vypf znfn pyje'