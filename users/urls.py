from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('friends/<str:my_username>/', FriendsView.as_view(), name = 'friend-list'),
    path('friends/<str:my_username>/<str:target_username>/', FriendsView.as_view(), name='friends'),
    path('profile/<str:username>/', ProfileView.as_view(), name='profile'),
    path('username-check/', UsernameCheckView.as_view(), name='username-check'),
]