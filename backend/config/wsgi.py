"""
Configuração WSGI (Web Server Gateway Interface) para o projeto LumenLab.

Expõe a variável invocável `application` compatível com servidores web
síncronos de produção, tais como Gunicorn ou uWSGI.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

application = get_wsgi_application()
