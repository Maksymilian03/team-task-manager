from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Team


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class TeamSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'members']


class TaskSerializer(serializers.ModelSerializer):
    assigned_to = UserSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source='assigned_to'
    )

    team = TeamSerializer(read_only=True)
    team_id = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(), write_only=True, source='team'
    )

    def validate_status(self, value):
        user = self.context['request'].user
        if value == 'done' and not user.is_staff:
            raise serializers.ValidationError("Tylko administrator może oznaczyć zadanie jako 'done'.")
        return value
    
    def create(self, validated_data):
        if validated_data.get("status") == "done":
            validated_data["completed"] = True
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if validated_data.get("status") == "done":
            validated_data["completed"] = True
        return super().update(instance, validated_data)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'assigned_to', 'assigned_to_id', 'team', 'team_id', 'due_date', 'completed', 'status']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        
        return user