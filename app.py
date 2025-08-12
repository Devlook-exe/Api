from fastapi import FastAPI
import requests
import os
import json
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asaas-api")

# Asaas
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

# Google Sheets
SPREADSHEET_ID = "1KEX0jFv2t8x7dSpbItVvCg_f3Xru_wHP-RjKH8dPdM4"
RANGE_NAME = "Extrato!A1"

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
    json_str = os.getenv("GOOGLE_SERVICE_ACCOUNT")

    if not json_str:
        logger.error("Variável de ambiente GOOGLE_SERVICE_ACCOUNT não foi definida.")
        return {"error": "GOOGLE_SERVICE_ACCOUNT não definida"}

    try:
        credentials_info = json.loads(json_str)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
    except Exception as e:
        logger.error(f"Erro ao carregar credenciais do Google: {str(e)}")
        return {"error": "Falha ao carregar credenciais do Google", "detalhes": str(e)}

    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()

    body = {
        "values": values
    }

    result = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption="RAW",
        body=body
    ).execute()

    logger.info(f"{result.get('updatedCells')} células atualizadas no Google Sheets.")
    return result

@app.get("/extrato")
def get_extrato():
    data = fetch_paginated("/financialTransactions", FIXED_PARAMS)
    if isinstance(data, dict) and data.get("error"):
        return data

    write_result = write_to_sheets(data)
    if isinstance(write_result, dict) and write_result.get("error"):
        return write_result

    return {
        "message": "Dados inseridos no Google Sheets com sucesso",
        "updatedCells": write_result.get('updatedCells')
    }

@app.get("/")
def home():
    return {"status": "API do Asaas rodando no Render com parâmetros fixos"}
