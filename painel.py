from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Permitir requisições do app Android
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

estado_bot = {
    "ativo": False,
    "modo": "agressivo"
}

@app.get("/status")
def get_status():
    return {
        "ativo": estado_bot["ativo"],
        "modo": estado_bot["modo"],
        "moedas_monitoradas": ["BTCUSDT", "ETHUSDT"],
        "valor_disponivel": 150.0
    }

@app.post("/bot/start")
def start_bot():
    estado_bot["ativo"] = True
    return {"status": "iniciado"}

@app.post("/bot/stop")
def stop_bot():
    estado_bot["ativo"] = False
    return {"status": "parado"}

@app.post("/modo")
def set_modo(perfil: dict):
    estado_bot["modo"] = perfil.get("perfil", "agressivo")
    return {"modo": estado_bot["modo"]}

@app.get("/operacoes")
def get_operacoes():
    return [
        {"symbol": "BTCUSDT", "preco": "62000", "data": "2025-05-10", "acao": "COMPRA"},
        {"symbol": "ETHUSDT", "preco": "3200", "data": "2025-05-10", "acao": "VENDA"}
    ]
