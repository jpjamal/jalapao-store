import uuid

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from apps.sales.models import Sale


class SaleEditMigrationTests(TransactionTestCase):
    def test_existing_marketplace_sale_keeps_its_import_origin(self):
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        before = [("sales", "0004_pedidos_de_marketplace")]
        executor.migrate(before)
        try:
            old = executor.loader.project_state(before).apps
            user = old.get_model("accounts", "User").objects.create(username="historical-sale")
            original = old.get_model("sales", "Sale").objects.create(
                channel="mercado_livre",
                external_id="2000001",
                idempotency_key=uuid.uuid4(),
                request_hash="h",
                gross=20,
                cost_total=8,
                net=20,
                profit=12,
                actor=user,
            )
        finally:
            MigrationExecutor(connection).migrate(latest)

        migrated = Sale.objects.get(pk=original.pk)
        self.assertEqual((migrated.external_channel, migrated.external_id), ("mercado_livre", "2000001"))
        self.assertIsNone(migrated.deleted_at)
