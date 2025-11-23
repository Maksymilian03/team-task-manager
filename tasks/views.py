import logging

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Count
from django.http import JsonResponse
from google_auth_oauthlib.flow import Flow
from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta

from .models import (
    Task,
    Team,
    Category,
    Comment,
    TaskLog,
    Profile,
    Notification,
    GoogleCredentials,
    TaskPriorityOption,
    TaskStatusOption,
    GoogleOAuthState,
)
from .serializers import (
    TaskSerializer,
    TeamSerializer,
    RegisterSerializer,
    CategorySerializer,
    CommentSerializer,
    TaskLogSerializer,
    UserSerializer,
    ProfileSerializer,
    NotificationSerializer,
    TaskPriorityOptionSerializer,
    TaskStatusOptionSerializer,
)
from .permissions import IsTeamManagerOrAssigned
from .utils import send_task_notification
from .google_integration import get_calendar_service


logger = logging.getLogger(__name__)



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]


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
    
    def perform_create(self, serializer):
        task = serializer.save()
        if task.assigned_to and task.assigned_to.email:  
            send_task_notification(task, task.assigned_to.email)

        self._auto_sync_calendar(task)

    def _auto_sync_calendar(self, task):
        """Próbuje od razu utworzyć wydarzenie w kalendarzu Google przypisanego użytkownika."""
        assigned_user = task.assigned_to
        if not assigned_user or not task.due_date:
            return
        service = get_calendar_service(assigned_user)
        if not service:
            return
        start_iso = task.due_date.isoformat()
        end_iso = (task.due_date + timedelta(hours=1)).isoformat()
        body = {
            "summary": task.title,
            "description": task.description or "",
            "start": {"dateTime": start_iso, "timeZone": "Europe/Warsaw"},
            "end": {"dateTime": end_iso, "timeZone": "Europe/Warsaw"},
        }
        try:
            service.events().insert(calendarId="primary", body=body).execute()
            logger.info("Utworzono automatyczne wydarzenie Google Calendar dla zadania %s", task.pk)
        except Exception as exc:  # pragma: no cover - logowanie błędów integracji
            logger.warning("Nie udało się zsynchronizować zadania %s z kalendarzem: %s", task.pk, exc)


    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def sync_calendar(self, request, pk=None):
        task = self.get_object()

        # tylko przypisany użytkownik albo staff/admin
        user = request.user
        if not (user.is_staff or task.assigned_to == user):
            return Response({"detail": "Brak dostępu do tego zadania."}, status=403)

        service = get_calendar_service(user)
        if not service:
            return Response(
                {"detail": "Użytkownik nie ma połączonego konta Google."},
                status=400,
            )

        if not task.due_date:
            return Response(
                {"detail": "Zadanie nie ma ustawionego terminu (due_date)."},
                status=400,
            )

        # zakładam, że due_date to DateTimeField
        start_iso = task.due_date.isoformat()
        # kończymy np. godzinę później
        end_iso = (task.due_date + timedelta(hours=1)).isoformat()

        event_body = {
            "summary": task.title,
            "description": task.description or "",
            "start": {
                "dateTime": start_iso,
                "timeZone": "Europe/Warsaw",  # ewentualnie z settings.TIME_ZONE
            },
            "end": {
                "dateTime": end_iso,
                "timeZone": "Europe/Warsaw",
            },
        }

        try:
            event = service.events().insert(calendarId="primary", body=event_body).execute()
        except Exception as exc:  # pragma: no cover - obsługa błędów API Google
            logger.warning("Błąd synchronizacji zadania %s z kalendarzem: %s", task.pk, exc)
            return Response(
                {"detail": "Wystąpił błąd po stronie Google Calendar."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "detail": "Utworzono wydarzenie w Google Calendar.",
                "event_id": event.get("id"),
                "html_link": event.get("htmlLink"),
            }
        )

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = Comment.objects.all()
        task_id = self.request.query_params.get('task')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        return queryset


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


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

   
    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user).order_by('-created_at')
        is_read = self.request.query_params.get('is_read')
        if is_read in ('true', 'false'):
            qs = qs.filter(is_read=(is_read == 'true'))
        return qs

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread': count})

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'updated': updated})

    
    @action(detail=True, methods=['post'], url_path='mark-as-read')
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()

        return Response({"status": "marked as read"}, status=status.HTTP_200_OK)


class TaskPriorityOptionViewSet(viewsets.ModelViewSet):
    queryset = TaskPriorityOption.objects.all()
    serializer_class = TaskPriorityOptionSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]


class TaskStatusOptionViewSet(viewsets.ModelViewSet):
    queryset = TaskStatusOption.objects.all()
    serializer_class = TaskStatusOptionSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]


class CurrentUserInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, 'profile', None)
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "is_staff": request.user.is_staff,
            "role": profile.role if profile else None,
        })


GOOGLE_OAUTH_CONFIG = {
    "web": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "project_id": "task-manager",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
    }
}


class GoogleOAuthInitView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        flow = Flow.from_client_config(
            GOOGLE_OAUTH_CONFIG,
            scopes=settings.GOOGLE_CALENDAR_SCOPES,
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        GoogleOAuthState.objects.create(user=request.user, state=state)
        return Response({"auth_url": auth_url})


def google_auth_callback(request):
    state_param = request.GET.get("state")
    if not state_param:
        logger.warning("Google OAuth callback without state")
        return redirect("/?google=error")
    try:
        state_obj = GoogleOAuthState.objects.select_related("user").get(state=state_param)
    except GoogleOAuthState.DoesNotExist:
        logger.warning("Google OAuth callback state not found: %s", state_param)
        return redirect("/?google=error")

    flow = Flow.from_client_config(
        GOOGLE_OAUTH_CONFIG,
        scopes=settings.GOOGLE_CALENDAR_SCOPES,
        state=state_param,
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

    try:
        flow.fetch_token(authorization_response=request.build_absolute_uri())
    except Exception as exc:  # pragma: no cover
        logger.warning("Google OAuth fetch_token error: %s", exc)
        state_obj.delete()
        return redirect("/?google=error")

    creds = flow.credentials
    creds_json = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }

    GoogleCredentials.objects.update_or_create(
        user=state_obj.user,
        defaults={"credentials_json": creds_json},
    )
    state_obj.delete()
    return redirect("/")


def app_home(request):
    """Prosty interfejs testowy do wzywania endpointów API."""
    return render(request, "app.html")
