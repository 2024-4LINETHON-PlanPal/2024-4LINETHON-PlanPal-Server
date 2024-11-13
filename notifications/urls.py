from rest_framework import routers
from .views import *
from django.urls import path

router = routers.SimpleRouter()

urlpatterns = [ 
    path('plan/<str:recipient_username>/', PlanNotificationView.as_view(), name='plan_notification'),
    path('promise/<str:recipient_username>/', PromiseNotificationView.as_view() , name='promise_notification'),
    path('friend/<str:recipient_username>/', FriendNotificationView.as_view() , name='notification_friend'),
    path('brag/<str:username>/<int:plan_id>/', BragView.as_view(), name='brag'),
    path('reply/<str:username>/<int:brag_id>/', ReplyView.as_view(), name='reply-create'),
    ]