from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand, CommandError

GROUP_NAME = "Контент-менеджер"

# Что может редактор контента: всё про контент сайта и правка (но не
# создание/удаление) текстов. Пользователи, группы и прочие настройки — нет.
PERMISSIONS = {
    "content": {
        "review": ["view", "add", "change", "delete"],
        "beforeafter": ["view", "add", "change", "delete"],
        "service": ["view", "add", "change", "delete"],
        "servicepage": ["view", "add", "change", "delete"],
        "servicepagefaq": ["view", "add", "change", "delete"],
        "partner": ["view", "add", "change", "delete"],
        "chemicalbrand": ["view", "add", "change", "delete"],
    },
    "api": {"item": ["view", "change"]},
}


class Command(BaseCommand):
    help = (
        "Создаёт/обновляет группу «Контент-менеджер». С --user USERNAME ещё и "
        "заводит такого сотрудника (без пароля: его задают командой changepassword)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--user", help="Логин сотрудника, которого добавить в группу")
        parser.add_argument("--first-name", default="", help="Имя для приветствия в админке")

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name=GROUP_NAME)
        perms = []
        for app_label, models in PERMISSIONS.items():
            for model, actions in models.items():
                for action in actions:
                    codename = f"{action}_{model}"
                    try:
                        perms.append(
                            Permission.objects.get(
                                content_type__app_label=app_label, codename=codename
                            )
                        )
                    except Permission.DoesNotExist as e:
                        raise CommandError(f"Нет права {app_label}.{codename}") from e
        group.permissions.set(perms)
        self.stdout.write(f"Группа «{GROUP_NAME}»: {len(perms)} прав")

        username = options.get("user")
        if not username:
            return
        user, created = User.objects.get_or_create(username=username)
        user.is_staff = True
        user.is_superuser = False
        if options["first_name"]:
            user.first_name = options["first_name"]
        if created:
            user.set_unusable_password()
        user.save()
        user.groups.add(group)
        state = "создан" if created else "обновлён"
        self.stdout.write(f"Пользователь {username} {state}, добавлен в группу.")
        if created:
            self.stdout.write(
                f"Пароль не задан. Задайте его: python manage.py changepassword {username}"
            )
