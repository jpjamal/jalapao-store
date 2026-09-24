"""A assinatura das chamadas da Shopee, isolada porque é onde todo mundo erra.

Toda chamada v2 leva `sign`: um HMAC-SHA256 do `partner_key` sobre uma string montada em
ordem fixa, em hexadecimal minúsculo. A ordem muda conforme o tipo de chamada:

- **pública** (pedir ou renovar token, ainda sem loja):
  `partner_id + caminho + timestamp`
- **de loja** (o resto, já autorizado):
  `partner_id + caminho + timestamp + access_token + shop_id`

O `caminho` é o do endpoint, com barra na frente e sem o domínio —
`/api/v2/product/get_item_list`. O `timestamp` é em segundos e vale 5 minutos.

Fica sozinho neste arquivo de propósito: é função pura, dá para conferir contra um caso
conhecido sem rede, sem credencial e sem banco.
"""

import hashlib
import hmac
import time


def timestamp_agora():
    return int(time.time())


def base_string(*, partner_id, caminho, timestamp, access_token="", shop_id=""):
    """Monta a string na ordem exigida. Campos vazios simplesmente não entram."""
    return f"{partner_id}{caminho}{timestamp}{access_token}{shop_id}"


def assinar(*, partner_key, partner_id, caminho, timestamp, access_token="", shop_id=""):
    texto = base_string(
        partner_id=partner_id,
        caminho=caminho,
        timestamp=timestamp,
        access_token=access_token,
        shop_id=shop_id,
    )
    return hmac.new(
        str(partner_key).encode("utf-8"), texto.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def parametros_comuns(
    *, partner_id, partner_key, caminho, timestamp=None, access_token="", shop_id=""
):
    """Os parâmetros que vão na query de toda chamada, já com a assinatura."""
    timestamp = timestamp or timestamp_agora()
    comuns = {
        "partner_id": partner_id,
        "timestamp": timestamp,
        "sign": assinar(
            partner_key=partner_key,
            partner_id=partner_id,
            caminho=caminho,
            timestamp=timestamp,
            access_token=access_token,
            shop_id=shop_id,
        ),
    }
    if access_token:
        comuns["access_token"] = access_token
    if shop_id:
        comuns["shop_id"] = shop_id
    return comuns
