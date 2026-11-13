"""
Roteamento de URLs do chatbot Lumia.
"""
from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Endpoint principal: envia mensagem e recebe streaming SSE
    path('message/', views.message_view, name='message'),

    # Histórico de uma sessão específica
    path('session/<str:session_id>/', views.session_history_view, name='session_history'),

    # Lista de sessões do usuário
    path('sessions/', views.list_sessions_view, name='list_sessions'),
]
