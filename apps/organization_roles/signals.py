from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.organization_roles.models import OrganizationRoleUser
from apps.organization_roles.services import clear_user_permission_cache


@receiver(post_save, sender=OrganizationRoleUser)
def handle_post_save(sender, instance, created, **kwargs):
    user_id = getattr(instance, "root_user_id", None)
    clear_user_permission_cache(user_id)


@receiver(post_delete, sender=OrganizationRoleUser)
def handle_post_delete(sender, instance, **kwargs):
    user_id = getattr(instance, "root_user_id", None)
    clear_user_permission_cache(user_id)
