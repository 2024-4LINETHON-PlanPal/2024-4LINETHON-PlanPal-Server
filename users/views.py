from django.shortcuts import render
from .models import Profile
from rest_framework import generics, status
from .serializers import *
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from notifications.models import Notification
from django.contrib.auth import get_user_model
from rest_framework.views import APIView

from .serializers import FriendsSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = Profile.objects.all()
    serializer_class = Register

class UsernameCheckView(APIView):
    def get(self, request, *args, **kwargs):
        username = request.query_params.get('username', None)
        
        if not username:
            return Response({"message": "아이디(username)를 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 아이디 중복 여부 확인
        if Profile.objects.filter(username=username).exists():
            return Response({"message": "이미 존재하는 아이디입니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "사용 가능한 아이디입니다."}, status=status.HTTP_200_OK)

class LoginView(generics.GenericAPIView):
    serializer_class = Login

    def post(self, request):
        username=request.data.get("username")
        password=request.data.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            Login(request, user)
            return Response({"message":"로그인 성공"}, status=status.HTTP_200_OK)
        else:
            return Response({"message":"사용자 이름 또는 비밀번호가 맞지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    lookup_field = 'username'

    def get_object(self):
        username = self.kwargs.get('username')
        return get_object_or_404(Profile, username=username)

class FriendsView(APIView):
    def post(self, request, my_username, target_username, format=None):
        try:
            user = Profile.objects.get(username=my_username)
        except ObjectDoesNotExist:
            return Response({'error': f"'{my_username}'을(를) 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        try:
            target_user = Profile.objects.get(username=target_username)
        except ObjectDoesNotExist:
            return Response({'error': "해당 유저는 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)
        
        if my_username == target_username:
            return Response({'error': "자기 자신을 친구로 추가할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        if user.friends.filter(username=target_user.username).exists():
            return Response({'message': "이미 친구입니다."}, status=status.HTTP_200_OK)

        user.friends.add(target_user)

        Notification.objects.create(
            recipient=target_user,
            message=f"{user.username}님이 {target_user.username}님을 친구 추가 하셨어요. \n {target_user}님을 친구 추가 하고 싶으시다면 클릭해주세요." ,
            notification_type="add_friend",
            action_type='follow'
        )

        return Response({'message': f"{target_user.username}님을 친구 추가했습니다."}, status=status.HTTP_201_CREATED)
    
    def delete(self, request, my_username, target_username, format=None):
        try:
            user = Profile.objects.get(username=my_username)
        except ObjectDoesNotExist:
            return Response({'error': f"프로필 '{my_username}'을(를) 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            target_user = Profile.objects.get(username=target_username)
        except ObjectDoesNotExist:
            return Response({'error': f"프로필 '{target_username}'을(를) 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        # 친구 목록에 target_user가 있는지 확인하고 없으면 400 처리
        if target_user not in user.friends.all():
            return Response({'error': f"{target_user.username}님은 친구 목록에 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
    
        user.friends.remove(target_user)
        serializer = FriendsSerializer(user.friends, many=True)
        return Response({'message': f"{target_user.username}님을 친구 목록에서 삭제했습니다.", "result": serializer.data}, status=status.HTTP_200_OK)

    def get(self, request, my_username, format=None):
        # GET 메서드: 친구 목록 조회 로직
        try:
            user = Profile.objects.get(username=my_username)
        except ObjectDoesNotExist:
            return Response({'error': f"프로필 '{my_username}'을(를) 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        # 친구 목록 직렬화
        serializer = FriendsSerializer(user.friends.all(), many=True)
        return Response({'message': '친구 리스트를 불러왔습니다.', 'result':serializer.data}, status=status.HTTP_200_OK)