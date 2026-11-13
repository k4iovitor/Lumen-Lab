"""
Controladores e visualizações (views) do chatbot Lumia com streaming SSE em português brasileiro.

Fornece endpoints para processamento de mensagens com Server-Sent Events (SSE)
e recuperação do histórico relacional de sessões.
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
# Autenticação de Usuários
# ---------------------------------------------------------------------------

def _autenticar_usuario(requisicao):
    """
    Extrai e valida o token JWT contido no cabeçalho HTTP Authorization.

    Funcionamento:
      1. Lê o cabeçalho 'Authorization' da requisição.
      2. Valida se inicia com o prefixo 'Bearer '.
      3. Invoca decodificar_token_jwt() para autenticação criptográfica.
      4. Resgata a instância correspondente do modelo User.

    Parâmetros:
        requisicao (HttpRequest): Requisição HTTP recebida.

    Retorna:
        tuple: (usuario, resposta_erro) — um dos elementos será None.
    """
    cabecalho_autorizacao = requisicao.META.get('HTTP_AUTHORIZATION', '')
    if not cabecalho_autorizacao.startswith('Bearer '):
        return None, JsonResponse({'erro': 'Token de autenticação não fornecido no cabeçalho.', 'error': 'Token ausente.'}, status=401)

    token_jwt = cabecalho_autorizacao.split(' ', 1)[1].strip()

    try:
        from apps.authentication.utils import decodificar_token_jwt
        dados_token = decodificar_token_jwt(token_jwt)
        id_usuario = dados_token.get('user_id') or dados_token.get('id_usuario')

        from django.contrib.auth.models import User
        usuario_autenticado = User.objects.get(id=id_usuario)
        return usuario_autenticado, None

    except Exception as erro_autenticacao:
        return None, JsonResponse({'erro': f'Token inválido ou expirado: {erro_autenticacao}', 'error': str(erro_autenticacao)}, status=401)


# ---------------------------------------------------------------------------
# Gestão de Sessões e Contexto do Estudante
# ---------------------------------------------------------------------------

def _obter_ou_criar_sessao(usuario, id_sessao: str = None):
    """
    Localiza uma sessão existente vinculada ao usuário ou cria uma nova sessão unívoca.

    Parâmetros:
        usuario (User): Instância do usuário Django autenticado.
        id_sessao (str, opcional): UUID da sessão existente em formato string.

    Retorna:
        SessaoChat: Objeto de sessão de chat ativo.
    """
    from apps.chatbot.models import SessaoChat

    if id_sessao:
        try:
            return SessaoChat.objects.get(id=id_sessao, usuario=usuario)
        except SessaoChat.DoesNotExist:
            pass

    return SessaoChat.objects.create(usuario=usuario)


def _montar_contexto_estudante(usuario) -> dict:
    """
    Extrai nome e idade do estudante para guiar o tom pedagógico do agente.

    Parâmetros:
        usuario (User): Usuário logado.

    Retorna:
        dict: Dicionário contendo id_usuario, nome_estudante e idade.
    """
    nome_estudante = usuario.get_full_name() or usuario.username
    idade_padrao = 12

    try:
        perfil = getattr(usuario, 'student_profile', None) or getattr(usuario, 'perfil_estudante', None)
        if perfil:
            if hasattr(perfil, 'first_name') and perfil.first_name:
                nome_estudante = perfil.first_name
            elif hasattr(perfil, 'nome') and perfil.nome:
                nome_estudante = perfil.nome

            data_nasc = getattr(perfil, 'date_of_birth', None) or getattr(perfil, 'data_nascimento', None)
            if data_nasc:
                hoje = date.today()
                idade_padrao = hoje.year - data_nasc.year - (
                    (hoje.month, hoje.day) < (data_nasc.month, data_nasc.day)
                )
    except Exception:
        pass

    return {
        'id_usuario': usuario.id,
        'user_id': usuario.id,
        'nome_estudante': nome_estudante,
        'student_name': nome_estudante,
        'idade': idade_padrao,
        'age': idade_padrao,
    }


# ---------------------------------------------------------------------------
# Gerador de Streaming SSE
# ---------------------------------------------------------------------------

def _fluxo_sse(usuario, mensagem_texto: str, id_sessao: str = None):
    """
    Gerador em tempo real (Server-Sent Events) para comunicação socrática.

    Funcionamento:
      1. Obtém a sessão e persiste a fala do estudante.
      2. Monta o estado inicial em português e executa o grafo LangGraph.
      3. Transmite palavra a palavra para efeito de digitação suave no frontend.
      4. Persiste a resposta da Lumia e encerra com evento 'concluido'.

    Parâmetros:
        usuario (User): Usuário autenticado.
        mensagem_texto (str): Pergunta do estudante.
        id_sessao (str, opcional): Identificador UUID da sessão.

    Produz:
        str: Eventos SSE no formato 'data: {...}\\n\\n'.
    """
    from ai_engine.agents.lumia_graph import obter_grafo_lumia
    from apps.chatbot.models import SessaoChat, MensagemChat

    try:
        sessao = _obter_ou_criar_sessao(usuario, id_sessao)
        contexto_estudante = _montar_contexto_estudante(usuario)

        # 1. Registra a mensagem do usuário no banco relacional
        MensagemChat.objects.create(
            sessao=sessao,
            papel='usuario',
            conteudo=mensagem_texto,
        )

        # 2. Configura a thread de execução do LangGraph
        grafo_lumia = obter_grafo_lumia()
        configuracao_grafo = {'configurable': {'thread_id': str(sessao.id)}}

        estado_inicial = {
            'mensagens': [HumanMessage(content=mensagem_texto)],
            'messages': [HumanMessage(content=mensagem_texto)],
            'id_usuario': contexto_estudante['id_usuario'],
            'user_id': contexto_estudante['id_usuario'],
            'nome_estudante': contexto_estudante['nome_estudante'],
            'student_name': contexto_estudante['nome_estudante'],
            'idade': contexto_estudante['idade'],
            'age': contexto_estudante['idade'],
            'intencao': None,
            'intent': None,
            'nivel_seguranca': 'seguro',
            'safety_level': 'safe',
            'contexto_recuperado': [],
            'retrieved_context': [],
            'dados_habito': None,
            'habit_data': None,
            'geracao': None,
            'generation': None,
        }

        # 3. Notifica início do stream
        evento_inicio = {
            'tipo': 'inicio',
            'type': 'start',
            'id_sessao': str(sessao.id),
            'session_id': str(sessao.id),
        }
        yield f'data: {json.dumps(evento_inicio)}\n\n'

        # 4. Executa o grafo cognitivo
        estado_final = grafo_lumia.invoke(estado_inicial, config=configuracao_grafo)
        resposta_texto = estado_final.get('geracao') or estado_final.get('generation', '')

        # Fallback de busca na lista de mensagens retornadas
        if not resposta_texto:
            lista_mensagens = estado_final.get('mensagens') or estado_final.get('messages', [])
            for msg in reversed(lista_mensagens):
                if isinstance(msg, AIMessage):
                    resposta_texto = msg.content
                    break

        # 5. Transmissão por palavras para efeito reativo
        palavras = resposta_texto.split(' ')
        for indice, palavra in enumerate(palavras):
            token_formatado = palavra + (' ' if indice < len(palavras) - 1 else '')
            evento_token = {
                'tipo': 'token',
                'type': 'token',
                'token': token_formatado,
            }
            yield f'data: {json.dumps(evento_token)}\n\n'

        # 6. Persiste a resposta da Lumia no banco relacional
        MensagemChat.objects.create(
            sessao=sessao,
            papel='assistente',
            conteudo=resposta_texto,
        )

        # 7. Emissão do evento de conclusão com metadados
        evento_conclusao = {
            'tipo': 'concluido',
            'type': 'done',
            'intencao': estado_final.get('intencao') or estado_final.get('intent', 'conversa_casual'),
            'intent': estado_final.get('intent', 'casual_chat'),
            'nivel_seguranca': estado_final.get('nivel_seguranca') or estado_final.get('safety_level', 'seguro'),
            'safety_level': estado_final.get('safety_level', 'safe'),
            'id_sessao': str(sessao.id),
            'session_id': str(sessao.id),
        }
        yield f'data: {json.dumps(evento_conclusao)}\n\n'

    except Exception as erro_processamento:
        traceback.print_exc()
        evento_erro = {
            'tipo': 'erro',
            'type': 'error',
            'mensagem': 'Ocorreu uma instabilidade ao processar sua dúvida. Por favor, tente novamente.',
            'message': 'Ocorreu um erro ao processar sua mensagem.',
        }
        yield f'data: {json.dumps(evento_erro)}\n\n'


# ---------------------------------------------------------------------------
# Visualizações Públicas (Views)
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(['POST', 'OPTIONS'])
def visualizacao_mensagem(requisicao):
    """
    Endpoint principal para envio de dúvidas e recepção de streaming SSE.

    POST /api/chatbot/mensagem/
    """
    if requisicao.method == 'OPTIONS':
        resposta_cors = JsonResponse({})
        resposta_cors['Access-Control-Allow-Origin'] = '*'
        resposta_cors['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        resposta_cors['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return resposta_cors

    usuario, erro_resposta = _autenticar_usuario(requisicao)
    if erro_resposta:
        return erro_resposta

    try:
        dados_corpo = json.loads(requisicao.body.decode('utf-8'))
        mensagem_texto = (dados_corpo.get('mensagem') or dados_corpo.get('message', '')).strip()
        id_sessao = dados_corpo.get('id_sessao') or dados_corpo.get('session_id')
    except Exception:
        return JsonResponse({'erro': 'Corpo da requisição JSON inválido.', 'error': 'JSON inválido.'}, status=400)

    if not mensagem_texto:
        return JsonResponse({'erro': 'A mensagem não pode ser vazia.', 'error': 'Mensagem vazia.'}, status=400)

    resposta_stream = StreamingHttpResponse(
        _fluxo_sse(usuario, mensagem_texto, id_sessao),
        content_type='text/event-stream',
    )
    resposta_stream['Cache-Control'] = 'no-cache'
    resposta_stream['X-Accel-Buffering'] = 'no'
    resposta_stream['Access-Control-Allow-Origin'] = '*'
    return resposta_stream


@csrf_exempt
@require_http_methods(['GET'])
def visualizacao_historico_sessao(requisicao, id_sessao: str):
    """
    Retorna o histórico cronológico de mensagens de uma sessão.

    GET /api/chatbot/sessao/<id_sessao>/
    """
    usuario, erro_resposta = _autenticar_usuario(requisicao)
    if erro_resposta:
        return erro_resposta

    try:
        from apps.chatbot.models import SessaoChat
        sessao = SessaoChat.objects.get(id=id_sessao, usuario=usuario)
        mensagens_banco = list(sessao.mensagens.all().values('id', 'papel', 'conteudo', 'criado_em'))

        mensagens_formatadas = []
        for msg in mensagens_banco:
            data_iso = msg['criado_em'].isoformat() if hasattr(msg['criado_em'], 'isoformat') else str(msg['criado_em'])
            mensagens_formatadas.append({
                'id': str(msg['id']),
                'papel': msg['papel'],
                'role': msg['papel'],
                'conteudo': msg['conteudo'],
                'content': msg['conteudo'],
                'criado_em': data_iso,
                'created_at': data_iso,
            })

        return JsonResponse({
            'id_sessao': str(sessao.id),
            'session_id': str(sessao.id),
            'mensagens': mensagens_formatadas,
            'messages': mensagens_formatadas,
        })
    except Exception as erro_busca:
        return JsonResponse({'erro': f'Sessão não localizada: {erro_busca}', 'error': str(erro_busca)}, status=404)


@csrf_exempt
@require_http_methods(['GET'])
def visualizacao_listar_sessoes(requisicao):
    """
    Lista todas as sessões conversacionais associadas ao usuário logado.

    GET /api/chatbot/sessoes/
    """
    usuario, erro_resposta = _autenticar_usuario(requisicao)
    if erro_resposta:
        return erro_resposta

    from apps.chatbot.models import SessaoChat
    sessoes_banco = SessaoChat.objects.filter(usuario=usuario).values('id', 'criado_em', 'atualizado_em')

    lista_sessoes = []
    for s in sessoes_banco:
        criado_iso = s['criado_em'].isoformat() if hasattr(s['criado_em'], 'isoformat') else str(s['criado_em'])
        atualizado_iso = s['atualizado_em'].isoformat() if hasattr(s['atualizado_em'], 'isoformat') else str(s['atualizado_em'])
        lista_sessoes.append({
            'id': str(s['id']),
            'id_sessao': str(s['id']),
            'criado_em': criado_iso,
            'created_at': criado_iso,
            'atualizado_em': atualizado_iso,
            'updated_at': atualizado_iso,
        })

    return JsonResponse({
        'sessoes': lista_sessoes,
        'sessions': lista_sessoes,
    })


# Aliases para compatibilidade integral
_authenticate_user = _autenticar_usuario
_get_or_create_session = _obter_ou_criar_sessao
_build_student_context = _montar_contexto_estudante
_sse_stream = _fluxo_sse
message_view = visualizacao_mensagem
session_history_view = visualizacao_historico_sessao
list_sessions_view = visualizacao_listar_sessoes
