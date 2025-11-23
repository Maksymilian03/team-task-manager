from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Task, Comment, Notification

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

def _notify(user: User, message: str, task: Task | None = None):
    if user is None:
        return
    Notification.objects.create(user=user, message=message, task=task)

@receiver(pre_save, sender=Task)
def task_before_save(sender, instance: Task, **kwargs):
    # zachowaj poprzedniego assigned_to / status do porównania po zapisie
    if instance.pk:
        try:
            original = Task.objects.get(pk=instance.pk)
            instance._was_assigned_to = original.assigned_to
            instance._old_status = original.status
        except Task.DoesNotExist:
            instance._was_assigned_to = None
            instance._old_status = None
    else:
        instance._was_assigned_to = None
        instance._old_status = None

@receiver(post_save, sender=Task)
def task_after_save(sender, instance: Task, created, **kwargs):
    if created:
        if instance.assigned_to:
            _notify(
                instance.assigned_to,
                f"Przypisano do Ciebie nowe zadanie: “{instance.title}”.",
                task=instance
            )
        return

    # zmiana przypisanego
    prev = getattr(instance, '_was_assigned_to', None)
    if prev != instance.assigned_to:
        if instance.assigned_to:
            _notify(instance.assigned_to, f"Otrzymałeś zadanie: “{instance.title}”.", task=instance)
        if prev:
            _notify(prev, f"Zadanie “{instance.title}” nie jest już do Ciebie przypisane.", task=instance)

    # zmiana statusu
    old_status = getattr(instance, '_old_status', None)
    if old_status and old_status != instance.status and instance.assigned_to:
        _notify(
            instance.assigned_to,
            f"Status zadania “{instance.title}” zmieniono: {old_status} → {instance.status}.",
            task=instance
        )

@receiver(post_save, sender=Comment)
def comment_created(sender, instance: Comment, created, **kwargs):
    if not created:
        return
    task = instance.task
    # główny adresat – osoba przypisana
    if task.assigned_to and task.assigned_to != instance.author:
        _notify(
            task.assigned_to,
            f"Nowy komentarz do zadania “{task.title}”: {instance.author.username}: {instance.content[:80]}",
            task=task
        )
