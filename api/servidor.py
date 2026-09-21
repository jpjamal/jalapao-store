#!/usr/bin/env python3
"""
API de produtos do Sistema Jalapão Store.

Só biblioteca padrão do Python — sem pip, sem framework, como o resto do projeto.
Guarda a lista num JSON em volume; é isso que faz os produtos existirem fora do
navegador e aparecerem em qualquer aparelho.

    GET  /api/produtos   -> a lista (aberto, como o resto do site)
    PUT  /api/produtos   -> grava a lista (exige o cabeçalho X-Senha)
    GET  /api/saude      -> para o healthcheck do container

A gravação é atômica (escreve em arquivo temporário e troca), e cada gravação
deixa uma cópia em historico/ — assim um erro de clique não apaga o cadastro
para sempre.
"""

import json
import os
import shutil
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PASTA     = os.environ.get("PASTA_DADOS", "/dados")
ARQUIVO   = os.path.join(PASTA, "produtos.json")
HISTORICO = os.path.join(PASTA, "historico")
SENHA_ARQ = os.path.join(PASTA, "senha.txt")
PORTA     = int(os.environ.get("PORTA", "8000"))
LIMITE    = 5 * 1024 * 1024          # 5 MB: uma lista de produtos não passa disso

trava = threading.Lock()


def agora():
    return datetime.now(timezone.utc).isoformat()


def senha_esperada():
    """A senha vive num arquivo do volume — nunca no repositório nem na imagem."""
    try:
        with open(SENHA_ARQ, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def ler_lista():
    try:
        with open(ARQUIVO, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"versao": 1, "itens": [], "atualizadoEm": None}


def gravar_lista(dados):
    os.makedirs(HISTORICO, exist_ok=True)
    dados["atualizadoEm"] = agora()

    # cópia do estado anterior antes de sobrescrever
    if os.path.exists(ARQUIVO):
        marca = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        shutil.copy2(ARQUIVO, os.path.join(HISTORICO, f"produtos-{marca}.json"))
        copias = sorted(os.listdir(HISTORICO))
        for velha in copias[:-30]:               # guarda as 30 últimas
            os.remove(os.path.join(HISTORICO, velha))

    temporario = ARQUIVO + ".tmp"
    with open(temporario, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    os.replace(temporario, ARQUIVO)              # troca atômica
    return dados


class Api(BaseHTTPRequestHandler):
    server_version = "JalapaoProdutos/1.0"

    def responder(self, codigo, corpo=None):
        dados = json.dumps(corpo if corpo is not None else {}, ensure_ascii=False)
        bruto = dados.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(bruto)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(bruto)

    def do_GET(self):
        if self.path.rstrip("/") == "/api/saude":
            return self.responder(200, {"ok": True})
        if self.path.rstrip("/") == "/api/produtos":
            with trava:
                return self.responder(200, ler_lista())
        self.responder(404, {"erro": "rota desconhecida"})

    def do_PUT(self):
        if self.path.rstrip("/") != "/api/produtos":
            return self.responder(404, {"erro": "rota desconhecida"})

        esperada = senha_esperada()
        if not esperada:
            return self.responder(503, {"erro": "servidor sem senha configurada"})
        if self.headers.get("X-Senha", "") != esperada:
            return self.responder(401, {"erro": "senha incorreta"})

        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            tamanho = 0
        if tamanho <= 0 or tamanho > LIMITE:
            return self.responder(413, {"erro": "corpo vazio ou grande demais"})

        try:
            enviado = json.loads(self.rfile.read(tamanho).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self.responder(400, {"erro": "json inválido"})

        itens = enviado.get("itens")
        if not isinstance(itens, list):
            return self.responder(400, {"erro": "faltou a lista de itens"})

        with trava:
            salvo = gravar_lista({"versao": enviado.get("versao", 1), "itens": itens})
        self.responder(200, salvo)

    def log_message(self, formato, *args):       # log enxuto, sem poluir
        print(f"{self.address_string()} {formato % args}", flush=True)


if __name__ == "__main__":
    os.makedirs(PASTA, exist_ok=True)
    print(f"produtos em {ARQUIVO} | senha {'definida' if senha_esperada() else 'AUSENTE'}", flush=True)
    ThreadingHTTPServer(("", PORTA), Api).serve_forever()
