"""Spec 016 — migração que dá o SKU no padrão atual aos produtos com código do site anterior."""

import importlib

from django.apps import apps
from django.test import TestCase

from apps.catalog.models import Product, sku_initials

migracao = importlib.import_module("apps.catalog.migrations.0005_padronizar_sku")


class PadronizarSkuTests(TestCase):
    def test_codigo_antigo_vira_padrao_e_o_novo_nao_muda(self):
        dummy = Product.objects.create(name="Dummy Aranha Articulado Montado Base Pack de Mãos Katanas",
                                       sku="p_mu33g2qt_gy1hi")
        luminaria = Product.objects.create(name="Luminária Air Form", sku="p_mu5w9zrx_zx7pl")
        novo = Product.objects.create(name="Suporte de Celular")  # já nasce no padrão
        codigo_do_novo = novo.sku

        migracao.padronizar(apps, None)

        dummy.refresh_from_db()
        luminaria.refresh_from_db()
        novo.refresh_from_db()
        self.assertRegex(dummy.sku, r"^SKU-DAAMBP-\d{4,}$")
        self.assertRegex(luminaria.sku, r"^SKU-LAF-\d{4,}$")
        self.assertEqual(novo.sku, codigo_do_novo)
        self.assertEqual(len({dummy.sku, luminaria.sku, novo.sku}), 3)

    def test_rodar_de_novo_nao_muda_nada(self):
        Product.objects.create(name="Luminária Air Form", sku="p_mu5w9zrx_zx7pl")
        migracao.padronizar(apps, None)
        antes = list(Product.objects.values_list("sku", flat=True))
        migracao.padronizar(apps, None)
        self.assertEqual(list(Product.objects.values_list("sku", flat=True)), antes)

    def test_iniciais_iguais_as_do_cadastro(self):
        # a migração copia a regra; se a do app mudar, este teste avisa
        for nome in ["Luminária Pimentão 3D", "Carregador Turbo 20W USB-C", "de da do", "Óculos para Sol"]:
            self.assertEqual(migracao.iniciais(nome), sku_initials(nome))
