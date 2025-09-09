from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions, generics
from .models import Task, Team
from .serializers import TaskSerializer, TeamSerializer, RegisterSerializer
from django_filters.rest_framework import DjangoFilterBackend


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['completed', 'team', 'due_date', 'status']


    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Task.objects.all()
        return Task.objects.filter(assigned_to=user)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer