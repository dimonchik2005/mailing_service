from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Создаёт и настраивает группу менеджеров."""

    help = "Создаёт группу менеджеров и назначает права"

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(
            name="Менеджеры",
        )

        permissions = [
            Permission.objects.get(
                content_type__app_label="mailings",
                codename="can_disable_mailing",
            ),
            Permission.objects.get(
                content_type__app_label="users",
                codename="can_block_user",
            ),
        ]

        group.permissions.set(permissions)

        if created:
            message = (
                "Группа «Менеджеры» создана и настроена."
            )
        else:
            message = (
                "Права группы «Менеджеры» обновлены."
            )

        self.stdout.write(
            self.style.SUCCESS(message)
        )