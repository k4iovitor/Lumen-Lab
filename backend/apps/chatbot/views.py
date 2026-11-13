"""
Views do chatbot Lumia com streaming SSE.

Fornece endpoint de mensagem via Server-Sent Events (SSE) para
comunicação em tempo real com o frontend React.
"""
from __future__ import annotations

import json
import traceback
from datetime import date

from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from langchain_core.messages import HumanMessage, AIMessage


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------

def _authenticate_user(request):
    """
    Extrai e valida o JWT do header Authorization.

    Returns:
        (user, error_response) — um dos dois será None.
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        return None, JsonResponse({'error': 'Token de autenticação ausente.'}, status=401)

    token = auth_header.split(' ', 1)[1].strip()

    try:
        from apps.authentication.utils import decode_jwt_token
        payload = decode_jwt_token(token)
        user_id = payload.get('user_id')

        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        return user, None

    except Exception as exc:
        return None, JsonResponse({'error': f'Token inválido: {exc}'}, status=401)


# ---------------------------------------------------------------------------
# Utilitários de sessão e contexto
# ---------------------------------------------------------------------------

def _get_or_create_session(user, session_id: str = None):
    """Obtém ou cria uma sessão de chat para o usuário."""
    from apps.chatbot.models import ChatSession

    if session_id:
        try:
            return ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            pass

    return ChatSession.objects.create(user=user)


def _build_student_context(user) -> dict:
    """Monta o contexto do estudante para o estado inicial do grafo."""
    student_name = user.get_full_name() or user.username
    age = 12  # padrão para a faixa etária da plataforma

    try:
        profile = user.student_profile
        if hasattr(profile, 'name') and profile.name:
            student_name = profile.name
        if hasattr(profile, 'birth_date') and profile.birth_date:
            today = date.today()
            age = today.year - profile.birth_date.year - (
                (today.month, today.day) < (profile.birth_date.month, profile.birth_date.day)
            )
    except Exception:
        pass

    return {
        'user_id': user.id,
        'student_name': student_name,
        'age': age,
    }


# ---------------------------------------------------------------------------
# Gerador SSE
# ---------------------------------------------------------------------------

def _sse_stream(user, message: str, session_id: str = None):
    """
    Gerador SSE que processa a mensagem pelo grafo Lumia e transmite tokens.

    Args:
        user: Instância do usuário autenticado.
        message: Mensagem do usuário.
        session_id: ID da sessão de chat (UUID string, opcional).
    Yields:
        Eventos SSE formatados como 'data: {...}\\n\\n'.
    """
    from ai_engine.agents.lumia_graph import get_lumia_graph
    from apps.chatbot.models import ChatSession, ChatMessage

    try:
        session = _get_or_create_session(user, session_id)
        student_ctx = _build_student_context(user)

        # Persiste mensagem do usuário
        ChatMessage.objects.create(
            session=session,
            role='user',
            content=message,
        )

        # Estado inicial do grafo
        graph = get_lumia_graph()
        config = {'configurable': {'thread_id': str(session.id)}}

        initial_state = {
            'messages': [HumanMessage(content=message)],
            'user_id': student_ctx['user_id'],
            'student_name': student_ctx['student_name'],
            'age': student_ctx['age'],
            'intent': None,
            'safety_level': 'safe',
            'retrieved_context': [],
            'habit_data': None,
            'generation': None,
        }

        # Sinaliza início do stream
        yield f'data: {json.dumps({"type": "start", "session_id": str(session.id)})}\n\n'

        # Executa o grafo LangGraph
        final_state = graph.invoke(initial_state, config=config)
        response_text = final_state.get('generation', '')

        # Fallback: busca na lista de mensagens
        if not response_text:
            for msg in reversed(final_state.get('messages', [])):
                if isinstance(msg, AIMessage):
                    response_text = msg.content
                    break

        # Transmite palavras individualmente (simula streaming)
        words = response_text.split(' ')
        for i, word in enumerate(words):
            token = word + (' ' if i < len(words) - 1 else '')
            yield f'data: {json.dumps({"type": "token", "token": token})}\n\n'

        # Persiste resposta da Lumia
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=response_text,
        )

        # Metadados finais
        meta = {
            'type': 'done',
            'intent': final_state.get('intent', 'casual_chat'),
            'safety_level': final_state.get('safety_level', 'safe'),
            'session_id': str(session.id),
        }
        yield f'data: {json.dumps(meta)}\n\n'

    except Exception:
        traceback.print_exc()
        error_payload = {
            'type': 'error',
            'message': 'Ocorreu um erro ao processar sua mensagem. Tente novamente.',
        }
        yield f'data: {json.dumps(error_payload)}\n\n'


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(['POST', 'OPTIONS'])
def message_view(request):
    """
    Endpoint principal do chatbot Lumia com streaming SSE.

    POST /api/chatbot/message/
    Headers: Authorization: Bearer <jwt_token>
    Body (JSON): {"message": "...", "session_id": "<uuid>"}  — session_id opcional

    Returns:
        StreamingHttpResponse com eventos SSE text/event-stream.
    """
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return response

    user, error = _authenticate_user(request)
    if error:
        return error

    try:
        body = json.loads(request.body.decode('utf-8'))
        message = body.get('message', '').strip()
        session_id = body.get('session_id')
    except Exception:
        return JsonResponse({'error': 'Corpo da requisição inválido.'}, status=400)

    if not message:
        return JsonResponse({'error': 'Mensagem não pode ser vazia.'}, status=400)

    response = StreamingHttpResponse(
        _sse_stream(user, message, session_id),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    response['Access-Control-Allow-Origin'] = '*'
    return response


@csrf_exempt
@require_http_methods(['GET'])
def session_history_view(request, session_id: str):
    """
    Retorna o histórico de mensagens de uma sessão.

    GET /api/chatbot/session/<session_id>/
    Headers: Authorization: Bearer <jwt_token>
    """
    user, error = _authenticate_user(request)
    if error:
        return error

    try:
        from apps.chatbot.models import ChatSession
        session = ChatSession.objects.get(id=session_id, user=user)
        messages = list(session.messages.all().values('id', 'role', 'content', 'created_at'))
        # Serializa UUIDs e datetimes para JSON
        for msg in messages:
            msg['id'] = str(msg['id'])
            if hasattr(msg['created_at'], 'isoformat'):
                msg['created_at'] = msg['created_at'].isoformat()
        return JsonResponse({'session_id': str(session.id), 'messages': messages})
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=404)


@csrf_exempt
@require_http_methods(['GET'])
def list_sessions_view(request):
    """
    Lista as sessões de chat do usuário autenticado.

    GET /api/chatbot/sessions/
    Headers: Authorization: Bearer <jwt_token>
    """
    user, error = _authenticate_user(request)
    if error:
        return error

    from apps.chatbot.models import ChatSession
    sessions_qs = ChatSession.objects.filter(user=user).values('id', 'created_at', 'updated_at')
    sessions = []
    for s in sessions_qs:
        sessions.append({
            'id': str(s['id']),
            'created_at': s['created_at'].isoformat() if hasattr(s['created_at'], 'isoformat') else str(s['created_at']),
            'updated_at': s['updated_at'].isoformat() if hasattr(s['updated_at'], 'isoformat') else str(s['updated_at']),
        })

    return JsonResponse({'sessions': sessions})
