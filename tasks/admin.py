from django.contrib import admin
from .models import Task, Profile, Team, Category


# Register your models here.


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'assigned_to', 'due_date', 'status', 'team']
    list_filter = ['status', 'due_date', 'team']
    search_fields = ['title', 'description']
    


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'team']
    list_filter = ['role', 'team']
    search_fields = ['user__username']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name']
    filter_horizontal = ['members',]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']