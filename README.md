A simple Flask app to register users in Google Sheets and generate per‑user QR codes that log timestamps.

## Features

- Admin‑protected interface to add new users
- Automatically creates a new date‑column in Sheets on first log of each day
- QR codes point to `/log/<username>` to record a timestamp in the sheet
- Basic flash messaging for success/info/warning/error

## Google Service Account
    Create a service account in Google Cloud Console.
    Enable Google Sheets API
    Grant it “Editor” access to your target Spreadsheet.
    Download the JSON and set SERVICE_ACCOUNT_PATH in your .env.

## Getting Started

git clone https://github.com/your‑username/my‑qr‑logger.git
cd my‑qr‑logger
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py