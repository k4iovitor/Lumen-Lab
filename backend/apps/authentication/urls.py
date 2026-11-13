"""
Mapeamento de rotas e endpoints do módulo de autenticação Google OAuth do LumenLab.

Define as rotas acessíveis sob o prefixo `/api/auth/`:
  - `google/`: Validação de tokens emitidos pelo Google Identity Services.
  - `register/`: Cadastro inicial de novos estudantes com Gmail e data de nascimento.
  - `profile/`: Consulta aos dados cadastrais do estudante autenticado.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Validação de credencial do Google Identity Services (login/registro)
    path('google/', views.google_auth, name='google_auth'),

    # Cadastro complementar de novo estudante
    path('register/', views.register, name='register'),

    # Consulta de perfil do usuário logado via JWT
    path('profile/', views.get_profile, name='get_profile'),

    # Configurações públicas de autenticação para o frontend (Google Client ID do .env)
    path('config/', views.get_auth_config, name='auth_config'),
]
