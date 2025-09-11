from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Team, Category, Comment, TaskLog


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class TeamSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'members']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class TaskSerializer(serializers.ModelSerializer):
    assigned_to = UserSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source='assigned_to'
    )

    team = TeamSerializer(read_only=True)
    team_id = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(), write_only=True, source='team'
    )
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True, source='category'
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
        user = self.context['request'].user

        for field in ['title', 'description', 'status']:
            if field in validated_data:
                old_value = getattr(instance, field)
                new_value = validated_data[field]
                if old_value != new_value:
                    TaskLog.objects.create(
                        task=instance,
                        user=user,
                        change_type=field,
                        old_value=old_value,
                        new_value=new_value,)

        if validated_data.get("status") == "done":
            validated_data["completed"] = True
        return super().update(instance, validated_data)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'assigned_to', 'assigned_to_id', 'team',
                   'team_id', 'due_date', 'completed', 'status', 'category', 'category_id', 'priority']


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
    
class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'task', 'author', 'content', 'created_at']


class TaskLogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = TaskLog
        fields = ['id', 'task', 'user', 'change_type', 'old_value', 'new_value', 'timestamp']