"""Cliente Mercado Livre. Transporte substituível permite teste sem rede ou credenciais."""

import base64
import hashlib
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from ..base import IntegrationError, MarketplaceAdapter, RemoteItem, Tokens, registrar

API = "https://api.mercadolibre.com"
AUTH = "https://auth.mercadolivre.com.br/authorization"

logger = logging.getLogger(__name__)


@dataclass
class HttpResponse:
    status: int
    body: object
    headers: dict


def transporte_urllib(method, path, *, token="", data=None, form=False, headers=None, raw=None):
    """`raw` manda bytes prontos (upload multipart); o Content-Type vem em `headers`."""
    url = API + path
    payload = None
    content_type = "application/x-www-form-urlencoded" if form else "application/json"
    if raw is not None:
        payload, content_type = raw, (headers or {}).pop("Content-Type", "application/octet-stream")
    elif data is not None:
        payload = (
            urllib.parse.urlencode(data).encode()
            if form else json.dumps(data).encode("utf-8")
        )
    req = urllib.request.Request(url, data=payload, method=method)
    req.add_header("Accept", "application/json")
    if payload is not None:
        req.add_header("Content-Type", content_type)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=60 if raw is not None else 20) as response:
            raw = response.read().decode("utf-8")
            return HttpResponse(response.status, json.loads(raw) if raw else {}, dict(response.headers))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            body = json.loads(raw)
        except ValueError:
            body = {}
        return HttpResponse(exc.code, body, dict(exc.headers))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise IntegrationError("Não foi possível comunicar com o Mercado Livre.") from exc


@registrar
class MercadoLivreAdapter(MarketplaceAdapter):
    channel = "mercado_livre"

    def __init__(self, *, transporte=None, config=None):
        self.transporte = transporte or transporte_urllib
        config = config or {}
        self.client_id = config.get("client_id", os.getenv("ML_APP_ID", ""))
        self.client_secret = config.get("client_secret", os.getenv("ML_CLIENT_SECRET", ""))
        self.redirect_uri = config.get("redirect_uri", os.getenv("ML_REDIRECT_URI", ""))
        self.pkce_enabled = config.get("pkce_enabled", os.getenv("ML_PKCE_ENABLED", "0") == "1")

    def _configurado(self):
        if not all((self.client_id, self.client_secret, self.redirect_uri)):
            raise IntegrationError("Configure ML_APP_ID, ML_CLIENT_SECRET e ML_REDIRECT_URI no backend.")

    def _request(self, method, path, *, token="", data=None, form=False, headers=None, raw=None):
        extra = {"raw": raw} if raw is not None else {}
        response = self.transporte(
            method, path, token=token, data=data, form=form, headers=headers, **extra
        )
        body = response.body
        if response.status >= 400:
            code = body.get("error", "") if isinstance(body, dict) else ""
            if response.status in (401, 403):
                message = "A autorização do Mercado Livre foi recusada ou expirou."
            elif response.status == 429:
                message = "O Mercado Livre limitou as chamadas. Tente novamente mais tarde."
            elif response.status == 409:
                message = "O estoque mudou no Mercado Livre. Tente sincronizar novamente."
            else:
                message = f"Mercado Livre respondeu HTTP {response.status}."
            raise IntegrationError(message, codigo=str(code), token_invalido=response.status == 401)
        return response

    def authorization_url(self, *, state="", code_verifier=""):
        self._configurado()
        if not state:
            raise IntegrationError("Estado de autorização obrigatório.")
        params = {
            "response_type": "code", "client_id": self.client_id,
            "redirect_uri": self.redirect_uri, "state": state,
        }
        if self.pkce_enabled:
            if not code_verifier:
                raise IntegrationError("PKCE exige código de verificação.")
            digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
            params.update(code_challenge=base64.urlsafe_b64encode(digest).rstrip(b"=").decode(),
                          code_challenge_method="S256")
        return AUTH + "?" + urllib.parse.urlencode(params)

    def _tokens(self, body):
        try:
            return Tokens(
                access_token=body["access_token"],
                refresh_token=body["refresh_token"],
                expires_in=int(body["expires_in"]),
                external_id=str(body["user_id"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise IntegrationError("Resposta de autorização incompleta do Mercado Livre.") from exc

    def exchange_code(self, *, code, external_id="", code_verifier=""):
        self._configurado()
        data = {
            "grant_type": "authorization_code", "client_id": self.client_id,
            "client_secret": self.client_secret, "code": code, "redirect_uri": self.redirect_uri,
        }
        if self.pkce_enabled:
            if not code_verifier:
                raise IntegrationError("Tentativa PKCE inválida.")
            data["code_verifier"] = code_verifier
        body = self._request("POST", "/oauth/token", data=data, form=True).body
        return self._tokens(body)

    def refresh(self, *, refresh_token, external_id):
        self._configurado()
        body = self._request("POST", "/oauth/token", form=True, data={
            "grant_type": "refresh_token", "client_id": self.client_id,
            "client_secret": self.client_secret, "refresh_token": refresh_token,
        }).body
        tokens = self._tokens(body)
        if tokens.external_id != str(external_id):
            raise IntegrationError("A renovação retornou outra conta do Mercado Livre.")
        return tokens

    def shop_info(self, *, account):
        return self._request("GET", f"/users/{account.external_id}", token=account.access_token).body

    def list_items(self, *, account):
        items = []
        offset = 0
        while True:
            path = f"/users/{account.external_id}/items/search?limit=50&offset={offset}"
            page = self._request("GET", path, token=account.access_token).body
            ids = page.get("results", [])
            for start in range(0, len(ids), 20):
                batch = ids[start:start + 20]
                detail = self._request("GET", "/items/bulk?" + urllib.parse.urlencode(
                    {"ids": ",".join(batch)}), token=account.access_token).body
                if not isinstance(detail, list) or len(detail) != len(batch):
                    raise IntegrationError("Resposta incompleta ao consultar anúncios do Mercado Livre.")
                for result in detail:
                    if result.get("status_code") != 200:
                        raise IntegrationError("Falha ao consultar um anúncio; importação interrompida.")
                    item = result.get("body") or {}
                    if not item.get("id") or str(item.get("seller_id")) != str(account.external_id):
                        raise IntegrationError("Anúncio sem ID ou pertencente a outra conta.")
                    attrs = item.get("attributes") or []
                    skus = {str(a.get("value_name") or a.get("value_id") or "").strip()
                            for a in attrs if a.get("id") == "SELLER_SKU"}
                    skus.discard("")
                    if item.get("seller_custom_field"):
                        skus.add(str(item["seller_custom_field"]).strip())
                    variations = item.get("variations") or []
                    if variations:
                        # Um anúncio pode representar vários produtos; o modelo atual não pode
                        # vincular cada variação com segurança.
                        sku = ""
                    else:
                        sku = next(iter(skus)) if len(skus) == 1 else ""
                    items.append(RemoteItem(
                        item_id=str(item.get("id", "")), title=item.get("title") or "",
                        sku=sku, stock=item.get("available_quantity"),
                        price=str(item.get("price") or ""), status=item.get("status") or "",
                        extra={"user_product_id": item.get("user_product_id") or "",
                               "family_id": item.get("family_id") or ""},
                    ))
            offset += len(ids)
            total = int((page.get("paging") or {}).get("total") or offset)
            if offset >= total or not ids:
                return items
            if offset >= 1000:
                raise IntegrationError("Mais de 1000 anúncios: importação por scan ainda não disponível.")

    def update_stock(self, *, account, item_id, quantity):
        if quantity < 0:
            raise IntegrationError("Saldo de estoque inválido.")
        item = self._request("GET", f"/items/{urllib.parse.quote(item_id, safe='')}",
                             token=account.access_token).body
        if str(item.get("seller_id")) != str(account.external_id):
            raise IntegrationError("Anúncio não pertence à conta conectada.")
        if item.get("variations"):
            raise IntegrationError("Anúncio com variações exige vínculo de estoque por variação.")
        if (item.get("shipping") or {}).get("logistic_type") == "fulfillment":
            raise IntegrationError("Estoque Full é gerido pelo Mercado Livre.")
        seller = self.shop_info(account=account)
        tags = set(seller.get("tags") or [])
        up_id = item.get("user_product_id")
        if "warehouse_management" in tags:
            if not up_id:
                raise IntegrationError("User Product ausente na conta com depósitos.")
            path = f"/user-products/{urllib.parse.quote(str(up_id), safe='')}/stock"
            stock = self._request("GET", path, token=account.access_token)
            locations = [loc for loc in (stock.body.get("locations") or [])
                         if loc.get("type") == "seller_warehouse"]
            version = next((value for key, value in stock.headers.items()
                            if key.lower() == "x-version"), "")
            if len(locations) != 1 or not version:
                raise IntegrationError("Depósito do vendedor ambíguo ou sem versão; saldo não enviado.")
            location = locations[0]
            if not location.get("store_id") or not location.get("network_node_id"):
                raise IntegrationError("Localização do depósito incompleta; saldo não enviado.")
            self._request("PUT", path + "/type/seller_warehouse", token=account.access_token,
                          headers={"x-version": str(version)}, data={"locations": [{
                              "store_id": location["store_id"],
                              "network_node_id": location["network_node_id"],
                              "quantity": quantity,
                          }]})
            return
        if up_id or item.get("stock_locations"):
            raise IntegrationError("Modelo de estoque do anúncio exige verificação antes do envio.")
        self._request("PUT", f"/items/{urllib.parse.quote(item_id, safe='')}",
                      token=account.access_token, data={"available_quantity": quantity})

    # ---------- anúncio: consulta e simulação, nunca criação ----------
    # Site fixo: a loja vende no Brasil. Os caminhos abaixo são os da documentação
    # oficial (Categorização de produtos, Atributos, Validador de publicações).
    SITE = "MLB"

    def suggest_categories(self, *, account, q, limit=3):
        """Até três categorias prováveis para o título; a primeira é a mais provável."""
        query = urllib.parse.urlencode({"q": q, "limit": max(1, min(int(limit), 8))})
        body = self._request(
            "GET", f"/sites/{self.SITE}/domain_discovery/search?{query}", token=account.access_token
        ).body
        return body if isinstance(body, list) else []

    def site_categories(self, *, account):
        """Categorias de primeiro nível do site, ponto de partida para navegar a árvore."""
        body = self._request("GET", f"/sites/{self.SITE}/categories", token=account.access_token).body
        return body if isinstance(body, list) else []

    def category(self, *, account, category_id):
        path = f"/categories/{urllib.parse.quote(str(category_id), safe='')}"
        return self._request("GET", path, token=account.access_token).body or {}

    def category_attributes(self, *, account, category_id):
        path = f"/categories/{urllib.parse.quote(str(category_id), safe='')}/attributes"
        body = self._request("GET", path, token=account.access_token).body
        return body if isinstance(body, list) else []

    # ---------- publicação (spec 012): as únicas chamadas que criam algo no Mercado Livre ----------

    def upload_picture(self, *, account, filename, content, mime_type):
        """Sobe uma foto para o Mercado Livre e devolve o id dela, para usar em `pictures`.

        As fotos da loja são privadas — não há URL pública para o `source` —, então vão pelo
        upload direto em multipart, que é o que a documentação recomenda."""
        fronteira = "jalapao" + os.urandom(12).hex()
        nome = "".join(c for c in filename if c not in '"\r\n') or "foto.jpg"
        corpo = b"".join([
            f"--{fronteira}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{nome}"\r\n'.encode(),
            f"Content-Type: {mime_type}\r\n\r\n".encode(),
            content,
            f"\r\n--{fronteira}--\r\n".encode(),
        ])
        response = self._request(
            "POST", "/pictures/items/upload", token=account.access_token,
            headers={"Content-Type": f"multipart/form-data; boundary={fronteira}"}, raw=corpo,
        )
        body = response.body if isinstance(response.body, dict) else {}
        foto_id = body.get("id")
        if not foto_id:
            # resposta fora do formato documentado: registra para ajustar com o caso real
            logger.warning(
                "upload de foto sem id: HTTP %s, corpo %s", response.status, str(response.body)[:800]
            )
            raise IntegrationError(
                f"O Mercado Livre recebeu a foto mas não devolveu o id dela (HTTP {response.status})."
            )
        return str(foto_id)

    def create_item(self, *, account, payload):
        """Cria o anúncio. Devolve `(item, causas)`: o item quando criou, as causas quando o
        Mercado Livre recusou com 400 — como na validação, o 400 aqui é resposta."""
        response = self.transporte("POST", "/items", token=account.access_token, data=payload)
        if response.status in (200, 201) and isinstance(response.body, dict) and response.body.get("id"):
            return response.body, []
        if response.status == 400 and isinstance(response.body, dict):
            causas = response.body.get("cause") or [{
                "type": "error",
                "code": str(response.body.get("error") or "body.invalid"),
                "message": str(response.body.get("message") or ""),
                "references": [],
            }]
            return None, causas
        if response.status in (401, 403):
            raise IntegrationError(
                "A autorização do Mercado Livre foi recusada ou expirou.",
                token_invalido=response.status == 401,
            )
        if response.status == 429:
            raise IntegrationError("O Mercado Livre limitou as chamadas. Tente novamente mais tarde.")
        raise IntegrationError(f"Mercado Livre respondeu HTTP {response.status} ao criar o anúncio.")

    def set_description(self, *, account, item_id, text):
        """A descrição vai em chamada própria, depois de o anúncio existir."""
        path = f"/items/{urllib.parse.quote(str(item_id), safe='')}/description"
        self._request("POST", path, token=account.access_token, data={"plain_text": text})

    def validate_item(self, *, account, payload):
        """Simula a publicação em POST /items/validate, que confere sem criar.

        Responde 204 quando o anúncio seria aceito; 400 com a lista `cause` quando não.
        Não passa por `_request` porque aqui o 400 é resposta esperada, não falha —
        o que interessa é justamente o corpo com as causas.
        """
        response = self.transporte(
            "POST", "/items/validate", token=account.access_token, data=payload
        )
        if response.status == 204:
            return []
        if response.status == 400 and isinstance(response.body, dict):
            causas = response.body.get("cause") or []
            if causas:
                return causas
            # 400 sem causa: erro de formato do próprio envio
            return [{
                "type": "error",
                "code": str(response.body.get("message") or "body.invalid"),
                "message": str(response.body.get("error") or response.body.get("message") or ""),
                "references": [],
            }]
        # 401/403/429 e o resto seguem o tratamento comum de erro
        if response.status in (401, 403):
            raise IntegrationError(
                "A autorização do Mercado Livre foi recusada ou expirou.",
                token_invalido=response.status == 401,
            )
        if response.status == 429:
            raise IntegrationError("O Mercado Livre limitou as chamadas. Tente novamente mais tarde.")
        raise IntegrationError(f"Mercado Livre respondeu HTTP {response.status} na validação.")
