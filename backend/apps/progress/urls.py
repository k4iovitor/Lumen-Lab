"""
Mapeamento de rotas e endpoints do módulo de progresso e assistência socrática do LumenLab em português brasileiro.

Define as rotas de telemetria, estado geral e diálogo socrático.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Rotas em Português Brasileiro
    path('estado/', views.obter_estado_aplicacao, name='estado_aplicacao'),
    path('navegacao/alternar/', views.alternar_secao_navegacao, name='alternar_secao_navegacao'),
    path('assistente/dialogo/', views.dialogo_assistente_socratica, name='dialogo_assistente_socratica'),

    # Rotas de compatibilidade retroativa
    path('state/', views.obter_estado_aplicacao, name='app_state'),
    path('navigation/switch/', views.alternar_secao_navegacao, name='switch_navigation'),
    path('assistant/chat/', views.dialogo_assistente_socratica, name='assistant_chat'),
]
