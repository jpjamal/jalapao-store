from apps.common.permissions import ModelPermissions


class AccountPermissions(ModelPermissions):
    """Aqui o POST não cria registro: conecta, importa, sincroniza — tudo é alteração.

    O mapa padrão do DRF manda POST pedir `add_`, o que obrigaria a dar permissão de criar
    conta para quem só vai mandar sincronizar. Mapeado para `change_`, que é o que essas
    ações realmente fazem.
    """

    perms_map = {**ModelPermissions.perms_map, "POST": ["%(app_label)s.change_%(model_name)s"]}
