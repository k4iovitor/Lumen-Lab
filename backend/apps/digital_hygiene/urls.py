"""
Mapeamento de rotas e endpoints do módulo de higiene digital do LumenLab em português brasileiro.

Define as rotas de listagem, criação, alternância de status e remoção de hábitos,
além da gestão das metas de tempo de tela e desconexão consciente.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Rotas em Português Brasileiro
    path('habitos/', views.colecao_habitos, name='colecao_habitos'),
    path('habitos/criar/', views.criar_novo_habito, name='criar_novo_habito'),
    path('habitos/alternar/', views.alternar_conclusao_habito, name='alternar_conclusao_habito'),
    path('habitos/excluir/', views.excluir_habito_agenda, name='excluir_habito_agenda'),
    path('tempo-tela/', views.visualizacao_meta_tempo_tela, name='meta_tempo_tela'),

    # Rotas de compatibilidade retroativa
    path('habits/', views.colecao_habitos, name='habits_collection'),
    path('habits/create/', views.criar_novo_habito, name='create_habit'),
    path('habits/toggle/', views.alternar_conclusao_habito, name='toggle_habit'),
    path('habits/delete/', views.excluir_habito_agenda, name='delete_habit'),
    path('screen-time/', views.visualizacao_meta_tempo_tela, name='screen_time_goal'),
]
