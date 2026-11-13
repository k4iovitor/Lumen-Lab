"""
Mapeamento de rotas e endpoints do módulo de progresso e assistência socrática do LumenLab.

Define as rotas acessíveis sob o prefixo `/api/`:
  - `state/`: Consulta o estado global da aplicação e do estudante.
  - `navigation/switch/`: Registra telemetria de mudança de tela.
  - `assistant/chat/`: Canal de conversação pedagógica com a assistente Lumia.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Recuperação do estado geral e indicadores de progresso
    path('state/', views.get_state, name='app_state'),

    # Registro de telemetria e navegação entre seções
    path('navigation/switch/', views.switch_navigation, name='switch_navigation'),

    # Conversação reflexiva e socrática com o agente Lumia
    path('assistant/chat/', views.assistant_chat, name='assistant_chat'),
]
