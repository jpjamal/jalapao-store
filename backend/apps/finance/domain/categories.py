"""Categorias do Caixa e origem do lançamento (spec 026): regras puras, sem banco."""

# Categorias do sistema: só os lançamentos automáticos as usam. Chave estável, e não o nome, para o
# código achá-las mesmo que alguém renomeie. (nome, direção)
SYSTEM_CATEGORIES = {
    "sale_adjustment": ("Correção de venda", "both"),
    "sale_received": ("Venda recebida", "in"),
    "sale_refund": ("Estorno de venda", "out"),
    "purchase": ("Compra de produtos", "out"),
    "purchase_refund": ("Estorno de compra de produtos", "in"),
    "supply_purchase": ("Compra de insumos", "out"),
    "supply_refund": ("Estorno de compra de insumos", "in"),
    "unclassified": ("A classificar", "both"),
}

# Origem do lançamento, para a tela mostrar de onde veio.
ORIGINS = {
    "sale_adjustment": "Correção de venda",
    "sale": "Venda",
    "sale_refund": "Estorno de venda",
    "purchase": "Compra de estoque",
    "purchase_refund": "Estorno de compra de estoque",
    "supply": "Compra de insumo",
    "supply_refund": "Estorno de compra de insumo",
    "manual": "Manual",
}

SYSTEM_KEY_OF_ORIGIN = {
    "sale_adjustment": "sale_adjustment",
    "sale": "sale_received",
    "sale_refund": "sale_refund",
    "purchase": "purchase",
    "purchase_refund": "purchase_refund",
    "supply": "supply_purchase",
    "supply_refund": "supply_refund",
    "manual": "unclassified",
}


def origin_of(
    *, direction, sale=False, receipt=False, refund_of_receipt=False, supply_receipt=False,
    refund_of_supply_receipt=False, sale_revision=False,
) -> str:
    """De onde veio o lançamento. Os argumentos dizem se a ligação existe (id preenchido)."""
    if sale_revision:
        return "sale_adjustment"
    if sale:
        return "sale" if direction == "in" else "sale_refund"
    if receipt:
        return "purchase"
    if refund_of_receipt:
        return "purchase_refund"
    if supply_receipt:
        return "supply"
    if refund_of_supply_receipt:
        return "supply_refund"
    return "manual"


def system_key_for(origin: str) -> str:
    """Categoria do sistema de um lançamento, pela origem. Manual sem categoria cai em A classificar."""
    return SYSTEM_KEY_OF_ORIGIN[origin]


def direction_fits(category_direction: str, entry_direction: str) -> bool:
    """A direção do lançamento tem de combinar com a da categoria (`both` serve para as duas)."""
    return category_direction == "both" or category_direction == entry_direction
