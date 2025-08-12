from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# Coloque aqui o ID da sua planilha
SPREADSHEET_ID = '1KEX0jFv2t8x7dSpbItVvCg_f3Xru_wHP-RjKH8dPdM4'

# Nome da aba onde vai inserir os dados
SHEET_NAME = 'Extrato'

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'service-account.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('sheets', 'v4', credentials=credentials)
sheet = service.spreadsheets()

@app.route('/extrato', methods=['POST'])
def extrato():
    data = request.get_json()

    if not isinstance(data, list) or len(data) == 0:
        return jsonify({"error": "JSON deve ser uma lista de objetos com dados"}), 400

    headers = list(data[0].keys())
    values = [headers] + [[item.get(key, "") for key in headers] for item in data]

    range_ = f'{SHEET_NAME}!A1'

    body = {'values': values}

    result = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_,
        valueInputOption='RAW',
        body=body
    ).execute()

    return jsonify({
        "updatedRange": result.get('updatedRange'),
        "updatedRows": result.get('updatedRows'),
        "updatedColumns": result.get('updatedColumns'),
        "updatedCells": result.get('updatedCells')
    })

if __name__ == '__main__':
    app.run(debug=True)

