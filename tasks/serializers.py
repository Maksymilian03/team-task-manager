from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Team, Category, Comment, TaskLog, Profile
from taggit.serializers import TagListSerializerField, TaggitSerializer


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role')
    
    class Meta:
        model = User
        fields = ['id', 'username', 'role']


class TeamSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all()        
    )

    class Meta:
        model = Team
        fields = ['id', 'name', 'members']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class TaskSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField()
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
                   'team_id', 'due_date', 'completed', 'status', 'category', 'category_id', 'priority', 'tags']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=Profile.ROLE_CHOICES, write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'role']

    def create(self, validated_data):
        role = validated_data.pop('role')
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )

        Profile.objects.create(user=user, role=role)
        
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


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)


    class Meta:
        model = Profile
        fields = ['id', 'user', 'role', 'team']