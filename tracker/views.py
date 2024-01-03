from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import generics, status, mixins
from tracker.models import *
from tracker.serializers import UserSerializer, AlertSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound

# Create your views here.


class HelloWorld(GenericAPIView):
    def get(self, request):
        return Response({"message": "Hello World!"})


class CreateUserView(generics.GenericAPIView, mixins.CreateModelMixin):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get("email", None)

        if email is None:
            return Response(
                {"message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {"message": "User already exists"}, status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)


class LoginAPIView(GenericAPIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email", None)
        password = request.data.get("password", None)
        if email is None or password is None:
            return Response(
                {"message": "Email and Password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"status": "User not registered"}, status=status.HTTP_401_UNAUTHORIZED
            )

        access = user.access()
        refresh = user.refresh()

        return Response(
            {"access": access, "refresh": refresh, "email": email},
            status=status.HTTP_200_OK,
        )


class CreateAlertView(GenericAPIView, mixins.CreateModelMixin):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class ListAlertView(GenericAPIView, mixins.ListModelMixin):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        status = self.request.query_params.get("status", None)
        coins = CoinAlert.objects.filter(user=self.request.user)
        if status is not None:
            coins = coins.filter(status=status)
        return coins

    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class DeleteAlertView(GenericAPIView, mixins.DestroyModelMixin):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        uuid = self.kwargs.get("uuid", None)
        try:
            return CoinAlert.objects.get(external_id=uuid)
        except CoinAlert.DoesNotExist:
            raise NotFound({"message": "Alert not found"})
        
    def delete(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
