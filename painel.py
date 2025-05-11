
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/painel", response_class=HTMLResponse)
async def painel(request: Request):
    return templates.TemplateResponse("painel.html", {
        "request": request,
        "status": "Parado",
        "saldo": 0.0,
        "moedas": "BTCUSDT, ETHUSDT"
    })
