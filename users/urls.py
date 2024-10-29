from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('friends/', FriendsView.as_view(), name='friends'),
    path('profile/', ProfileView.as_view(), name='profile'),
]