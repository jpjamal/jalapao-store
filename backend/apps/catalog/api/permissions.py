from apps.common.permissions import ModelPermissions


class DraftChangePermission(ModelPermissions):
    """Validar é POST mas não cria nada: exige permissão de alterar rascunho, não de criar."""

    perms_map = {**ModelPermissions.perms_map, "POST": ["%(app_label)s.change_%(model_name)s"]}


class DraftPublishPermission(DraftChangePermission):
    """Publicar cria anúncio de verdade: além de alterar rascunho, exige a permissão própria."""

    perms_map = {
        **DraftChangePermission.perms_map,
        "POST": ["%(app_label)s.change_%(model_name)s", "%(app_label)s.publish_%(model_name)s"],
    }
