from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification, Brag, Reply
from .serializers import NotificationSerializer,ReplySerializer,BragSerializer, PromiseNotificationSerializer
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from plan.models import Plan
from .serializers import BragSerializer
from users.models import Profile
from django.contrib.contenttypes.models import ContentType
from plan.serializers import PlanSerializer
from django.contrib.auth import get_user_model

from datetime import timedelta
from django.utils import timezone
from promise.models import Promise

User = get_user_model()

class PlanNotificationView(APIView):
    def get(self, request, recipient_username, *args, **kwargs):
        recipient = get_object_or_404(User, username=recipient_username)

        filtered_notifications = Notification.objects.filter(
            recipient=recipient,
            notification_type__in=['plan_deadline', 'daily_achievement'])

        serializer = NotificationSerializer(filtered_notifications, many=True)

        return Response({"message":"계획 알림을 불러왔습니다.", "result":serializer.data}, status=status.HTTP_200_OK)


class PromiseNotificationView(APIView):
    def get(self, request, recipient_username, *args, **kwargs):
        recipient = get_object_or_404(User, username=recipient_username)

        filtered_notifications = Notification.objects.filter(
            recipient=recipient,
            notification_type__in=['vote', 'promise_accept', 'promise_completed']
        )

        # vote인 경우 남은 시간까지 더해서 리턴
        results = []
        
        for notification in filtered_notifications:
            serialized_data = PromiseNotificationSerializer(notification).data

            if notification.notification_type == 'vote' and isinstance(notification.content_object, Promise):
                promise = notification.content_object
                # 약속 생성된 지 24시간을 기준으로 남은 시간 계산
                time_elapsed = timezone.now() - promise.created_at
                remaining_time = timedelta(hours=24) - time_elapsed
                
                # 남은 시간이 양수일 때만 HH:MM 형식으로 추가
                if remaining_time.total_seconds() > 0:
                    hours, remainder = divmod(remaining_time.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    serialized_data['remaining_time'] = f"{hours:02}:{minutes:02}"
                else:
                    serialized_data['remaining_time'] = "투표 시간이 만료되었습니다."

            results.append(serialized_data)

        return Response({"message": "약속 알림을 불러왔습니다.", "result": results}, status=status.HTTP_200_OK)

class FriendNotificationView(APIView):
    def get(self, request, recipient_username, *args, **kwargs):
        recipient = get_object_or_404(User, username=recipient_username)

        filtered_notifications = Notification.objects.filter(
            recipient=recipient,
            notification_type__in=['brag', 'cheering', 'add_friend'])

        serializer = NotificationSerializer(filtered_notifications, many=True)

        return Response({"message":"친구 알림을 불러왔습니다.", "result":serializer.data}, status=status.HTTP_200_OK)

# 떠벌림
class BragView(APIView):
    def post(self, request, username, plan_id):
        user = get_object_or_404(User, username=username)
        plan = get_object_or_404(Plan, id=plan_id)

        serializer = BragSerializer(data=request.data)
        if serializer.is_valid():
            brag = Brag.objects.create(
                plan = plan,
                author=user,
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
                    message=f"{user.nickname}님이 자신의 계획을 떠벌리셨습니다. \n '{brag.memo}'",
                    notification_type='brag',
                    content_type=content_type,
                    object_id=plan.id
                )
                
            return Response({"message":"떠벌림이 성공적으로 전송되었습니다.", "result": {"brag_id": brag.id, "memo": serializer.validated_data.get('memo')}}, status=status.HTTP_200_OK)
        return Response({"message":"떠벌림을 실패했습니다.", "result": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# 답장
class ReplyView(APIView):
    def post(self, request, username, brag_id):
        user = get_object_or_404(User, username=username)
        brag = get_object_or_404(Brag, id=brag_id)

        serializer = ReplySerializer(data=request.data)
        
        if serializer.is_valid():
            reply = Reply.objects.create(
                brag=brag,
                author=user,
                memo=serializer.validated_data.get('memo')
            )

            # Reply 객체 직렬화하여 반환
            #reply_serializer = ReplySerializer(reply)

            content_type = ContentType.objects.get_for_model(reply)
            Notification.objects.create(
                recipient=brag.author,
                message=f"{user.nickname}님께서 {brag.author.nickname}님을 응원하셨어요. \n '{reply.memo}'",
                notification_type='cheering',
                content_type=content_type,
                object_id=reply.id
            )
            
            return Response({"message": "답변이 성공적으로 등록되었습니다.", "result": serializer.data}, status=status.HTTP_201_CREATED)
        
        return Response({"message": "답변 등록에 실패했습니다.", "result": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# 팔로우 백
class NotificationActionView(APIView):
    def post(self, request, notification_id, format=None):
        try:
            notification = Notification.objects.get(id=notification_id, recipient=request.user)
        except Notification.DoesNotExist:
            return Response({'error':'알림을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        if notification.action_type == 'follow':
            target_user = Profile.objects.get(username=notification.message.split()[0]) # 메세지에서 대상 유저 추출

            if not request.user.friends.filter(username=target_user.username).exists():
                request.user.friends.add(target_user)
                return Response({"message":f"{target_user.nickname}을 친구 추가 했습니다."})

        return Response({'error':'잘못된 요청입니다.'}, status=status.HTTP_400_BAD_REQUEST)