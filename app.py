from datetime import datetime
from zoneinfo import ZoneInfo
import io, base64

from flask import Flask, session, redirect, url_for, request, render_template
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import qrcode

from config import Config

app = Flask(__name__)
app.config.from_object(Config)

creds = Credentials.from_service_account_file(
    app.config['SERVICE_ACCOUNT_FILE'],
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
sheets_api = build('sheets', 'v4', credentials=creds).spreadsheets()

def get_column_letter(idx: int) -> str:
    if idx < 1:
        return ''
    res = ''
    while idx:
        idx, rem = divmod(idx-1, 26)
        res = chr(65 + rem) + res
    return res

def get_headers() -> list[str]:
    resp = sheets_api.values().get(
        spreadsheetId=app.config['SPREADSHEET_ID'],
        range=f"{app.config['SHEET_NAME']}!1:1"
    ).execute()
    return resp.get('values', [[]])[0]

@app.before_request
def require_login():
    if request.endpoint not in ('login', 'static') and not session.get('logged_in'):
        return redirect(url_for('login', next=request.path))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        u = request.form.get('username', '')
        p = request.form.get('password', '')
        if u == app.config['ADMIN_USERNAME'] and p == app.config['ADMIN_PASSWORD']:
            session['logged_in'] = True
            session['username'] = u
            next_page = request.args.get('next')
            if not next_page:
                return render_template(
                    'log.html',
                    message='Logged in successfully',
                    category='success',
                    title='Logged‑in'
                )
            return redirect(next_page)
        else:
            error = 'Incorrect Username or Password'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/createnewuser', methods=['GET', 'POST'])
def create_new_user():
    error = ''
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            error = 'Name cannot be empty.'
            return render_template('createnewuser.html', error=error)
        names = sheets_api.values().get(
            spreadsheetId=app.config['SPREADSHEET_ID'],
            range=f"{app.config['SHEET_NAME']}!A:A",
            majorDimension='COLUMNS'
        ).execute().get('values', [[]])[0]
        if name in names:
            error = f'User "{name}" already exists.'
            return render_template('createnewuser.html', error=error)
        sheets_api.values().append(
            spreadsheetId=app.config['SPREADSHEET_ID'],
            range=f"{app.config['SHEET_NAME']}!A:A",
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': [[name]]}
        ).execute()
        buf = io.BytesIO()
        url = request.url_root + 'log/' + name
        qrcode.make(url).save(buf, 'PNG')
        qr_b64 = base64.b64encode(buf.getvalue()).decode()
        return render_template('success.html', name=name, qr_code=qr_b64)
    return render_template('createnewuser.html', error=error)

@app.route('/log/<username>')
def update_cell(username):
    tz = ZoneInfo(app.config['TIMEZONE'])
    now = datetime.now(tz)
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%I:%M:%S %p')

    headers = get_headers()
    if date_str not in headers:
        meta = sheets_api.get(
            spreadsheetId=app.config['SPREADSHEET_ID'],
            fields='sheets.properties'
        ).execute()
        sheet_id = next(
            s['properties']['sheetId']
            for s in meta['sheets']
            if s['properties']['title'] == app.config['SHEET_NAME']
        )
        insert_at = len(headers)
        sheets_api.batchUpdate(
            spreadsheetId=app.config['SPREADSHEET_ID'],
            body={'requests': [{
                'insertDimension': {
                    'range': {
                        'sheetId': sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': insert_at,
                        'endIndex': insert_at + 1
                    },
                    'inheritFromBefore': True
                }
            }]}
        ).execute()
        new_col = get_column_letter(insert_at + 1)
        sheets_api.values().update(
            spreadsheetId=app.config['SPREADSHEET_ID'],
            range=f"{app.config['SHEET_NAME']}!{new_col}1",
            valueInputOption='RAW',
            body={'values': [[date_str]]}
        ).execute()
        headers = get_headers()

    col_idx = headers.index(date_str) + 1
    col_letter = get_column_letter(col_idx)
    names = sheets_api.values().get(
        spreadsheetId=app.config['SPREADSHEET_ID'],
        range=f"{app.config['SHEET_NAME']}!A:A",
        majorDimension='COLUMNS'
    ).execute().get('values', [[]])[0]

    if username not in names:
        return render_template(
            'log.html',
            message=f'User "{username}" was not found.',
            category='error',
            title='Not Found'
        )

    row_idx = names.index(username) + 1
    cell = f"{app.config['SHEET_NAME']}!{col_letter}{row_idx}"
    existing = sheets_api.values().get(
        spreadsheetId=app.config['SPREADSHEET_ID'],
        range=cell
    ).execute().get('values', [['']])[0][0]

    if existing.strip():
        return render_template(
            'log.html',
            message=f'{username} has already been logged at {existing}',
            category='info',
            title='Already Logged'
        )

    sheets_api.values().update(
        spreadsheetId=app.config['SPREADSHEET_ID'],
        range=cell,
        valueInputOption='USER_ENTERED',
        body={'values': [[time_str]]}
    ).execute()

    return render_template(
        'log.html',
        message=f'{username} has been logged successfully',
        category='success',
        title='Logged'
    )

if __name__ == '__main__':
    app.run(debug=True)
