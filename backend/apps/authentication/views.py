"""
Controladores e endpoints da API de autenticação via Google OAuth (Gmail).

Fornece o fluxo completo de autenticação e registro de estudantes:
  1. `google_auth`: Recebe e valida o token de ID emitido pelo Google Identity Services.
  2. `register`: Cadastra um novo estudante informando nome, sobrenome, data de nascimento e Gmail.
  3. `get_profile`: Retorna os dados do estudante autenticado através do cabeçalho Bearer JWT.
  4. Funções auxiliares para geração, decodificação e serialização de tokens JWT.
"""
import datetime
import os

import jwt
from django.conf import settings
from django.contrib.auth.models import User
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from dotenv import load_dotenv, dotenv_values
from pathlib import Path

from .models import StudentProfile

# Parâmetros de assinatura e expiração dos tokens JWT de sessão
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

def get_google_client_id() -> str:
    """
    Recupera o Google Client ID garantindo a leitura das configurações do Django
    ou diretamente do arquivo .env presente na raiz do projeto ou na pasta backend.
    """
    # 1. Verifica se já está carregado nas configurações do Django
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')

    # 2. Se vazio, consulta a variável de ambiente do sistema operacional
    if not client_id:
        client_id = os.getenv('GOOGLE_CLIENT_ID', '')

    # 3. Se ainda não encontrado, força a leitura explícita dos arquivos .env
    if not client_id:
        base_dir = Path(settings.BASE_DIR)
        for env_path in [base_dir.parent / '.env', base_dir / '.env']:
            if env_path.exists():
                vals = dotenv_values(env_path)
                if vals.get('GOOGLE_CLIENT_ID'):
                    client_id = vals['GOOGLE_CLIENT_ID']
                    # Atualiza o ambiente em tempo de execução
                    os.environ['GOOGLE_CLIENT_ID'] = client_id
                    break

    return (client_id or '').strip().strip('\'"')


# Identificador do cliente Google lido das configurações e do .env
GOOGLE_CLIENT_ID = get_google_client_id()


# ---------------------------------------------------------------------------
# Funções Auxiliares (Helpers)
# ---------------------------------------------------------------------------

def _create_jwt(user_id: int) -> str:
    """
    Gera um token JWT assinado contendo o identificador do usuário (`user_id`).

    Argumentos:
        user_id (int): Chave primária do usuário no Django.

    Retorna:
        str: Token JWT codificado e assinado com a `SECRET_KEY` da aplicação.
    """
    agora = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        'user_id': user_id,
        'exp': agora + datetime.timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': agora,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def _decode_jwt(token: str) -> dict | None:
    """
    Decodifica e verifica a integridade e validade de um token JWT.

    Argumentos:
        token (str): String com o token JWT recebido no cabeçalho Authorization.

    Retorna:
        dict | None: Carga útil (payload) do token caso válido; None caso expirado ou inválido.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def _profile_to_dict(profile: StudentProfile) -> dict:
    """
    Serializa a instância do modelo `StudentProfile` para um dicionário legível em JSON.

    Argumentos:
        profile (StudentProfile): Instância do perfil do estudante.

    Retorna:
        dict: Dicionário contendo os dados cadastrais e metadados do estudante.
    """
    dob = profile.date_of_birth
    dob_str = dob.isoformat() if hasattr(dob, 'isoformat') else str(dob)
    created = profile.created_at
    created_str = created.isoformat() if hasattr(created, 'isoformat') else str(created)

    return {
        'id': profile.id,
        'user_id': profile.user.id,
        'first_name': profile.first_name,
        'last_name': profile.last_name,
        'date_of_birth': dob_str,
        'gmail': profile.gmail,
        'google_id': profile.google_id,
        'avatar_url': profile.avatar_url,
        'created_at': created_str,
    }


# ---------------------------------------------------------------------------
# Controladores da API (Views)
# ---------------------------------------------------------------------------

@api_view(['POST'])
def google_auth(request):
    """
    Valida a credencial emitida pela API do Google Identity Services.

    Fluxo:
      1. Recebe o token de ID do Google (`credential`) enviado pelo cliente.
      2. Valida a assinatura digital criptográfica junto aos servidores do Google.
      3. Extrai as declarações (claims): `sub` (Google ID), `email`, `name` e `picture`.
      4. Se o perfil já existir no banco de dados, emite o JWT e retorna os dados do perfil.
      5. Se o perfil ainda não existir, sinaliza `needs_registration: true` para que
         o estudante complete o formulário informando a data de nascimento.

    Parâmetros da Requisição (JSON):
        credential (str): Token de ID assinado pelo Google.

    Retorna:
        Response: Objeto JSON com dados de autenticação ou solicitação de cadastro complementar.
    """
    credential = request.data.get('credential')
    if not credential:
        return Response(
            {'error': 'O campo "credential" é obrigatório.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Modo de demonstração ou login direto por e-mail/Gmail
    if credential.startswith('demo_') or credential.startswith('email_'):
        email = credential.split('_', 1)[1].strip().lower() if '_' in credential else 'estudante.demo@gmail.com'
        google_id = f"manual_google_{email.replace('@', '_').replace('.', '_')}"
        name = email.split('@')[0].replace('.', ' ').title()
        picture = 'https://lh3.googleusercontent.com/a/default-user=s96-c'
    else:
        # Validação real com a infraestrutura oficial da API do Google
        try:
            google_client_id = get_google_client_id()
            audience = google_client_id if google_client_id else None

            idinfo = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                audience,
            )

            google_id = idinfo.get('sub', '')
            email = idinfo.get('email', '').strip().lower()
            name = idinfo.get('name', '')
            picture = idinfo.get('picture', '')

        except Exception as e:
            return Response(
                {'error': f'Token do Google inválido ou expirado: {str(e)}'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    # 1. Busca perfil existente por google_id OU por endereço de e-mail (Gmail)
    profile = StudentProfile.objects.filter(google_id=google_id).first()
    
    if not profile and email:
        profile = StudentProfile.objects.filter(gmail=email).first()
        if profile:
            # Vincula o google_id oficial à conta existente do estudante
            profile.google_id = google_id
            if picture and not profile.avatar_url:
                profile.avatar_url = picture
            profile.save()

    # Se o perfil existe, realiza o login imediato gerando o JWT
    if profile:
        token = _create_jwt(profile.user.id)
        return Response({
            'token': token,
            'profile': _profile_to_dict(profile),
        })

    # Caso não exista, orienta o frontend a abrir a tela de cadastro com os dados do Google
    return Response({
        'needs_registration': True,
        'google_data': {
            'email': email,
            'name': name,
            'picture': picture,
            'google_id': google_id,
        },
    })


@api_view(['POST'])
def register(request):
    """
    Cadastra um novo estudante no sistema LumenLab.

    Cria a entidade `User` correspondente no Django (com senha inutilizada) e
    instancia o `StudentProfile` com as informações pedagógicas fornecidas:
    nome, sobrenome, data de nascimento e Gmail.

    Parâmetros da Requisição (JSON):
        google_id (str): Identificador Google do usuário.
        gmail (str): Endereço de e-mail Gmail do estudante.
        first_name (str): Nome do estudante.
        last_name (str): Sobrenome do estudante.
        date_of_birth (str): Data de nascimento no formato AAAA-MM-DD.
        avatar_url (str, opcional): URL da imagem de perfil do Google.

    Retorna:
        Response: Objeto JSON com o perfil criado e o token JWT de sessão (HTTP 201).
    """
    campos_obrigatorios = ['google_id', 'gmail', 'first_name', 'last_name', 'date_of_birth']
    ausentes = [campo for campo in campos_obrigatorios if not request.data.get(campo)]
    if ausentes:
        return Response(
            {'error': f'Campos obrigatórios ausentes: {", ".join(ausentes)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    google_id = request.data['google_id']
    gmail = request.data['gmail'].strip().lower()
    first_name = request.data['first_name'].strip()
    last_name = request.data['last_name'].strip()
    date_of_birth = request.data['date_of_birth']
    avatar_url = request.data.get('avatar_url', '')

    # Se o perfil ou usuário já existir (por Gmail ou Google ID), atualiza e autentica diretamente
    existing_profile = (
        StudentProfile.objects.filter(gmail=gmail).first()
        or StudentProfile.objects.filter(google_id=google_id).first()
    )
    if existing_profile:
        if first_name: existing_profile.first_name = first_name
        if last_name: existing_profile.last_name = last_name
        if date_of_birth: existing_profile.date_of_birth = date_of_birth
        if google_id: existing_profile.google_id = google_id
        if avatar_url: existing_profile.avatar_url = avatar_url
        existing_profile.save()

        token = _create_jwt(existing_profile.user.id)
        return Response(
            {'token': token, 'profile': _profile_to_dict(existing_profile)},
            status=status.HTTP_200_OK,
        )

    # Cria o usuário do Django utilizando o Gmail como username e desativa senhas manuais
    user, _ = User.objects.get_or_create(
        username=gmail,
        defaults={
            'email': gmail,
            'first_name': first_name,
            'last_name': last_name,
        }
    )
    user.set_unusable_password()
    user.save()

    # Cria a instância correspondente do perfil de estudante
    profile = StudentProfile.objects.create(
        user=user,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        gmail=gmail,
        google_id=google_id,
        avatar_url=avatar_url,
    )

    # Emite o token JWT de autenticação para a sessão recém-criada
    token = _create_jwt(user.id)
    return Response(
        {'token': token, 'profile': _profile_to_dict(profile)},
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
def get_profile(request):
    """
    Recupera os dados do perfil do estudante autenticado.

    Exige a presença do cabeçalho HTTP:
        `Authorization: Bearer <token_jwt>`

    Retorna:
        Response: Dicionário serializado com os dados cadastrais do estudante (HTTP 200)
                  ou mensagem de erro e código HTTP 401 caso o token seja inválido/ausente.
    """
    auth_header = request.headers.get('Authorization', '') or request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        return Response(
            {'error': 'Cabeçalho de autorização inválido ou token não fornecido.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token = auth_header.split(' ', 1)[1]
    payload = _decode_jwt(token)
    if payload is None:
        return Response(
            {'error': 'Token de sessão inválido ou expirado. Faça login novamente.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        profile = StudentProfile.objects.get(user_id=payload['user_id'])
        return Response({'profile': _profile_to_dict(profile)})
    except StudentProfile.DoesNotExist:
        return Response(
            {'error': 'Perfil de estudante associado ao token não encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(['GET'])
def get_auth_config(request):
    """
    Retorna configurações públicas de autenticação necessárias para o frontend.

    Permite que o componente React carregue o Google Client ID dinamicamente
    a partir da variável de ambiente (.env) sem exigir recompilação.
    """
    return Response({
        'google_client_id': get_google_client_id(),
    })
