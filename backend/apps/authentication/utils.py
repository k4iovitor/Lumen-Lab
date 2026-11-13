"""
Módulo de utilitários de autenticação JWT em português brasileiro.

Fornece funções para geração, assinatura criptográfica e validação de tokens JWT
utilizados na comunicação segura entre o cliente frontend e os endpoints da API.
"""
from __future__ import annotations

import datetime
import jwt
from django.conf import settings

# Constantes de configuração do algoritmo de criptografia e tempo de expiração do token
ALGORITMO_JWT = 'HS256'
HORAS_EXPIRACAO_JWT = 24

# Aliases em inglês para retrocompatibilidade
JWT_ALGORITHM = ALGORITMO_JWT
JWT_EXPIRATION_HOURS = HORAS_EXPIRACAO_JWT


def criar_token_jwt(id_usuario: int) -> str:
    """
    Gera um token JWT assinado contendo o identificador unívoco do usuário.

    Funcionamento passo a passo:
      1. Obtém o instante atual em horário UTC para registro de emissão (iat).
      2. Define a data e hora de expiração (exp) somando 24 horas ao instante atual.
      3. Monta o dicionário de carga útil (payload) com id_usuario, iat e exp.
      4. Assina e codifica o payload utilizando a chave secreta do Django (SECRET_KEY)
         e o algoritmo criptográfico HMAC-SHA256 (HS256).
      5. Retorna a string do token JWT pronta para inclusão no cabeçalho HTTP Authorization.

    Parâmetros:
        id_usuario (int): Chave primária do usuário registrado na tabela auth_user.

    Retorna:
        str: Token JWT codificado em formato texto seguro.
    """
    instante_atual = datetime.datetime.now(datetime.timezone.utc)
    dados_carga_util = {
        'user_id': id_usuario,
        'id_usuario': id_usuario,
        'iat': instante_atual,
        'exp': instante_atual + datetime.timedelta(hours=HORAS_EXPIRACAO_JWT),
    }
    return jwt.encode(dados_carga_util, settings.SECRET_KEY, algorithm=ALGORITMO_JWT)


def decodificar_token_jwt(token: str) -> dict:
    """
    Decodifica, valida e verifica a integridade criptográfica de um token JWT.

    Funcionamento passo a passo:
      1. Recebe a string do token extraída do cabeçalho de autorização.
      2. Utiliza a chave secreta do Django (SECRET_KEY) para verificar se a assinatura é autêntica.
      3. Checa automaticamente se o tempo de expiração (exp) já foi ultrapassado.
      4. Retorna o dicionário de dados (payload) decodificado contendo o identificador do usuário.

    Parâmetros:
        token (str): String com o token JWT no formato 'header.payload.signature'.

    Retorna:
        dict: Dicionário contendo os dados decodificados do usuário e os timestamps.

    Exceções disparadas:
        jwt.ExpiredSignatureError: Caso o token tenha sido emitido há mais de 24 horas.
        jwt.InvalidTokenError: Se a assinatura for inválida ou o conteúdo tiver sido adulterado.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITMO_JWT])


# Aliases para compatibilidade com chamadas pré-existentes
create_jwt = criar_token_jwt
decode_jwt_token = decodificar_token_jwt
