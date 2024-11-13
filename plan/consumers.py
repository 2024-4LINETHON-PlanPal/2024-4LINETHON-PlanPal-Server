import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from django.conf import settings

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f"user_{self.user.id}"
        
        # 사용자의 시간대 설정
        user_timezone = getattr(self.user, 'timezone', settings.TIME_ZONE)
        timezone.activate(user_timezone)

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()

        # 연결 성공 메시지 전송
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Successfully connected to the notification channel.'
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        timezone.deactivate()

    async def send_notification(self, event):
        message = event['message']
        notification_type = event.get('notification_type', 'general')
        
        # 현재 시간을 사용자의 시간대로 변환
        current_time = timezone.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")

        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': message,
            'notification_type': notification_type,
            'timestamp': formatted_time
        }))

    async def receive(self, text_data):
        
        try:
            data = json.loads(text_data)
            await self.send(text_data=json.dumps({
                'type': 'message_received',
                'message': 'Message received successfully.'
            }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format.'
            }))