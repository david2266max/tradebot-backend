
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests
import sqlite3
from binance.client import Client

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BOT_TOKEN = "7921479727:AAH1s5TdMprUJO6VAx4C_2c9fAWN9wH3cyg"
CHAT_ID = "1069380923"

API_KEY = "SUA_API_KEY"
API_SECRET = "SUA_API_SECRET"
binance_client = Client(API_KEY, API_SECRET)

estado_bot = {
    "ativo": False,
    "modo": "agressivo",
    "moedas_monitoradas": ["BTCUSDT", "ETHUSDT"],
    "valor_disponivel": 150.0,
    "operacoes": []
}

def notificar_telegram(msg: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data, timeout=5)

def consultar_saldo():
    info = binance_client.get_account()
    saldos = info['balances']
    ativos = [s for s in saldos if float(s['free']) > 0]
    return ativos

def consultar_preco(symbol="BTCUSDT"):
    ticker = binance_client.get_symbol_ticker(symbol=symbol)
    return ticker

def criar_ordem(symbol="BTCUSDT", side="BUY", tipo="MARKET", quantidade=0.001):
    ordem = binance_client.create_order(
        symbol=symbol,
        side=side,
        type=tipo,
        quantity=quantidade
    )
    return ordem

@app.get("/binance/saldo")
def saldo_binance():
    return consultar_saldo()

@app.get("/binance/preco")
def preco_binance(symbol: str = "BTCUSDT"):
    return consultar_preco(symbol)

@app.post("/binance/ordem")
def ordem_binance(symbol: str = "BTCUSDT", side: str = "BUY", quantidade: float = 0.001):
    ordem = criar_ordem(symbol, side, "MARKET", quantidade)
    notificar_telegram(f"🚨 Ordem enviada: {ordem}")
    return ordem

@app.get("/status")
def get_status():
    return estado_bot

@app.post("/bot/start")
def start_bot():
    estado_bot["ativo"] = True
    notificar_telegram(f"🔔 Bot ativado (modo: {estado_bot['modo']})")
    return {"status": "iniciado"}

@app.post("/bot/stop")
def stop_bot():
    estado_bot["ativo"] = False
    notificar_telegram("🛑 Bot parado")
    return {"status": "parado"}

@app.post("/modo")
async def set_modo(request: Request):
    data = await request.json()
    novo_modo = data.get("modo", "agressivo")
    estado_bot["modo"] = novo_modo
    notificar_telegram(f"⚙️ Modo alterado para: {novo_modo}")
    return {"modo": novo_modo}

@app.get("/operacoes")
def get_operacoes():
    return estado_bot["operacoes"]

@app.get("/painel", response_class=HTMLResponse)
async def painel(request: Request):
    return templates.TemplateResponse("painel.html", {
        "request": request,
        "ativo": estado_bot["ativo"],
        "modo": estado_bot["modo"],
        "moedas": estado_bot["moedas_monitoradas"],
        "saldo": estado_bot["valor_disponivel"],
        "operacoes": estado_bot["operacoes"]
    })
