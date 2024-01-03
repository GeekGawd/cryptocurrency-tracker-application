from django.urls import path
from . import views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


urlpatterns = [
    path('', views.HelloWorld.as_view(), name='home'),

    path('signup/', views.CreateUserView.as_view(), name='register'),

    path('login/', views.LoginAPIView.as_view(), name='login'),

    path('alerts/create/', views.CreateAlertView.as_view(), name='create-alert'),

    path('alerts/list/', views.ListAlertView.as_view(), name="list-alert"),

    path('alerts/delete/<uuid:uuid>/', views.DeleteAlertView.as_view(), name='delete-alert'),

    # path('alerts/delete/<uuid:uuid>/', views.DeleteAlertView.as_view(), name='delete_alert'),

    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "schema/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="schema-docs",
    ),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]