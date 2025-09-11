from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions, generics
from .models import Task, Team, Category, Comment, TaskLog, Profile
from .serializers import TaskSerializer, TeamSerializer, RegisterSerializer, CategorySerializer, CommentSerializer, TaskLogSerializer, UserSerializer, ProfileSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from .permissions import IsTeamManagerOrAssigned


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamManagerOrAssigned]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['completed', 'team', 'due_date', 'status', 'category', 'priority']


    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Task.objects.all()
        
        if not hasattr(user, 'profile'):
            return Task.objects.none()
        
        profile = user.profile

        if profile.role == 'manager':
            return Task.objects.filter(team=profile.team)
        
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


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TaskLogViewSet(viewsets.ModelViewSet):
    queryset = TaskLog.objects.all()
    serializer_class = TaskLogSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.select_related('user', 'team').all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer): 
        serializer.save()