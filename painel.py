
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import requests
import sqlite3
import logging
import time
from pydantic import BaseModel, validator

app = FastAPI()

security = HTTPBasic()
templates = Jinja2Templates(directory="templates")

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Credenciais
USUARIO = "admin"
SENHA = "dNMsSuvlJUhe2hYk"

BOT_TOKEN = "7921479727:AAH1s5TdMprUJO6VAx4C_2c9fAWN9wH3cyg"
CHAT_ID = "1069380923"

def notificar_telegram(msg: str, tentativas=3):
    if BOT_TOKEN != "COLE_SEU_TOKEN_AQUI":
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        for tentativa in range(1, tentativas + 1):
            try:
                logging.info(f"Enviando para Telegram: {msg} (tentativa {tentativa})")
                r = requests.post(url, data=data, timeout=5)
                logging.info(f"Status Telegram: {r.status_code} {r.text}")
                if r.status_code == 200:
                    break
            except Exception as e:
                logging.error(f"Erro Telegram: {e}")
                time.sleep(1)

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
    "operacoes": []
}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"Requisição: {request.method} {request.url}")
    response = await call_next(request)
    logging.info(f"Resposta: {response.status_code}")
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Erro inesperado: {exc}")
    return JSONResponse(status_code=500, content={"erro": "Erro interno do servidor."})

@app.get("/status")
def get_status():
    return estado_bot

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
    novo_modo = data.get("modo", "agressivo")
    estado_bot["modo"] = novo_modo
    notificar_telegram(f"⚙️ Modo alterado para: {novo_modo}")
    return {"modo": novo_modo}

@app.get("/operacoes")
def get_operacoes():
    return estado_bot["operacoes"]

class OperacaoInput(BaseModel):
    symbol: str
    preco: float
    acao: str
    data: str

    @validator('symbol')
    def symbol_nao_vazio(cls, v):
        if not v.strip():
            raise ValueError('Symbol não pode ser vazio')
        return v

    @validator('preco')
    def preco_positivo(cls, v):
        if v <= 0:
            raise ValueError('Preço deve ser positivo')
        return v

    @validator('data')
    def data_formatada(cls, v):
        if len(v) != 10 or v[4] != '-' or v[7] != '-':
            raise ValueError('Data deve estar no formato YYYY-MM-DD')
        return v

DB_PATH = "database.db"

@app.post("/operar")
def nova_operacao(operacao: OperacaoInput):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT INTO operacoes (symbol, preco, acao, data) VALUES (?, ?, ?, ?)",
                     (operacao.symbol, operacao.preco, operacao.acao, operacao.data))
        conn.commit()
        estado_bot["operacoes"].append(operacao.dict())
    finally:
        conn.close()
    return {"status": "registrado"}

def autenticar(credentials: HTTPBasicCredentials = Depends(security)):
    if not (secrets.compare_digest(credentials.username, USUARIO) and 
            secrets.compare_digest(credentials.password, SENHA)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais incorretas",
            headers={"WWW-Authenticate": "Basic"},
        )

@app.get("/painel", response_class=HTMLResponse)
async def painel(request: Request, credentials: HTTPBasicCredentials = Depends(autenticar)):
    return templates.TemplateResponse("painel.html", {"request": request})
