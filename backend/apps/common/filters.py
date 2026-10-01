"""Busca, ordenação e período das listagens (spec 027), iguais em todas as telas.

O banco de produção (PostgreSQL alpine) ordena texto por byte e o SQLite só trata ASCII, então "Água" iria
depois de "Zebra" e "agua" não acharia "Água". Por isso a busca e a ordenação de texto trabalham sobre o texto
**sem acento e em minúsculas**, calculado no próprio banco com `Replace`, que funciona igual nos dois.
"""

import unicodedata
from functools import reduce
from operator import and_, or_

import django_filters
from decimal import Decimal

from django.db.models import CharField, DecimalField, F, Func, Q, Value
from django.db.models.functions import Coalesce
from rest_framework.filters import OrderingFilter, SearchFilter

# letras acentuadas e a letra simples minúscula que as substitui, para a busca e a ordenação
_PLAIN = {
    "a": "áàâãäåÁÀÂÃÄÅ",
    "e": "éèêëÉÈÊË",
    "i": "íìîïÍÌÎÏ",
    "o": "óòôõöÓÒÔÕÖ",
    "u": "úùûüÚÙÛÜ",
    "c": "çÇ",
    "n": "ñÑ",
}
_FROM = "".join(chars for chars in _PLAIN.values())
_TO = "".join(plain * len(chars) for plain, chars in _PLAIN.items())


def fold_text(text: str) -> str:
    """O mesmo tratamento do banco, em Python: minúsculas e sem acento."""
    decomposed = unicodedata.normalize("NFD", text or "")
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def _fold_sql(value):
    return None if value is None else fold_text(str(value))


class Fold(Func):
    """Texto do campo em minúsculas e sem acento, calculado no banco. No PostgreSQL é `LOWER(TRANSLATE(...))`,
    uma chamada só; no SQLite, uma função registrada que usa o `fold_text` acima."""

    function = "PT_FOLD"
    arity = 1
    output_field = CharField()

    def as_postgresql(self, compiler, connection, **extra):
        return self.as_sql(
            compiler, connection, function="LOWER",
            template=f"%(function)s(TRANSLATE(%(expressions)s, '{_FROM}', '{_TO}'))", **extra,
        )

    def as_sqlite(self, compiler, connection, **extra):
        connection.ensure_connection()
        connection.connection.create_function("PT_FOLD", 1, _fold_sql, deterministic=True)
        return self.as_sql(compiler, connection, **extra)


def folded(field: str):
    """Expressão do banco com o texto do campo sem acento e em minúsculas."""
    return Fold(field)


def _many_valued(model, path: str) -> bool:
    """O caminho passa por uma relação que repete linhas (reversa ou muitos-para-muitos)?"""
    current = model
    for part in path.split("__")[:-1]:
        field = current._meta.get_field(part)
        if field.many_to_many or field.one_to_many:
            return True
        current = field.related_model
    return False


class FoldedSearchFilter(SearchFilter):
    """`?search=` que ignora maiúscula e acento, nos `search_fields` da tela. Várias palavras: todas
    precisam aparecer, cada uma em algum dos campos."""

    def filter_queryset(self, request, queryset, view):
        fields = [f.lstrip("^=@$") for f in (self.get_search_fields(view, request) or [])]
        terms = self.get_search_terms(request)
        if not fields or not terms:
            return queryset
        aliases = {field: f"_busca_{i}" for i, field in enumerate(fields)}
        queryset = queryset.alias(**{alias: folded(field) for field, alias in aliases.items()})
        conditions = [
            reduce(or_, [Q(**{f"{alias}__contains": fold_text(term)}) for alias in aliases.values()])
            for term in terms
        ]
        queryset = queryset.filter(reduce(and_, conditions))
        if any(_many_valued(queryset.model, field) for field in fields):
            queryset = queryset.distinct()
        return queryset


class StableOrderingFilter(OrderingFilter):
    """`?ordering=campo` ou `-campo`, só nos campos que a tela declara em `ordering_fields`. Os campos de
    texto que a tela lista em `ordering_text_fields` ordenam sem acento e sem diferenciar maiúscula, e os de
    `ordering_zero_fields` tratam "sem registro" como zero (produto ou insumo que nunca teve estoque). Valor
    vazio vai sempre para o fim, nos dois sentidos e em qualquer banco. A ordem termina no `pk`, para uma
    linha não pular de página entre duas consultas."""

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if not ordering:
            return queryset
        text_fields = set(getattr(view, "ordering_text_fields", ()))
        zero_fields = set(getattr(view, "ordering_zero_fields", ()))
        expressions = []
        for item in ordering:
            name = item.lstrip("-")
            if name in text_fields:
                base = folded(name)
            elif name in zero_fields:
                base = Coalesce(F(name), Value(Decimal(0)), output_field=DecimalField(max_digits=20, decimal_places=6))
            else:
                base = F(name)
            expressions.append(base.desc(nulls_last=True) if item.startswith("-") else base.asc(nulls_last=True))
        if not any(item.lstrip("-") in ("pk", "id") for item in ordering):
            expressions.append("pk")
        return queryset.order_by(*expressions)


def range_filterset(model, *, date_field, fields=(), datetime_field=False, extra=None):
    """FilterSet com `date_from` e `date_to` (dia inclusive) sobre `date_field`, mais os filtros exatos de
    `fields` e os `extra` declarados à mão."""
    prefix = "date__" if datetime_field else ""
    attributes = {
        "date_from": django_filters.DateFilter(field_name=date_field, lookup_expr=f"{prefix}gte"),
        "date_to": django_filters.DateFilter(field_name=date_field, lookup_expr=f"{prefix}lte"),
        "Meta": type("Meta", (), {"model": model, "fields": list(fields)}),
        **(extra or {}),
    }
    return type(f"{model.__name__}ListFilterSet", (django_filters.FilterSet,), attributes)
