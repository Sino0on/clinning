"""Права на «Страницы услуг» для группы «Контент-менеджер».

Права Django создаёт только после всех миграций (post_migrate), поэтому
здесь создаём их заранее сами. Если группы нет (свежая база), ничего не
делаем: её создаст команда setup_content_editor, в ней новые права уже есть.
"""

from django.contrib.auth.management import create_permissions
from django.db import migrations

GROUP_NAME = "Контент-менеджер"
CODENAMES = [
    f"{action}_{model}"
    for model in ("servicepage", "servicepagefaq")
    for action in ("view", "add", "change", "delete")
]


def grant(apps, schema_editor):
    app_config = apps.get_app_config("content")
    app_config.models_module = True
    create_permissions(app_config, apps=apps, verbosity=0)
    app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    group = Group.objects.filter(name=GROUP_NAME).first()
    if group is None:
        return
    group.permissions.add(
        *Permission.objects.filter(content_type__app_label="content", codename__in=CODENAMES)
    )


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("content", "0003_service_pages"),
    ]

    operations = [migrations.RunPython(grant, migrations.RunPython.noop)]
