from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification, Brag
from .serializers import NotificationSerializer
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from plan.models import Plan
from .serializers import BragSerializer
from users.models import Profile
from django.contrib.contenttypes.models import ContentType
from plan.serializers import PlanSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class PlanNotificationView(APIView):
    def get(self, request, *args, **kwargs):
        filtered_notifications = Notification.objects.filter(
            notification_type__in=['plan_deadline', 'daily_achievement'])

        serializer = NotificationSerializer(filtered_notifications, many=True)

        return Response({"message":"계획 알림을 불러왔습니다.", "result":serializer.data}, status=status.HTTP_200_OK)

class PromiseNotificationView(APIView):
    def get(self, request, *args, **kwargs):
        filtered_notifications = Notification.objects.filter(
            notification_type__in=['vote', 'promise_accept'])

        serializer = NotificationSerializer(filtered_notifications, many=True)

        return Response({"message":"약속 알림을 불러왔습니다.", "result":serializer.data}, status=status.HTTP_200_OK)

class FriendNotificationView(APIView):
    def get(self, request, *args, **kwargs):
        filtered_notifications = Notification.objects.filter(
            notification_type__in=['brag', 'cheering', 'add_friend'])

        serializer = NotificationSerializer(filtered_notifications, many=True)

        return Response({"message":"친구 알림을 불러왔습니다.", "result":serializer.data}, status=status.HTTP_200_OK)


class BragView(APIView):
    def post(self, request,plan_id):
        plan = get_object_or_404(Plan, id=plan_id)
        serializer = BragSerializer(data=request.data)
        if serializer.is_valid():
            brag = Brag.objects.create(
                plan = plan,
                author=request.user,
                memo=serializer.validated_data.get('memo') 
            )
        
            recipient_ids = request.data.get('recipient', [])
            recipients = User.objects.filter(id__in=recipient_ids)
            
            brag.recipients.set(recipients)

            # Plan 직렬화
            plan_serializer = PlanSerializer(plan)

            content_type = ContentType.objects.get_for_model(plan)
            for recipient in recipients:
                Notification.objects.create(
                    recipient=recipient,
                    message=f"{request.user.nickname}님이 '{brag.memo}'라고 떠벌렸습니다!",
                    notification_type='brag',
                    content_type=content_type,
                    object_id=plan.id
                )
                
            return Response({"message":"떠벌림이 성공적으로 전송되었습니다.", "result": serializer.data}, status=status.HTTP_200_OK)
        return Response({"message":"떠벌림을 실패했습니다.", "result": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)