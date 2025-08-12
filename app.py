from fastapi import FastAPI
import requests
import os
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asaas-api")

BASE_URL = "https://api-sandbox.asaas.com/v3"
ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")

HEADERS = {
    "accept": "application/json",
    "access_token": ASAAS_API_KEY
}

FIXED_PARAMS = {
    "startDate": "2025-06-01",
    "finishDate": "2025-08-12",
    "order": "desc"
}

# Variáveis para Google Sheets
SERVICE_ACCOUNT_FILE = "path/to/your/service-account.json"  # Substitua pelo caminho real
SPREADSHEET_ID = "sua_planilha_id_aqui"  # Coloque o ID da sua planilha
RANGE_NAME = "Sheet1!A1"  # Intervalo para começar a inserir dados

def fetch_paginated(endpoint: str, params: dict):
    data_all = []
    offset = 0

    while True:
        paginated_params = params.copy()
        paginated_params.update({"limit": 100, "offset": offset})

        resp = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS, params=paginated_params)

        if resp.status_code != 200:
            logger.error(f"Erro Asaas ({resp.status_code}): {resp.text}")
            return {"error": f"Erro {resp.status_code}", "detalhes": resp.text}

        json_resp = resp.json()

        logger.info(f"Resposta Asaas (offset={offset}): {json_resp}")

        data_all.extend(json_resp.get("data", []))

        if not json_resp.get("hasMore"):
            break

        offset += 100

    if data_all:
        keys = list(data_all[0].keys())
        array_de_arrays = [keys]
        for item in data_all:
            array_de_arrays.append([item.get(k) for k in keys])
        return array_de_arrays
    else:
        return []

def write_to_sheets(values):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()

    body = {
        "values": values
    }

    result = sheet.values().update(
        spreadsheetId=1KEX0jFv2t8x7dSpbItVvCg_f3Xru_wHP-RjKH8dPdM4,
        range=Extrato!A1,
        valueInputOption="RAW",
        body=body
    ).execute()

    logger.info(f"{result.get('updatedCells')} células atualizadas no Google Sheets.")
    return result

@app.get("/extrato")
def get_extrato():
    data = fetch_paginated("/financialTransactions", FIXED_PARAMS)
    if isinstance(data, dict) and data.get("error"):
        return data  # Retorna erro da API Asaas

    write_result = write_to_sheets(data)
    return {
        "message": "Dados inseridos no Google Sheets com sucesso",
        "updatedCells": write_result.get('updatedCells')
    }

@app.get("/")
def home():
    return {"status": "API do Asaas rodando no Render com parâmetros fixos (sem type)"}

