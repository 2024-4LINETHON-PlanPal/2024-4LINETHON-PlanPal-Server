from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import Profile
from plan.models import Plan

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('plan_deadline', 'Plan_deadline'),
        ('daily_achievement', 'Daily_achievement'),
        ('brag', 'Barg'),
        ('cheering', 'Cheering'),
        ('add_friend', 'Add_friend'),
        ('vote', 'Vote'),
        ('promise_accept', 'Promise_accept')
    )
    recipient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True) # 알림이 어떤 타입의 객체와 관련이 있는지
    object_id = models.PositiveIntegerField(null=True, blank=True) # 관련된 객체의 ID를 저장하는 필드
    content_object = GenericForeignKey('content_type', 'object_id') # content_type과 object_id를 통해 실제 객체에 접근
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default="plan")

    class Meta:
        ordering = ['-created_at']

class Brag(models.Model):
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='brags')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='brags')
    memo = models.TextField()
    recipients = models.ManyToManyField(Profile, related_name='received_brags') 
    created_at = models.DateTimeField(auto_now_add=True)