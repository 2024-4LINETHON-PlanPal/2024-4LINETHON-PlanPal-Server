from rest_framework import serializers
from .models import Plan, Category
from users.models import Profile
from django.shortcuts import get_object_or_404

from promise.serializers import ProfileSerializer, PromiseSerializer

import pytz
from django.utils import timezone

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'color', 'is_public']

class PlanSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    participant = ProfileSerializer(many=True, read_only=True)
    is_completed = serializers.BooleanField(required=False)
    promise_id = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Plan
        fields = ['id', 'title', 'category', 'start', 'end', 'participant', 'memo', 'is_completed', 'promise_id']
        read_only_fields = ['author']