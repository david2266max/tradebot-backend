from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Middleware para permitir acesso externo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado simulado do bot
estado_bot = {
    "ativo": False,
    "modo": "agressivo",
    "moedas_monitoradas": ["BTCUSDT", "ETHUSDT"],
    "valor_disponivel": 150.0,
    "operacoes": [
        {"symbol": "BTCUSDT", "preco": "62000", "data": "2025-05-10", "acao": "COMPRA"},
        {"symbol": "ETHUSDT", "preco": "3200", "data": "2025-05-10", "acao": "VENDA"}
    ]
}

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/status")
def get_status():
    return {
        "ativo": estado_bot["ativo"],
        "modo": estado_bot["modo"],
        "moedas_monitoradas": estado_bot["moedas_monitoradas"],
        "valor_disponivel": estado_bot["valor_disponivel"]
    }

@app.get("/operacoes")
def get_operacoes():
    return estado_bot["operacoes"]

@app.get("/painel", response_class=HTMLResponse)
def painel(request: Request):
    return templates.TemplateResponse("painel.html", {
        "request": request,
        "ativo": estado_bot["ativo"],
        "modo": estado_bot["modo"],
        "moedas": estado_bot["moedas_monitoradas"],
        "saldo": estado_bot["valor_disponivel"],
        "operacoes": estado_bot["operacoes"]
    })
