"""
Mapeamento de rotas e endpoints do módulo de autenticação Google OAuth do LumenLab em português brasileiro.

Define as rotas acessíveis sob o prefixo `/api/auth/` e `/api/autenticacao/`:
  - `google/`: Validação de tokens emitidos pelo Google Identity Services.
  - `cadastro/` ou `register/`: Cadastro inicial de novos estudantes com Gmail e data de nascimento.
  - `perfil/` ou `profile/`: Consulta aos dados cadastrais do estudante autenticado.
  - `configuracao/` ou `config/`: Recuperação do Client ID público do Google OAuth.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Rotas em Português Brasileiro
    path('google/', views.google_auth, name='autenticacao_google'),
    path('cadastro/', views.register, name='cadastro_estudante'),
    path('perfil/', views.get_profile, name='perfil_estudante'),
    path('configuracao/', views.get_auth_config, name='configuracao_autenticacao'),

    # Rotas de compatibilidade retroativa
    path('register/', views.register, name='register'),
    path('profile/', views.get_profile, name='get_profile'),
    path('config/', views.get_auth_config, name='auth_config'),
]
