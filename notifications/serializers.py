from rest_framework import serializers
from .models import Notification, Brag, Reply
from users.serializers import ProfileSerializer
from plan.serializers import PlanSerializer

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'message', 'created_at', 'content_type', 'object_id', 'content_object', 'notification_type']

        def to_representation(self, instance):
            representation = super().to_representation(instance)

            if instance.content_object:
                representation['related_object'] = str(instance.content_object)
        
            return representation

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