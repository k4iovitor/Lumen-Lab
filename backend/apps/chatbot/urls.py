"""
Roteamento de URLs do chatbot Lumia em português brasileiro.

Configura as rotas para envio de mensagens com streaming SSE e histórico relacional.
"""
from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Rota principal para envio de mensagem e streaming Server-Sent Events (SSE)
    path('mensagem/', views.visualizacao_mensagem, name='mensagem'),

    # Recuperação do histórico de uma sessão específica
    path('sessao/<str:id_sessao>/', views.visualizacao_historico_sessao, name='historico_sessao'),

    # Listagem de todas as sessões do estudante
    path('sessoes/', views.visualizacao_listar_sessoes, name='listar_sessoes'),

    # Rotas espelho para retrocompatibilidade
    path('message/', views.visualizacao_mensagem, name='message_legado'),
    path('session/<str:id_sessao>/', views.visualizacao_historico_sessao, name='session_history_legado'),
    path('sessions/', views.visualizacao_listar_sessoes, name='sessions_legado'),
]
