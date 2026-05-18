from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_start, name="account_login"),
    path("me/", views.me, name="account_me"),
    path("api/me/", views.api_me, name="accounts_api_me"),
    path("claims/", views.claims_inspect, name="account_claims"),
]
