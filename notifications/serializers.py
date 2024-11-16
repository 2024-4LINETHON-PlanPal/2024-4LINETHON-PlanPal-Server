from rest_framework import serializers
from .models import Notification, Brag, Reply
from users.serializers import ProfileSerializer
from plan.serializers import PlanSerializer
from users.models import Profile

class NotificationSerializer(serializers.ModelSerializer):
    plan_title = serializers.SerializerMethodField()
    friend_nickname = serializers.SerializerMethodField()
    brag_id = serializers.SerializerMethodField()
    friend_username = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'message', 'notification_type', 'plan_title', 'friend_nickname', 'friend_username','brag_id']

    def get_plan_title(self, obj):
        if obj.notification_type in ['add_friend', 'brag']:
            try:
                brag = Brag.objects.get(id=obj.object_id)
                return brag.plan.title 
            except Brag.DoesNotExist:
                return None
        return None

    def get_friend_username(self, obj):
        if obj.notification_type in ['add_friend', 'brag']:
            try:
                user = Profile.objects.get(id=obj.author.id)
                return user.username
            except Profile.DoesNotExist:
                return None
        return None

    def get_friend_nickname(self, obj):
        if obj.notification_type in ['add_friend', 'brag']:
            try:
                brag = Brag.objects.get(id=obj.author.id)
                return brag.author.nickname
            except Brag.DoesNotExist:
                return None
        return None

    def get_brag_id(self, obj):
        if obj.notification_type in ['add_friend', 'brag']:
            try:
                brag = Brag.objects.get(id=obj.object_id)
                return brag.id
            except Brag.DoesNotExist:
                return None
        return None

class BragSerializer(serializers.ModelSerializer):
    author = ProfileSerializer(many=True, read_only=True)
    recipient = ProfileSerializer(many=True, read_only=True)
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Brag
        fields = ['id', 'author', 'plan', 'recipient', 'memo']
        read_only = ['author', 'created_at']

class ReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Reply
        fields = ['id', 'brag', 'author', 'memo', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']

class PromiseNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'message', 'notification_type', 'object_id']
