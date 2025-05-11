
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from fastapi import FastAPI

app = FastAPI()

@app.get("/status")
def get_status():
    return {
        "ativo": False,
        "modo": "agressivo",
        "moedas_monitoradas": ["BTCUSDT", "ETHUSDT"],
        "valor_disponivel": 150.0
    }
