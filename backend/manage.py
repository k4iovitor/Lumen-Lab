#!/usr/bin/env python
"""
Utilitário de linha de comando do Django para tarefas administrativas do LumenLab.

Permite executar o servidor de desenvolvimento, efetuar migrações no banco
de dados, criar superusuários e rodar rotinas de verificação do sistema.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def main():
    """Executa tarefas administrativas e operacionais do Django."""
    # Carrega variáveis de ambiente do .env da raiz ou da pasta backend
    base_dir = Path(__file__).resolve().parent
    load_dotenv(base_dir.parent / '.env')
    load_dotenv(base_dir / '.env')

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Não foi possível importar o Django. Verifique se ele está instalado "
            "e acessível na sua variável de ambiente PYTHONPATH. O ambiente virtual "
            "(.venv) está ativado?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
