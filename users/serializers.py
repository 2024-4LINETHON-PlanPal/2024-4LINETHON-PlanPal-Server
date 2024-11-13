from .models import Profile
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404

from plan.models import Category

# 회원가입
class Register(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators = [validate_password]
    )

    nickname = serializers.CharField(required=True)
    
    class Meta:
        model = Profile
        fields = ('username', 'password','nickname')

    # 닉네임 중복 검사
    def validate_nickname(self, value):
        if Profile.objects.filter(nickname=value).exists():
            raise serializers.ValidationError("이미 존재하는 닉네임입니다.")
        return value

    def create(self, validated_data):
        user = Profile.objects.create(
            username=validated_data['username'],
            nickname=validated_data['nickname']  
        )
        user.set_password(validated_data['password'])
        user.save()
        
        # 약속 카테고리 생성
        Category.objects.create(
            author=user,
            title="약속",
            color="#FF6A3B",
            is_public=True
        )

        return user

# 로그인
class Login(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

# 프로필 정보 확인
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('nickname', 'image', 'intro')

    # 닉네임 중복 검사
    def validate_nickname(self, value):
        request_user = self.instance
        
        # 다른 사용자의 닉네임과 중복되는지 확인
        if Profile.objects.filter(nickname=value).exclude(id=request_user.id).exists():
            raise serializers.ValidationError("이미 존재하는 닉네임입니다.")
        
        return value
    
    def update(self, instance, validated_data):
        instance.nickname = validated_data.get('nickname', instance.nickname)
        instance.image = validated_data.get('image', instance.image)
        instance.intro = validated_data.get('intro', instance.intro)
        instance.save()
        return instance
    

# 'id', 'username', 'nickname' 반환을 위한 시리얼라이저
class FriendsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'username', 'nickname']