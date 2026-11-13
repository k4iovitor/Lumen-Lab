"""
Configurações para o ambiente de produção do LumenLab.

Em ambientes de produção reais (ex.: Docker, Railway, Render, AWS),
desative `DEBUG`, restrinja `ALLOWED_HOSTS` aos domínios autorizados,
habilite cookies seguros com HTTPS e configure o banco de dados PostgreSQL.
"""
from .base import *
import os

# Desativa mensagens de depuração em produção
DEBUG = False

# Domínios e IPs expressamente autorizados a acessar o backend
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Configurações de cookies e cabeçalhos seguros
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True

# Descomente abaixo em ambientes servidos obrigatoriamente sob HTTPS:
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
