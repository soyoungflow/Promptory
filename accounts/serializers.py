from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

from .auth_messages import friendly_auth_detail

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        'no_active_account': friendly_auth_detail('no_active_account', code='no_active_account'),
    }


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except TokenError as exc:
            detail = getattr(exc, 'detail', None) or str(exc)
            code = getattr(exc, 'default_code', None)
            raise serializers.ValidationError({
                'detail': friendly_auth_detail(detail, code=code),
            }) from exc


class RegisterSerializer(serializers.ModelSerializer):
    """
    회원가입 Serializer.
    - 입력: email, username, password, password2
    - 출력: id, email, username
    - 검증: 이메일 중복, 비밀번호 일치, Django 비밀번호 정책
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, label='비밀번호 확인')

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password', 'password2')
        read_only_fields = ('id',)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': '비밀번호가 일치하지 않습니다.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        # create_user → 비밀번호 해시 저장 (set_password 내부 호출)
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """내 프로필 조회 / 수정"""
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'bio', 'avatar', 'date_joined')
        read_only_fields = ('id', 'email', 'date_joined')
