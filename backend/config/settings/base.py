"""
Configurações base do ecossistema backend LumenLab.

Define as variáveis fundamentais compartilhadas entre os ambientes de
desenvolvimento e produção, incluindo aplicações instaladas, middlewares,
banco de dados SQLite, CORS para comunicação com o frontend React e
parâmetros de integração com a API Google OAuth.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Diretório raiz do projeto backend (onde se encontra o manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Carrega variáveis de ambiente tanto da raiz do projeto quanto da pasta backend
load_dotenv(BASE_DIR.parent / '.env')
load_dotenv(BASE_DIR / '.env')

# Chave secreta de assinatura criptográfica (substituída via variável de ambiente em produção)
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-lumenlab-dev-key-change-in-prod')

# Modo de depuração ativo por padrão em desenvolvimento
DEBUG = True

# Hosts permitidos a enviar requisições para a aplicação
ALLOWED_HOSTS = ['*']

# ---------------------------------------------------------------------------
# Aplicações Instaladas
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Módulos essenciais do Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Bibliotecas de terceiros
    'rest_framework',
    'corsheaders',

    # Aplicações pedagógicas e operacionais do LumenLab
    'apps.progress',         # Estado, navegação e assistente socrática Lumia
    'apps.cybersecurity',    # Módulo de cibersegurança e simulação de phishing
    'apps.digital_hygiene',  # Módulo de hábitos e controle de tempo de tela
    'apps.ai_challenges',    # Módulo de desafios conceituais de IA
    'apps.authentication',   # Autenticação Google OAuth (Gmail) e perfis de estudantes
    'apps.chatbot',          # Chatbot Lumia — sessões e mensagens de chat
]

# ---------------------------------------------------------------------------
# Middlewares de Requisição / Resposta
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',                     # Cabeçalhos CORS para o frontend React
    'django.middleware.security.SecurityMiddleware',             # Proteções de segurança de transporte
    'django.contrib.sessions.middleware.SessionMiddleware',       # Gerenciamento de sessões
    'django.middleware.common.CommonMiddleware',                 # Normalização de URLs e tratamento comum
    'django.middleware.csrf.CsrfViewMiddleware',                 # Proteção contra requisições forjadas (CSRF)
    'django.contrib.auth.middleware.AuthenticationMiddleware',   # Associação de usuário à requisição
    'django.contrib.messages.middleware.MessageMiddleware',       # Mensagens flash para o admin
    'django.middleware.clickjacking.XFrameOptionsMiddleware',     # Proteção contra ataques de clickjacking
]

# Rota do arquivo central de URLs
ROOT_URLCONF = 'config.urls'

# Configuração de templates do Django (usados principalmente pelo admin nativo)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Definição dos módulos de aplicação WSGI e ASGI
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ---------------------------------------------------------------------------
# Banco de Dados
# ---------------------------------------------------------------------------
# Suporta conexão direta com PostgreSQL quando configurado via variáveis de ambiente (.env),
# mantendo fallback padrão para SQLite no ambiente de desenvolvimento local.
if os.getenv('POSTGRES_DB') or os.getenv('DB_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', os.getenv('DB_NAME', 'lumenlab')),
            'USER': os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'postgres')),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', '')),
            'HOST': os.getenv('POSTGRES_HOST', os.getenv('DB_HOST', 'localhost')),
            'PORT': os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432')),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ---------------------------------------------------------------------------
# Validação de Senhas
# ---------------------------------------------------------------------------
# Senhas manuais desativadas: a autenticação primária é intermediada pelo Google OAuth
AUTH_PASSWORD_VALIDATORS = []

# ---------------------------------------------------------------------------
# Configuração do Django REST Framework (DRF)
# ---------------------------------------------------------------------------
# Permissão global AllowAny para endpoints públicos com validação explícita via JWT/Google
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# ---------------------------------------------------------------------------
# Internacionalização e Fuso Horário
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Arquivos estáticos
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Configuração de CORS (Cross-Origin Resource Sharing)
# ---------------------------------------------------------------------------
# Permite que o frontend React rodando em Vite (localhost:5173) efetue requisições à API
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Parâmetros de Integração Google OAuth (Gmail)
# ---------------------------------------------------------------------------
# ID do Cliente Google registrado no Google Cloud Console para o LumenLab
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '').strip().strip('\'"')

# ---------------------------------------------------------------------------
# Configurações do Chatbot Lumia (AI Engine)
# ---------------------------------------------------------------------------
GOOGLE_API_KEY = (os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY', '')).strip().strip('\'"')
CHROMA_PERSIST_DIR = str(BASE_DIR / 'data' / 'chroma_db')
CHROMA_COLLECTION_NAME = 'lumenlab_docs'
RAG_DOCS_DIR = str(BASE_DIR / 'ai_engine' / 'knowledge')
