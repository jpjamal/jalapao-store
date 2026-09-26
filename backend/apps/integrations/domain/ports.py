"""O contrato que todo marketplace cumpre.

É a costura pensada para o Mercado Livre entrar depois sem mexer nos serviços. Quem chama
não sabe de qual marketplace se trata: pede o adaptador pelo nome do canal e usa estes
métodos. O Mercado Livre entra como `apps/integrations/meli/`, registra-se aqui, e pronto.

As diferenças conhecidas entre os dois moldaram o contrato:

- a Shopee assina cada chamada com HMAC-SHA256 e usa token de 4 horas;
- o Mercado Livre usa OAuth2 com `Bearer` e token de 6 horas, sem assinatura por chamada.

Por isso o contrato não fala em cabeçalho nem em assinatura — fala no que se quer feito.
"""

from dataclasses import dataclass, field


class IntegrationError(Exception):
    """Falha vinda do marketplace, já traduzida para quem chamou."""

    def __init__(self, mensagem, *, codigo="", token_invalido=False):
        super().__init__(mensagem)
        self.codigo = codigo
        self.token_invalido = token_invalido


@dataclass
class Tokens:
    access_token: str
    refresh_token: str
    expires_in: int  # segundos
    external_id: str = ""
    # quando o marketplace informa até quando a própria autorização vale
    authorization_expires_at: object = None


@dataclass
class RemoteItem:
    """Um anúncio do lado de lá, no mínimo comum entre Shopee e Mercado Livre."""

    item_id: str
    title: str = ""
    sku: str = ""
    stock: int | None = None
    price: str = ""
    status: str = ""
    extra: dict = field(default_factory=dict)


class MarketplaceAdapter:
    """Interface. Cada canal implementa; ninguém instancia esta."""

    channel = ""

    # ---------- autorização ----------
    def authorization_url(self, *, state: str = "") -> str:
        raise NotImplementedError

    def exchange_code(self, *, code: str, external_id: str) -> Tokens:
        raise NotImplementedError

    def refresh(self, *, refresh_token: str, external_id: str) -> Tokens:
        raise NotImplementedError

    # ---------- leitura ----------
    def shop_info(self, *, account) -> dict:
        raise NotImplementedError

    def list_items(self, *, account) -> list[RemoteItem]:
        raise NotImplementedError

    # ---------- escrita ----------
    def update_stock(self, *, account, item_id: str, quantity: int) -> None:
        raise NotImplementedError


_ADAPTADORES = {}


def registrar(classe):
    """Decorador de registro: `@registrar` na classe do adaptador."""
    _ADAPTADORES[classe.channel] = classe
    return classe


def adaptador(channel):
    """Devolve o adaptador do canal, já construído a partir das configurações."""
    classe = _ADAPTADORES.get(channel)
    if not classe:
        raise IntegrationError(f"Canal sem integração disponível: {channel}.")
    return classe()


def canais_disponiveis():
    return sorted(_ADAPTADORES)
