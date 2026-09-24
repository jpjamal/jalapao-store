"""Adaptador da Shopee.

O transporte é injetável: em produção é `urllib` da biblioteca padrão — o backend não tem
dependência de HTTP e não vale trazer uma só por isto —, e nos testes é uma função falsa
que devolve respostas gravadas. É o que permite provar assinatura, renovação de token e
tratamento de erro sem credencial e sem rede.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta

from django.utils import timezone

from ..base import IntegrationError, MarketplaceAdapter, RemoteItem, Tokens, registrar
from .assinatura import parametros_comuns, timestamp_agora

# Domínio do Brasil. A Shopee separa por região e a escolha errada responde erro de loja
# inexistente, que não parece erro de domínio — por isso fica explícito aqui.
BASE_PADRAO = "https://openplatform.shopee.com.br"

CAMINHO_AUTH = "/api/v2/shop/auth_partner"
CAMINHO_TOKEN = "/api/v2/auth/token/get"
CAMINHO_REFRESH = "/api/v2/auth/access_token/get"
CAMINHO_SHOP_INFO = "/api/v2/shop/get_shop_info"
CAMINHO_ITEM_LIST = "/api/v2/product/get_item_list"
CAMINHO_ITEM_BASE = "/api/v2/product/get_item_base_info"
CAMINHO_UPDATE_STOCK = "/api/v2/product/update_stock"

# erros de token que valem uma renovação e uma segunda tentativa
ERROS_DE_TOKEN = {
    "error_auth",
    "error_token",
    "invalid_access_token",
    "access_token_error",
    "error_expired_access_token",
}


def transporte_urllib(metodo, url, corpo=None, timeout=20):
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo)
    if dados is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resposta:
            return json.loads(resposta.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        corpo_erro = e.read().decode("utf-8", "replace")
        try:
            return json.loads(corpo_erro or "{}")
        except ValueError:
            raise IntegrationError(f"Shopee respondeu HTTP {e.code}: {corpo_erro[:200]}") from e
    except urllib.error.URLError as e:
        raise IntegrationError(f"Não consegui falar com a Shopee: {e.reason}") from e


@registrar
class ShopeeAdapter(MarketplaceAdapter):
    channel = "shopee"

    def __init__(self, *, transporte=None, config=None):
        self.transporte = transporte or transporte_urllib
        c = config or {}
        self.partner_id = c.get("partner_id") or os.getenv("SHOPEE_PARTNER_ID", "")
        self.partner_key = c.get("partner_key") or os.getenv("SHOPEE_PARTNER_KEY", "")
        self.redirect_uri = c.get("redirect_uri") or os.getenv("SHOPEE_REDIRECT_URI", "")
        self.base = (c.get("base") or os.getenv("SHOPEE_API_BASE") or BASE_PADRAO).rstrip("/")

    # ---------- infraestrutura ----------
    def _exigir_credenciais(self):
        if not (self.partner_id and self.partner_key):
            raise IntegrationError(
                "Integração da Shopee sem credenciais: configure SHOPEE_PARTNER_ID e "
                "SHOPEE_PARTNER_KEY no servidor."
            )

    def _url(self, caminho, *, access_token="", shop_id="", extra=None):
        comuns = parametros_comuns(
            partner_id=self.partner_id,
            partner_key=self.partner_key,
            caminho=caminho,
            access_token=access_token,
            shop_id=shop_id,
        )
        comuns.update(extra or {})
        return f"{self.base}{caminho}?{urllib.parse.urlencode(comuns)}"

    def _chamar(self, metodo, caminho, *, access_token="", shop_id="", corpo=None, extra=None):
        self._exigir_credenciais()
        url = self._url(caminho, access_token=access_token, shop_id=shop_id, extra=extra)
        resposta = self.transporte(metodo, url, corpo) or {}
        erro = str(resposta.get("error") or "")
        if erro:
            raise IntegrationError(
                resposta.get("message") or f"Shopee recusou a chamada ({erro}).",
                codigo=erro,
                token_invalido=erro in ERROS_DE_TOKEN,
            )
        return resposta

    # ---------- autorização ----------
    def authorization_url(self, *, state=""):
        """Link que o dono abre para autorizar a loja.

        `redirect_uri` sai de configuração porque a Shopee valida o domínio dele contra o
        declarado no Console: se um dia recusar o IP, muda a variável e não o código.
        """
        self._exigir_credenciais()
        if not self.redirect_uri:
            raise IntegrationError("Configure SHOPEE_REDIRECT_URI antes de gerar o link.")
        timestamp = timestamp_agora()
        comuns = parametros_comuns(
            partner_id=self.partner_id,
            partner_key=self.partner_key,
            caminho=CAMINHO_AUTH,
            timestamp=timestamp,
        )
        destino = self.redirect_uri
        if state:
            junta = "&" if "?" in destino else "?"
            destino = f"{destino}{junta}{urllib.parse.urlencode({'state': state})}"
        comuns["redirect"] = destino
        return f"{self.base}{CAMINHO_AUTH}?{urllib.parse.urlencode(comuns)}"

    def _tokens_da_resposta(self, dados, external_id):
        acesso = dados.get("access_token") or ""
        atualizacao = dados.get("refresh_token") or ""
        if not acesso:
            raise IntegrationError("A Shopee não devolveu access_token.")
        return Tokens(
            access_token=acesso,
            refresh_token=atualizacao,
            expires_in=int(dados.get("expire_in") or dados.get("expires_in") or 14400),
            external_id=str(dados.get("shop_id") or external_id or ""),
        )

    def exchange_code(self, *, code, external_id):
        dados = self._chamar(
            "POST",
            CAMINHO_TOKEN,
            corpo={"code": code, "partner_id": int(self.partner_id), "shop_id": int(external_id)},
        )
        return self._tokens_da_resposta(dados, external_id)

    def refresh(self, *, refresh_token, external_id):
        dados = self._chamar(
            "POST",
            CAMINHO_REFRESH,
            corpo={
                "refresh_token": refresh_token,
                "partner_id": int(self.partner_id),
                "shop_id": int(external_id),
            },
        )
        return self._tokens_da_resposta(dados, external_id)

    # ---------- leitura ----------
    def shop_info(self, *, account):
        return self._chamar(
            "GET",
            CAMINHO_SHOP_INFO,
            access_token=account.access_token,
            shop_id=account.external_id,
        )

    def list_items(self, *, account, teto=200):
        """Lista os anúncios e traz o essencial de cada um.

        A Shopee separa em duas chamadas: a lista devolve ids, e o detalhe devolve título,
        SKU e saldo. Pagina de 100 em 100 e para no teto, para não varrer catálogo enorme
        numa requisição de tela.
        """
        ids, offset = [], 0
        while len(ids) < teto:
            pagina = self._chamar(
                "GET",
                CAMINHO_ITEM_LIST,
                access_token=account.access_token,
                shop_id=account.external_id,
                extra={
                    "offset": offset,
                    "page_size": 100,
                    "item_status": "NORMAL",
                },
            ).get("response") or {}
            lote = [str(i.get("item_id")) for i in (pagina.get("item") or []) if i.get("item_id")]
            ids.extend(lote)
            if not pagina.get("has_next_page") or not lote:
                break
            offset = pagina.get("next_offset", offset + len(lote))

        itens = []
        for pedaco in [ids[i : i + 50] for i in range(0, len(ids[:teto]), 50)]:
            detalhe = self._chamar(
                "GET",
                CAMINHO_ITEM_BASE,
                access_token=account.access_token,
                shop_id=account.external_id,
                extra={"item_id_list": ",".join(pedaco)},
            ).get("response") or {}
            for bruto in detalhe.get("item_list") or []:
                itens.append(
                    RemoteItem(
                        item_id=str(bruto.get("item_id")),
                        title=bruto.get("item_name") or "",
                        sku=bruto.get("item_sku") or "",
                        stock=_saldo(bruto),
                        status=bruto.get("item_status") or "",
                        extra={"has_model": bool(bruto.get("has_model"))},
                    )
                )
        return itens

    # ---------- escrita ----------
    def update_stock(self, *, account, item_id, quantity):
        self._chamar(
            "POST",
            CAMINHO_UPDATE_STOCK,
            access_token=account.access_token,
            shop_id=account.external_id,
            corpo={
                "item_id": int(item_id),
                "stock_list": [
                    {"model_id": 0, "seller_stock": [{"stock": int(quantity)}]},
                ],
            },
        )


def _saldo(bruto):
    """O saldo vem em formatos diferentes conforme a época da API; tenta os conhecidos."""
    info = bruto.get("stock_info_v2") or {}
    resumo = info.get("summary_info") or {}
    if "total_available_stock" in resumo:
        return resumo["total_available_stock"]
    for linha in bruto.get("stock_info") or []:
        if linha.get("stock_type") == 2 and "current_stock" in linha:
            return linha["current_stock"]
    return None


def validade_da_autorizacao(dias=365):
    """A Shopee limita a autorização a 365 dias e não informa a data na troca de token."""
    return timezone.now() + timedelta(days=dias)
