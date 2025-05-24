from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests
import threading
import time
from binance.client import Client
from dotenv import load_dotenv

import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
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
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print(f"Erro ao notificar Telegram: {e}")

def consultar_saldo():
    try:
        info = binance_client.get_account()
        saldos = info['balances']
        ativos = [s for s in saldos if float(s['free']) > 0]
        return ativos
    except Exception as e:
        return {"erro": str(e)}

def consultar_preco(symbol="BTCUSDT"):
    try:
        ticker = binance_client.get_symbol_ticker(symbol=symbol)
        return ticker
    except Exception as e:
        return {"erro": str(e)}

def criar_ordem(symbol="BTCUSDT", side="BUY", tipo="MARKET", quantidade=0.001):
    try:
        ordem = binance_client.create_order(
            symbol=symbol,
            side=side,
            type=tipo,
            quantity=quantidade
        )
        return ordem
    except Exception as e:
        return {"erro": str(e)}

def monitorar_automaticamente(symbol="BTCUSDT", intervalo=60, preco_alvo_compra=50000, preco_alvo_venda=60000):
    def loop():
        while True:
            preco_info = consultar_preco(symbol)
            if "erro" in preco_info:
                print(f"Erro ao consultar preço: {preco_info['erro']}")
                time.sleep(intervalo)
                continue

            preco = float(preco_info["price"])
            print(f"Preço atual de {symbol}: {preco}")

            if preco <= preco_alvo_compra:
                resultado = criar_ordem(symbol, "BUY", "MARKET", 0.001)
                notificar_telegram(f"✅ Ordem automática de COMPRA enviada para {symbol} a {preco}: {resultado}")

            elif preco >= preco_alvo_venda:
                resultado = criar_ordem(symbol, "SELL", "MARKET", 0.001)
                notificar_telegram(f"✅ Ordem automática de VENDA enviada para {symbol} a {preco}: {resultado}")

            time.sleep(intervalo)

    threading.Thread(target=loop, daemon=True).start()

@app.post("/monitor/start")
def iniciar_monitoramento(symbol: str = "BTCUSDT", preco_alvo_compra: float = 50000, preco_alvo_venda: float = 60000, intervalo: int = 60):
    monitorar_automaticamente(symbol, intervalo, preco_alvo_compra, preco_alvo_venda)
    return {"status": f"Monitoramento iniciado para {symbol} com intervalo de {intervalo}s"}

@app.get("/binance/saldo")
def saldo_binance():
    return consultar_saldo()

@app.get("/binance/preco")
def preco_binance(symbol: str = "BTCUSDT"):
    return consultar_preco(symbol)

@app.post("/binance/ordem")
def ordem_binance(symbol: str = "BTCUSDT", side: str = "BUY", quantidade: float = 0.001):
    resultado = criar_ordem(symbol, side, "MARKET", quantidade)
    notificar_telegram(f"🚨 Ordem enviada: {resultado}")
    return resultado

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
