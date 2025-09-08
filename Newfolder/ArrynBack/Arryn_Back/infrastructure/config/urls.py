from django.urls import path
from ..api.views import getUsers, createUser, userDetail, ArchivosJsonView

urlpatterns = [
    path('user/', getUsers, name='get_user'),
    path('user/create', createUser, name='create_user'),
    path('user/<int:pk>/', userDetail, name='user_detail'),
    path("archivos/", ArchivosJsonView.as_view(), name="archivos"),
]