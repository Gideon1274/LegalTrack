from django.dispatch import receiver
from django.db.models.signals import pre_save
from documents.models import Case
from .models import CaseTransition


@receiver(pre_save, sender=Case)
def log_case_transition(sender, instance, **kwargs):
    if not instance._state.adding:
        previous = sender.objects.get(pk=instance.pk)
    if previous.status != instance.status:
        CaseTransition.objects.create(
            case=instance,
            old_status=previous.status,
            new_status=instance.status,
            changed_by='system',
)