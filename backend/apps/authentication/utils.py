"""
Utilitários de autenticação JWT reutilizáveis em outros módulos do projeto.

Extrai as funções de geração e decodificação de JWT do views.py de autenticação
para permitir importação limpa por outras apps (ex: chatbot).
"""
from __future__ import annotations

import datetime
import jwt
from django.conf import settings

JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


def create_jwt(user_id: int) -> str:
    """
    Gera um token JWT assinado contendo o identificador do usuário.

    Args:
        user_id: ID do usuário Django.
    Returns:
        Token JWT codificado como string.
    """
    agora = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        'user_id': user_id,
        'iat': agora,
        'exp': agora + datetime.timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    """
    Decodifica e verifica a integridade e validade de um token JWT.

    Args:
        token: String com o token JWT recebido no cabeçalho Authorization.
    Returns:
        Payload decodificado como dicionário.
    Raises:
        jwt.ExpiredSignatureError: Se o token expirou.
        jwt.InvalidTokenError: Se o token é inválido.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
