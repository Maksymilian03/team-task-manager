from django.db import models
from django.contrib.auth.models import User
from taggit.managers import TaggableManager


class Team(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name='teams')

    def __str__(self):
        return self.name
    

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
    
class TaskStatusOption(models.Model):
    value = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'label']

    def __str__(self):
        return self.label


class TaskPriorityOption(models.Model):
    value = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'label']

    def __str__(self):
        return self.label


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='tasks')
    due_date = models.DateTimeField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='todo')
    priority = models.CharField(max_length=50, default='medium')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    tags = TaggableManager(blank=True)

    def __str__(self):
        return self.title
    

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Komentarz {self.author.username} do zadania: {self.task.title}"
    

class TaskLog(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_type = models.CharField(max_length=100)  # np. "status", "opis"
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Zmiana {self.change_type} przez {self.user} - ({self.timestamp})"
    

class Profile(models.Model):
    ROLE_CHOICES = (
        ('manager', 'Menedżer'),
        ('employee', 'Prawcownik'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - ({self.role}), team: {self.team}"
    

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=500)
    task = models.ForeignKey('Task', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.user}] {self.message[:60]}"
    

class GoogleCredentials(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="google_credentials")
    # zapisujemy JSON wygenerowany przez Credentials.to_json()
    credentials_json = models.JSONField()

    def __str__(self):
        return f"Google creds for {self.user.username}"


class GoogleOAuthState(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="google_oauth_states")
    state = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["state"])]

    def __str__(self):
        return f"OAuthState for {self.user}"

 
    
