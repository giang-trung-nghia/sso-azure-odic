from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_start, name="account_login"),
    path("me/", views.me, name="account_me"),
    path("claims/", views.claims_inspect, name="account_claims"),
]
