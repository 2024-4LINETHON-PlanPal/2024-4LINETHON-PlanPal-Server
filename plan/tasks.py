from celery import shared_task
from django.utils import timezone
from .models import Plan
from notifications.models import Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model

User = get_user_model()

@shared_task
def check_plan_deadlines():
    now = timezone.now().astimezone(timezone.get_current_timezone())
    plans = Plan.objects.filter(is_completed=False)
    
    for plan in plans:
        plan_end = plan.end.astimezone(timezone.get_current_timezone())
        deadline = plan_end - now

        message = f"{plan.title} 마감시간까지 1시간 남았습니다! 잊지 말고 계획을 실행해주세요!"

        if deadline <= timezone.timedelta(hours=1) and deadline > timezone.timedelta(0):
            Notification.objects.create(
                recipient=plan.author,
                message=message,
                notification_type='plan_deadline'
        )

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{plan.author.id}", 
                {
                    "type": "send_notification",
                    "message": message
                }
            )

@shared_task(name='tasks.send_daily_achievement')
def send_daily_achievement():
    yesterday = timezone.now().date() - timezone.timedelta(days=1)
    users = User.objects.all()

    for user in users:
        total_plans = Plan.objects.filter(author=user, start__date=yesterday).count()
        completed_plans = Plan.objects.filter(author=user, start__date=yesterday, is_completed=True).count()

        message = f"어제는 {total_plans}개의 계획 중에서 {completed_plans}개의 계획을 달성하셨습니다! \n {yesterday.year}년 {yesterday.month}월 {yesterday.day}일의 {user.nickname}님은 성실하셨네요!"

        Notification.objects.create(
            recipient=user,
            message=message,
            notification_type='daily_achievement'
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",
            {
                'type': 'send_notification',
                'message': message,
            }
        )