import uuid

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from apps.finance.models import CashCategory, CashEntry
from apps.supplies.models import SupplyCategory


class CashCategoriesMigrationTests(TransactionTestCase):
    def test_existing_entries_are_classified_by_origin_and_manual_ones_wait(self):
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        # A migração 0006 de finance depende da 0005 de sales. As duas precisam voltar juntas
        # para que o modelo histórico e a tabela física de Sale tenham as mesmas colunas.
        before = [("finance", "0004_estoque_compras_insumos"), ("sales", "0004_pedidos_de_marketplace")]
        executor.migrate(before)
        try:
            old = executor.loader.project_state(before).apps
            user = old.get_model("accounts", "User").objects.create(username="historical-cash")
            sale = old.get_model("sales", "Sale").objects.create(
                channel="direct", idempotency_key=uuid.uuid4(), request_hash="h", gross=20, cost_total=8,
                net=20, profit=12, actor=user,
            )
            Entry = old.get_model("finance", "CashEntry")
            common = dict(description="Antigo", occurred_on="2026-09-01", actor=user)
            Entry.objects.create(direction="out", amount=10, **common)  # manual
            Entry.objects.create(direction="in", amount=5, **common)  # manual
            Entry.objects.create(direction="in", amount=20, sale=sale, **common)  # recebimento de venda
            Entry.objects.create(direction="out", amount=20, sale=sale, **common)  # estorno de venda
        finally:
            MigrationExecutor(connection).migrate(latest)
        by_amount = {}
        for entry in CashEntry.objects.select_related("category"):
            by_amount.setdefault((entry.direction, entry.category.name), 0)
            by_amount[(entry.direction, entry.category.name)] += 1
        self.assertEqual(
            by_amount,
            {
                ("out", "A classificar"): 1,
                ("in", "A classificar"): 1,
                ("in", "Venda recebida"): 1,
                ("out", "Estorno de venda"): 1,
            },
        )
        unclassified = CashCategory.objects.get(system_key="unclassified")
        self.assertFalse(unclassified.counts_in_result)
        # as iniciais do dono: Energia não conta (a energia estimada já está no custo da peça), imposto conta
        self.assertFalse(CashCategory.objects.get(name="Energia").counts_in_result)
        self.assertTrue(CashCategory.objects.get(name="Impostos e taxas").counts_in_result)
        self.assertFalse(CashCategory.objects.get(name="Retirada do dono").counts_in_result)
        correction = CashCategory.objects.get(system_key="sale_adjustment")
        self.assertEqual((correction.direction, correction.counts_in_result), ("both", False))
        self.assertEqual(CashCategory.objects.filter(system_key__isnull=False).count(), 8)


class SupplyExpenseOptionMigrationTests(TransactionTestCase):
    def test_option_is_off_only_where_the_cost_is_already_in_the_piece(self):
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        before = [("supplies", "0003_insumos_na_venda")]
        executor.migrate(before)
        try:
            old = executor.loader.project_state(before).apps
            Category = old.get_model("supplies", "SupplyCategory")
            for name in ["Filamentos", "Acabamento", "Colas e fitas", "Embalagens", "Etiquetas e papelaria", "Outra do dono"]:
                Category.objects.create(name=name)
        finally:
            MigrationExecutor(connection).migrate(latest)
        flags = dict(SupplyCategory.objects.values_list("name", "counts_as_expense"))
        self.assertEqual(
            flags,
            {
                "Filamentos": False,
                "Acabamento": False,
                "Colas e fitas": False,
                "Embalagens": True,
                "Etiquetas e papelaria": True,
                "Outra do dono": True,
            },
        )
