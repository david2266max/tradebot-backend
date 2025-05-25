# ✅ Imagem base
FROM python:3.11-slim

# ✅ Define diretório de trabalho
WORKDIR /app

# ✅ Copia arquivos
COPY . /app

# ✅ Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Expõe porta
EXPOSE 8000

# ✅ Comando de inicialização
CMD ["uvicorn", "painel:app", "--host", "0.0.0.0", "--port", "8000"]
