from rest_framework import routers
from .views import *
from django.urls import path

router = routers.SimpleRouter()

urlpatterns = [ 
    path('plan/', PlanNotificationView.as_view(), name='plan_notification'),
    path('promise/', PromiseNotificationView.as_view() , name='promise_notification'),
    path('friend/', FriendNotificationView.as_view() , name='notification_friend'),
    path('brag/<int:plan_id>/', BragView.as_view(), name='brag'),
    path('brags/<int:brag_id>/reply/', ReplyView.as_view(), name='reply-create'),
    ]