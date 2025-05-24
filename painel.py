
import threading
import time
from fastapi import FastAPI

app = FastAPI()

# Simula função de consultar preço na Binance
def consultar_preco(symbol="BTCUSDT"):
    return {"price": "55000.00"}

# Simula função de criar ordem real na Binance
def criar_ordem(symbol, side, tipo, quantidade):
    print(f"Ordem criada: {side} {quantidade} {symbol}")

# Simula envio de notificação Telegram
def notificar_telegram(msg):
    print(f"Telegram: {msg}")

def monitorar_automaticamente(symbol="BTCUSDT", intervalo=60, preco_alvo_compra=50000, preco_alvo_venda=60000):
    def loop():
        while True:
            preco = float(consultar_preco(symbol)["price"])
            print(f"Preço atual de {symbol}: {preco}")

            if preco <= preco_alvo_compra:
                criar_ordem(symbol, "BUY", "MARKET", 0.001)
                notificar_telegram(f"✅ Ordem automática de COMPRA enviada para {symbol} a {preco}")

            elif preco >= preco_alvo_venda:
                criar_ordem(symbol, "SELL", "MARKET", 0.001)
                notificar_telegram(f"✅ Ordem automática de VENDA enviada para {symbol} a {preco}")

            time.sleep(intervalo)

    threading.Thread(target=loop, daemon=True).start()

@app.post("/monitor/start")
def iniciar_monitoramento(symbol: str = "BTCUSDT", preco_alvo_compra: float = 50000, preco_alvo_venda: float = 60000, intervalo: int = 60):
    monitorar_automaticamente(symbol, intervalo, preco_alvo_compra, preco_alvo_venda)
    return {"status": f"Monitoramento iniciado para {symbol} com intervalo de {intervalo}s"}
