from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TeamViewSet

router = DefaultRouter()
router.register(r'teams', TeamViewSet)
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    path('', include(router.urls))
]