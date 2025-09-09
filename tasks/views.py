from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions, generics
from .models import Task, Team
from .serializers import TaskSerializer, TeamSerializer, RegisterSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count



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
    
    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        user = request.user
        queryset = self.get_queryset()

        summary = queryset.values('status').annotate(count=Count('id'))
        return Response(summary)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer