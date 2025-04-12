import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
    SHEET_NAME = os.getenv('SHEET_NAME', 'Sheet1')
    TIMEZONE = os.getenv('TIMEZONE', 'UTC')
    SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_PATH')
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'changeme')
