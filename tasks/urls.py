from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskViewSet,
    TeamViewSet,
    RegisterView,
    CategoryViewSet,
    CommentViewSet,
    TaskLogViewSet,
    UserViewSet,
    ProfileViewSet,
    NotificationViewSet,
    TaskPriorityOptionViewSet,
    TaskStatusOptionViewSet,
    CurrentUserInfoView,
    GoogleOAuthInitView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView



router = DefaultRouter()
router.register(r'teams', TeamViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'logs', TaskLogViewSet)
router.register(r'users', UserViewSet)
router.register(r'profiles', ProfileViewSet)
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'priorities', TaskPriorityOptionViewSet, basename='priority')
router.register(r'statuses', TaskStatusOptionViewSet, basename='status')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('google/auth-url/', GoogleOAuthInitView.as_view(), name='google_auth_url'),
    path('me/', CurrentUserInfoView.as_view(), name='current-user-info'),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
