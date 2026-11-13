"""
Mapeamento de rotas e endpoints do módulo de higiene digital do LumenLab.

Define as rotas de listagem, criação, alternância de status e remoção de hábitos.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Coleção principal de hábitos (GET para listar, POST para criar)
    path('habits/', views.habits_collection, name='habits_collection'),

    # Criação explícita de hábitos
    path('habits/create/', views.create_habit, name='create_habit'),

    # Alternância de status de conclusão
    path('habits/toggle/', views.toggle_habit, name='toggle_habit'),

    # Remoção de hábitos da agenda
    path('habits/delete/', views.delete_habit, name='delete_habit'),

    # Metas de tempo de tela, proporção jogos/redes e reserva para afazeres
    path('screen-time/', views.screen_time_goal_view, name='screen_time_goal'),
]
