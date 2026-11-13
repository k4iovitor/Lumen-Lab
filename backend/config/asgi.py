"""
Configuração ASGI (Asynchronous Server Gateway Interface) para o projeto LumenLab.

Expõe a variável invocável `application` para servidores assíncronos (ex.: Uvicorn, Daphne),
permitindo suporte a streaming de respostas de IA, conexões WebSockets e canais em tempo real.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

application = get_asgi_application()
