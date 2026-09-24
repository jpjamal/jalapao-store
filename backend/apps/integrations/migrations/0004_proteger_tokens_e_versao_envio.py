from django.db import migrations, models

from apps.integrations import fields as token_fields


def cifrar_legado(apps, schema_editor):
    Account = apps.get_model("integrations", "MarketplaceAccount")
    Attempt = apps.get_model("integrations", "OAuthAttempt")
    alias = schema_editor.connection.alias
    for conta in Account.objects.using(alias).iterator():
        updates = {}
        for nome in ("access_token", "refresh_token"):
            valor = getattr(conta, nome)
            if valor and not valor.startswith(token_fields.PREFIXO):
                updates[nome] = token_fields.cifrar(valor)
        if updates:
            Account.objects.using(alias).filter(pk=conta.pk).update(**updates)
    for tentativa in Attempt.objects.using(alias).iterator():
        valor = tentativa.code_verifier
        if valor and not valor.startswith(token_fields.PREFIXO):
            Attempt.objects.using(alias).filter(pk=tentativa.pk).update(
                code_verifier=token_fields.cifrar(valor),
            )


class Migration(migrations.Migration):
    dependencies = [
        ("integrations", "0003_oauthattempt"),
    ]

    operations = [
        migrations.AddField(
            model_name="listing", name="last_pushed_version",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="marketplaceaccount", name="access_token",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="marketplaceaccount", name="refresh_token",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="oauthattempt", name="code_verifier",
            field=models.TextField(blank=True),
        ),
        migrations.RunPython(cifrar_legado),
        migrations.AlterField(
            model_name="marketplaceaccount", name="access_token",
            field=token_fields.EncryptedTextField(blank=True),
        ),
        migrations.AlterField(
            model_name="marketplaceaccount", name="refresh_token",
            field=token_fields.EncryptedTextField(blank=True),
        ),
        migrations.AlterField(
            model_name="oauthattempt", name="code_verifier",
            field=token_fields.EncryptedTextField(blank=True),
        ),
    ]
