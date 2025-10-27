from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/new/', views.new_game, name='new_game'),
    path('api/hit/', views.hit, name='hit'),
    path('api/stand/', views.stand, name='stand'),
    path('api/bet/', views.bet, name='bet'),
    path('api/double/', views.double, name='double'),
    path('api/split/', views.split, name='split'),
    path('api/reset/', views.reset_game, name='reset_game'),
]