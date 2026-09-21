# API de produtos — Python puro, sem dependência nenhuma.
FROM python:3.12-alpine

WORKDIR /app
COPY servidor.py .

# os dados moram em volume; a imagem não carrega nada
RUN mkdir -p /dados
EXPOSE 8000

CMD ["python", "-u", "servidor.py"]
