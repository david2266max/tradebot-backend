
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests

app = FastAPI()

# Configuração do bot Telegram
BOT_TOKEN = "7921479727:AAH1s5TdMprUJO6VAx4C_2c9fAWN9wH3cyg"
CHAT_ID = "930323255"

def notificar_telegram(msg: str):
    if BOT_TOKEN != "COLE_SEU_TOKEN_AQUI":
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        try:
            print("ENVIANDO:", msg)  # <- linha nova
            r = requests.post(url, data=data, timeout=5)
            print("STATUS TELEGRAM:", r.status_code, r.text)  # <- linha nova
        except Exception as e:
            print("Erro Telegram:", e)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

estado_bot = {
    "ativo": False,
    "modo": "agressivo",
    "moedas_monitoradas": ["BTCUSDT", "ETHUSDT"],
    "valor_disponivel": 150.0,
    "operacoes": [
        {"symbol": "BTCUSDT", "preco": "62000", "data": "2025-05-11", "acao": "COMPRA"},
        {"symbol": "ETHUSDT", "preco": "3200", "data": "2025-05-11", "acao": "VENDA"}
    ]
}

templates = Jinja2Templates(directory="templates")

@app.get("/status")
def get_status():
    return {
        "ativo": estado_bot["ativo"],
        "modo": estado_bot["modo"],
        "moedas_monitoradas": estado_bot["moedas_monitoradas"],
        "valor_disponivel": estado_bot["valor_disponivel"]
    }

@app.post("/bot/start")
def start_bot():
    estado_bot["ativo"] = True
    notificar_telegram("🔔 Bot ativado (modo: {})".format(estado_bot["modo"]))
    return {"status": "iniciado"}

@app.post("/bot/stop")
def stop_bot():
    estado_bot["ativo"] = False
    notificar_telegram("🛑 Bot parado")
    return {"status": "parado"}

@app.post("/modo")
async def set_modo(request: Request):
    data = await request.json()
    novo_modo = data.get("perfil", "agressivo")
    estado_bot["modo"] = novo_modo
    notificar_telegram("⚙️ Modo alterado para: {}".format(novo_modo))
    return {"modo": novo_modo}

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
