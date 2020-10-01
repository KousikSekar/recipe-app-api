from rest_framework.authtoken.views import ObtainAuthToken
from . import serializers
from rest_framework import generics, authentication, permissions
from django.contrib.auth import get_user_model
from rest_framework.settings import api_settings
# Create your views here.


class CreateUserView(generics.CreateAPIView, generics.ListAPIView):
    """Create Users"""
    serializer_class = serializers.UserSerializer
    queryset = get_user_model().objects.all()

class AuhtenticateUserView(ObtainAuthToken):
    """Authenticate users"""
    serializer_class = serializers.AuthtokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES # The default renderer classes displays the token in view

class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.UserSerializer
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

