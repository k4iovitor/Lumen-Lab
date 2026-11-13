"""
Configuração mestre de roteamento de URLs do LumenLab em português brasileiro.

A lista `urlpatterns` encaminha as requisições HTTP para as respectivas
aplicações do projeto:
  - `admin/`: Painel administrativo nativo do Django.
  - `api/progresso/` ou `api/`: Rotas de progresso pedagógico e telemetria.
  - `api/autenticacao/` ou `api/auth/`: Rotas de autenticação Google OAuth (Gmail) e cadastro de estudantes.
  - `api/higiene-digital/` ou `api/digital-hygiene/`: Rotas de hábitos de higiene digital e rotina consciente.
  - `api/chatbot/`: Rotas do chatbot Lumia — mensagens SSE e histórico de sessão.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Painel Administrativo do Django
    path('admin/', admin.site.urls),

    # Endpoints de progresso, telemetria de navegação e assistente Lumia
    path('api/', include('apps.progress.urls')),
    path('api/progresso/', include('apps.progress.urls')),

    # Endpoints de autenticação via Google OAuth, cadastro e perfil de estudante
    path('api/auth/', include('apps.authentication.urls')),
    path('api/autenticacao/', include('apps.authentication.urls')),

    # Endpoints de higiene digital e hábitos de desconexão consciente
    path('api/digital-hygiene/', include('apps.digital_hygiene.urls')),
    path('api/higiene-digital/', include('apps.digital_hygiene.urls')),

    # Endpoints do chatbot Lumia — mensagens SSE e histórico de sessão
    path('api/chatbot/', include('apps.chatbot.urls')),
]
