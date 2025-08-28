from django.urls import path
from . import views
from .views import forgot_password, reset_password

urlpatterns = [
    path("", views.task_list_create, name="task_list_create"),
    path("<int:pk>/", views.task_detail, name="task_detail"),
    path("forgot-password/", forgot_password, name="forgot-password"),
    path("reset-password/", reset_password, name="reset-password"),
]
