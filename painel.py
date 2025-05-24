
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USUARIO = "admin"
SENHA = "dNMsSuvlJUhe2hYk"
BOT_TOKEN = "7921479727:AAH1s5TdMprUJO6VAx4C_2c9fAWN9wH3cyg"
CHAT_ID = "1069380923"

PERFIS = {
    "agressivo": {"alocacao": 0.8, "moedas": ["BTCUSDT", "ETHUSDT", "SOLUSDT"], "risco": "alto"},
    "moderado": {"alocacao": 0.5, "moedas": ["BTCUSDT", "ETHUSDT"], "risco": "médio"},
    "manual": {"alocacao": 0.2, "moedas": ["BTCUSDT"], "risco": "baixo"}
}

estado_bot = {"ativo": False, "modo": "agressivo", "valor_disponivel": 150.0, "operacoes": []}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

def ajustar_alocacao():
    perfil = estado_bot['modo']
    alocacao = PERFIS[perfil]['alocacao']
    saldo = estado_bot['valor_disponivel']
    return round(saldo * alocacao, 2)

def estrategia_rsi(rsi):
    if rsi < 30: return "COMPRA"
    if rsi > 70: return "VENDA"
    return "MANTER"

def cruzamento_medias(movel_curta, movel_longa):
    if movel_curta > movel_longa: return "COMPRA"
    if movel_curta < movel_longa: return "VENDA"
    return "MANTER"

def operar_automaticamente(symbol, preco_atual, rsi, movel_curta, movel_longa):
    decisao_rsi = estrategia_rsi(rsi)
    decisao_media = cruzamento_medias(movel_curta, movel_longa)
    if decisao_rsi == "MANTER" and decisao_media == "MANTER":
        return {"status": "Nenhuma ação tomada"}
    acao = "COMPRA" if "COMPRA" in [decisao_rsi, decisao_media] else "VENDA"
    operacao = {"symbol": symbol, "preco": preco_atual, "data": time.strftime("%Y-%m-%d"), "acao": acao}
    estado_bot['operacoes'].append(operacao)
    logging.info(f"Operação automática: {operacao}")
    notificar_telegram(f"📈 Operação automática: {operacao}")
    return operacao

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
    notificar_telegram(f"🔔 Bot ativado (modo: {estado_bot['modo']})")
    valor_investir = ajustar_alocacao()
    logging.info(f"Ajuste automático: investir {valor_investir}")
    preco, rsi, movel_curta, movel_longa = 62000, 25, 60000, 61000
    operar_automaticamente("BTCUSDT", preco, rsi, movel_curta, movel_longa)
    return {"status": "iniciado", "alocacao": valor_investir}

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

@app.get("/operacoes/filtro")
def filtrar_operacoes(symbol: str = None, acao: str = None):
    ops = estado_bot["operacoes"]
    if symbol: ops = [op for op in ops if op["symbol"] == symbol]
    if acao: ops = [op for op in ops if op["acao"] == acao]
    return ops

class OperacaoInput(BaseModel):
    symbol: str
    preco: float
    acao: str
    data: str

    @validator('symbol')
    def symbol_nao_vazio(cls, v):
        if not v.strip(): raise ValueError('Symbol não pode ser vazio')
        return v

    @validator('preco')
    def preco_positivo(cls, v):
        if v <= 0: raise ValueError('Preço deve ser positivo')
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
    if not (secrets.compare_digest(credentials.username, USUARIO) and secrets.compare_digest(credentials.password, SENHA)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais incorretas",
                            headers={"WWW-Authenticate": "Basic"})

@app.get("/painel", response_class=HTMLResponse)
async def painel(request: Request, credentials: HTTPBasicCredentials = Depends(autenticar)):
    return templates.TemplateResponse("painel.html", {"request": request})
