from django.core.mail import send_mail
from django.conf import settings

def send_task_notification(task, recipient_email):
    subject = f"Nowe zadanie: {task.title}"
    message = (
        f"Cześć!\n\n"
        f"Otrzymałeś nowe zadanie:\n"
        f"Tytuł: {task.title}\n"
        f"Opis: {task.description}\n"
        f"Termin: {task.due_date}\n"
        f"Priorytet: {task.priority}\n\n"
        f"Pozdrawiamy,\nZespół Task Managera"
    )
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER or "noreply@taskmanager.com",
        [recipient_email],
        fail_silently=False,
    )
