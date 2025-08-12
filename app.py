from fastapi import FastAPI
import requests
import os
import logging

app = FastAPI()

# Configuração de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asaas-api")

# URL da API sandbox do Asaas
BASE_URL = "https://api-sandbox.asaas.com/v3"
ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")  # Configure essa var no ambiente (ex: Render)

HEADERS = {
    "accept": "application/json",
    "access_token": ASAAS_API_KEY
}

# Parâmetros fixos
FIXED_PARAMS = {
    "startDate": "2025-08-01",
    "finishDate": "2025-08-12",
    "order": "desc"
}

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

    # Transforma lista de dicionários em array de arrays
    if data_all:
        keys = list(data_all[0].keys())
        array_de_arrays = [keys]
        for item in data_all:
            array_de_arrays.append([item.get(k) for k in keys])
        return array_de_arrays
    else:
        return []

@app.get("/extrato")
def get_extrato():
    return fetch_paginated("/financialTransactions", FIXED_PARAMS)

@app.get("/")
def home():
    return {"status": "API do Asaas rodando no Render com parâmetros fixos (sem type)"}

