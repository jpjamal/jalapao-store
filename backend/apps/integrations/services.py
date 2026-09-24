"""Casos de uso da integração. Nada aqui sabe de qual marketplace se trata.

A regra que vale para o arquivo inteiro: **o marketplace nunca pode atrapalhar a loja**.
Envio acontece fora da transação que mexeu no estoque, falha vira erro registrado no evento,
e nenhuma leitura de lá sobrescreve dado daqui sem o dono mandar.
"""

from datetime import timedelta
import hashlib
import secrets

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.catalog.models import Product
from apps.inventory.models import Stock

from .base import IntegrationError, adaptador
from .models import Listing, MarketplaceAccount, OAuthAttempt, OutboxEvent

# renova o token um pouco antes de vencer, para a chamada não esbarrar no limite
FOLGA_DO_TOKEN = timedelta(minutes=10)
TOPICO_ESTOQUE = "inventory.changed"


def _guardar_tokens(conta, tokens, *, validade_autorizacao=None):
    conta.access_token = tokens.access_token
    conta.refresh_token = tokens.refresh_token or conta.refresh_token
    conta.token_expires_at = timezone.now() + timedelta(seconds=tokens.expires_in)
    if validade_autorizacao:
        conta.authorization_expires_at = validade_autorizacao
    conta.last_error = ""
    conta.save(
        update_fields=[
            "access_token",
            "refresh_token",
            "token_expires_at",
            "authorization_expires_at",
            "last_error",
            "active",
            "updated_at",
        ]
    )
    return conta


def link_de_autorizacao(canal, *, state=""):
    return adaptador(canal).authorization_url(state=state)


def iniciar_oauth_ml(user):
    """Estado de uso único vinculado ao usuário que iniciou a autorização."""
    adapter = adaptador(MarketplaceAccount.Channel.ML)
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48) if adapter.pkce_enabled else ""
    url = adapter.authorization_url(state=state, code_verifier=verifier)
    OAuthAttempt.objects.create(
        state_hash=hashlib.sha256(state.encode()).hexdigest(),
        user=user, code_verifier=verifier, expires_at=timezone.now() + timedelta(minutes=10),
    )
    return url


def conectar_ml(*, user, code, state):
    """Aceita somente retorno da autorização iniciada por este usuário."""
    state_hash = hashlib.sha256(state.encode()).hexdigest()
    with transaction.atomic():
        tentativa = OAuthAttempt.objects.select_for_update().filter(state_hash=state_hash).first()
        if not tentativa or tentativa.user_id != user.pk or tentativa.consumed_at or tentativa.expires_at <= timezone.now():
            raise IntegrationError("Autorização do Mercado Livre inválida ou expirada. Inicie novamente.")
        tentativa.consumed_at = timezone.now()
        tentativa.save(update_fields=["consumed_at", "updated_at"])
        verifier = tentativa.code_verifier
    tokens = adaptador(MarketplaceAccount.Channel.ML).exchange_code(
        code=code, external_id="", code_verifier=verifier,
    )
    if not tokens.external_id or not tokens.refresh_token:
        raise IntegrationError("Mercado Livre não retornou a conta e o refresh token.")
    with transaction.atomic():
        conta, _ = MarketplaceAccount.objects.select_for_update().get_or_create(
            channel=MarketplaceAccount.Channel.ML, external_id=tokens.external_id,
        )
        conta.active = True
        return _guardar_tokens(conta, tokens)


@transaction.atomic
def conectar(*, canal, code, external_id, nome=""):
    """Troca o código do callback por tokens e guarda a loja conectada."""
    if canal == MarketplaceAccount.Channel.ML:
        raise IntegrationError("Mercado Livre exige state; use o fluxo OAuth próprio.")
    adap = adaptador(canal)
    tokens = adap.exchange_code(code=code, external_id=external_id)
    conta, _ = MarketplaceAccount.objects.select_for_update().get_or_create(
        channel=canal, external_id=str(tokens.external_id or external_id)
    )
    conta.active = True
    if nome:
        conta.name = nome
    validade = tokens.authorization_expires_at
    if validade is None and canal == MarketplaceAccount.Channel.SHOPEE:
        from .shopee.cliente import validade_da_autorizacao

        validade = validade_da_autorizacao()
    return _guardar_tokens(conta, tokens, validade_autorizacao=validade)


def renovar(conta):
    if conta.channel == MarketplaceAccount.Channel.ML:
        with transaction.atomic():
            atual = MarketplaceAccount.objects.select_for_update().get(pk=conta.pk)
            if (atual.access_token != conta.access_token and atual.token_valido):
                for campo in ("access_token", "refresh_token", "token_expires_at"):
                    setattr(conta, campo, getattr(atual, campo))
                return conta
            if not atual.refresh_token:
                raise IntegrationError("Conta sem refresh token: autorize novamente.")
            tokens = adaptador(conta.channel).refresh(
                refresh_token=atual.refresh_token, external_id=atual.external_id,
            )
            if not tokens.refresh_token:
                raise IntegrationError("Renovação sem novo refresh token; autorize novamente.")
            _guardar_tokens(atual, tokens)
            for campo in ("access_token", "refresh_token", "token_expires_at"):
                setattr(conta, campo, getattr(atual, campo))
            return conta
    if not conta.refresh_token:
        raise IntegrationError("Loja sem refresh token: autorize novamente.")
    tokens = adaptador(conta.channel).refresh(
        refresh_token=conta.refresh_token, external_id=conta.external_id
    )
    return _guardar_tokens(conta, tokens)


def _token_pronto(conta):
    vencido = not conta.token_expires_at or conta.token_expires_at - FOLGA_DO_TOKEN <= timezone.now()
    if vencido or not conta.access_token:
        renovar(conta)
    return conta


def chamar(conta, operacao, **kwargs):
    """Executa uma operação do adaptador cuidando do token.

    Renova antes se estiver perto de vencer e, se ainda assim o marketplace reclamar do
    token, renova e tenta **uma** vez. Duas tentativas no máximo, para não virar laço.
    """
    if not conta.active:
        raise IntegrationError("Conta desativada; autorize novamente antes de sincronizar.")
    _token_pronto(conta)
    adap = adaptador(conta.channel)
    try:
        return getattr(adap, operacao)(account=conta, **kwargs)
    except IntegrationError as e:
        if not e.token_invalido:
            raise
        renovar(conta)
        return getattr(adap, operacao)(account=conta, **kwargs)


# ---------- catálogo ----------


def importar_anuncios(conta):
    """Traz os anúncios e casa com os produtos pelo código (SKU).

    Nunca cria produto: anúncio sem correspondência fica sem vínculo e aparece na tela como
    pendente, para o dono decidir. Também não mexe em estoque nem em custo.
    """
    itens = chamar(conta, "list_items")
    por_sku = {p.sku.strip().lower(): p for p in Product.objects.all() if p.sku}
    casados, pendentes = 0, []

    for item in itens:
        chave = (item.sku or "").strip().lower()
        produto = por_sku.get(chave) if chave else None
        if not produto:
            pendentes.append({"item_id": item.item_id, "title": item.title, "sku": item.sku})
            continue
        existente = Listing.objects.filter(
            marketplace=conta.channel, seller_id=conta.external_id, item_id=item.item_id,
        ).first()
        if existente and existente.sync_enabled and existente.product_id != produto.pk:
            pendentes.append({"item_id": item.item_id, "title": item.title, "sku": item.sku})
            continue
        defaults = {
            "product": produto,
            "title": item.title[:300],
            "remote_stock": item.stock,
            "user_product_id": str(item.extra.get("user_product_id") or ""),
            "family_id": str(item.extra.get("family_id") or ""),
        }
        if existente and existente.product_id != produto.pk:
            defaults["last_pushed_version"] = None
        vinculo, criado = Listing.objects.update_or_create(
            marketplace=conta.channel,
            seller_id=conta.external_id,
            item_id=item.item_id,
            defaults=defaults,
        )
        casados += 1 if criado else 0

    conta.last_synced_at = timezone.now()
    conta.save(update_fields=["last_synced_at", "updated_at"])
    return {"total": len(itens), "vinculos_novos": casados, "pendentes": pendentes}


# ---------- estoque ----------


def enviar_estoque(conta, *, teto=100):
    """Envia o saldo atual por anúncio e reconcilia a fila entre todas as contas Shopee."""
    if conta.channel == MarketplaceAccount.Channel.ML:
        return enviar_estoque_ml(conta, teto=teto)
    if not conta.active:
        raise IntegrationError("Conta desativada; autorize novamente antes de sincronizar.")
    enviados, ignorados, falhas = 0, 0, []
    ids = list(Listing.objects.filter(
        marketplace=MarketplaceAccount.Channel.SHOPEE,
        seller_id=conta.external_id,
        sync_enabled=True,
    ).order_by("item_id").values_list("pk", flat=True))
    for listing_id in ids:
        if enviados + len(falhas) >= teto:
            break
        # A trava impede que duas solicitações enviem versões em ordem inversa.
        with transaction.atomic():
            vinculo = Listing.objects.select_for_update().get(pk=listing_id)
            if not vinculo.sync_enabled:
                continue
            try:
                # Nova consulta depois de adquirir a trava: evita snapshot antigo
                # quando outra sincronização aguardou a primeira terminar.
                saldo = Stock.objects.get(product_id=vinculo.product_id)
            except Stock.DoesNotExist:
                ignorados += 1
                continue
            if vinculo.last_pushed_version == saldo.version:
                ignorados += 1
                continue
            try:
                chamar(conta, "update_stock", item_id=vinculo.item_id, quantity=saldo.quantity)
            except IntegrationError as exc:
                erro = f"{vinculo.item_id}: {exc}"[:500]
                falhas.append(erro)
                OutboxEvent.objects.filter(
                    topic=TOPICO_ESTOQUE,
                    delivered_at__isnull=True,
                    payload__product_id=str(vinculo.product_id),
                ).update(attempts=F("attempts") + 1, last_error=erro, updated_at=timezone.now())
                continue
            vinculo.remote_stock = saldo.quantity
            vinculo.last_pushed_version = saldo.version
            vinculo.stock_pushed_at = timezone.now()
            vinculo.save(update_fields=[
                "remote_stock", "last_pushed_version", "stock_pushed_at", "updated_at",
            ])
            OutboxEvent.objects.filter(
                topic=TOPICO_ESTOQUE,
                delivered_at__isnull=True,
                payload__product_id=str(vinculo.product_id),
            ).update(attempts=F("attempts") + 1, updated_at=timezone.now())
            enviados += 1

    # A entrega é global somente quando todos os anúncios Shopee habilitados para o
    # produto receberam uma versão ao menos tão recente quanto a do evento.
    eventos = OutboxEvent.objects.filter(
        topic=TOPICO_ESTOQUE, delivered_at__isnull=True,
    ).order_by("created_at", "id")[:teto]
    for event_id in eventos.values_list("pk", flat=True):
        with transaction.atomic():
            evento = OutboxEvent.objects.select_for_update().get(pk=event_id)
            if evento.delivered_at:
                continue
            payload = evento.payload or {}
            product_id, version = payload.get("product_id"), payload.get("version")
            if not product_id or not isinstance(version, int):
                evento.last_error = "Evento de estoque sem produto ou versão válida."
                evento.save(update_fields=["last_error", "updated_at"])
                continue
            contas_ativas = MarketplaceAccount.objects.filter(
                channel=MarketplaceAccount.Channel.SHOPEE,
                active=True,
            ).values("external_id")
            vinculos = Listing.objects.filter(
                marketplace=MarketplaceAccount.Channel.SHOPEE,
                product_id=product_id,
                sync_enabled=True,
                seller_id__in=contas_ativas,
            )
            if vinculos.filter(last_pushed_version__isnull=True).exists() or vinculos.filter(
                last_pushed_version__lt=version,
            ).exists():
                continue
            evento.delivered_at = timezone.now()
            evento.last_error = ""
            evento.save(update_fields=["delivered_at", "last_error", "updated_at"])
            if not vinculos.exists():
                ignorados += 1
    return {"enviados": enviados, "ignorados": ignorados, "falhas": falhas}


def enviar_estoque_ml(conta, *, teto=100):
    """Envia saldo atual a pedido do usuário sem consumir a fila compartilhada."""
    vinculos = Listing.objects.filter(
        marketplace=MarketplaceAccount.Channel.ML, seller_id=conta.external_id,
        sync_enabled=True,
    ).select_related("product", "product__stock").order_by("item_id")[:teto]
    enviados, ignorados, falhas = 0, 0, []
    for vinculo in vinculos:
        try:
            saldo = vinculo.product.stock.quantity
        except Product.stock.RelatedObjectDoesNotExist:
            ignorados += 1
            continue
        try:
            chamar(conta, "update_stock", item_id=vinculo.item_id, quantity=saldo)
        except IntegrationError as exc:
            falhas.append(f"{vinculo.item_id}: {exc}"[:500])
            continue
        vinculo.remote_stock = saldo
        vinculo.stock_pushed_at = timezone.now()
        vinculo.save(update_fields=["remote_stock", "stock_pushed_at", "updated_at"])
        enviados += 1
    return {"enviados": enviados, "ignorados": ignorados, "falhas": falhas}


def situacao(conta):
    return {
        "id": str(conta.id),
        "channel": conta.channel,
        "channel_label": conta.get_channel_display(),
        "external_id": conta.external_id,
        "name": conta.name,
        "active": conta.active,
        "token_valido": conta.token_valido,
        "authorization_expires_at": (
            conta.authorization_expires_at.isoformat() if conta.authorization_expires_at else None
        ),
        "authorization_days_left": conta.dias_ate_expirar_autorizacao,
        "last_synced_at": conta.last_synced_at.isoformat() if conta.last_synced_at else None,
        "last_error": conta.last_error,
    }
