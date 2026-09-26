from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    name = "apps.integrations"

    def ready(self):
        """Importar o pacote de cada canal é o que registra o adaptador.

        Sem isto nada importa `apps.integrations.infrastructure.shopee` na aplicação rodando, o decorador
        `@registrar` nunca executa e a tela responde "canal sem integração disponível" —
        embora os testes passem, porque lá o módulo é importado direto.
        """
        from apps.integrations.infrastructure import mercado_livre, shopee  # noqa: F401
