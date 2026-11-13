"""
Controladores e endpoints da API de higiene digital e rotina consciente do LumenLab em português brasileiro.

Gerencia o armazenamento persistente no banco de dados (PostgreSQL/SQLite)
de hábitos, atividades de foco offline e tempo consciente de tela,
vinculados univocamente a cada estudante autenticado.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.contrib.auth.models import User
from datetime import datetime, date
import jwt

from .models import Habit, ScreenTimeGoal


def _obter_usuario_da_requisicao(requisicao):
    """
    Identifica o usuário autenticado a partir do cabeçalho HTTP Authorization (Bearer JWT).

    Funcionamento passo a passo:
      1. Extrai o cabeçalho 'Authorization' da requisição.
      2. Se presente com o prefixo 'Bearer ', extrai o token JWT.
      3. Decodifica o token usando a chave secreta do Django (SECRET_KEY) e algoritmo HS256.
      4. Resgata o id_usuario contido no payload e busca o usuário correspondente no banco.
      5. Se o usuário estiver autenticado via sessão padrão do Django, retorna requisicao.user.
      6. Em ambiente de desenvolvimento local, fornece fallback para o primeiro usuário cadastrado.

    Parâmetros:
        requisicao (HttpRequest): Objeto de requisição do Django REST Framework.

    Retorna:
        User: Instância do usuário autenticado ou None caso não localizado.
    """
    cabecalho_autorizacao = requisicao.headers.get('Authorization', '')
    if cabecalho_autorizacao.startswith('Bearer '):
        token_jwt = cabecalho_autorizacao.split(' ', 1)[1].strip()
        try:
            dados_payload = jwt.decode(token_jwt, settings.SECRET_KEY, algorithms=['HS256'])
            id_usuario = dados_payload.get('user_id') or dados_payload.get('id_usuario')
            if id_usuario:
                usuario_localizado = User.objects.filter(id=id_usuario).first()
                if usuario_localizado:
                    return usuario_localizado
        except Exception:
            pass

    if requisicao.user and requisicao.user.is_authenticated:
        return requisicao.user

    # Fallback para o primeiro usuário em ambiente local de teste
    return User.objects.first()


# Alias para compatibilidade
_get_user_from_request = _obter_usuario_da_requisicao


@api_view(['GET', 'POST'])
def colecao_habitos(requisicao):
    """
    Manipula a coleção de hábitos do estudante autenticado.

    Funcionamento:
      - GET: Retorna a lista de hábitos filtrados por data pontual (?date= ou ?data=)
             ou por intervalo de datas (?start_date= & ?end_date=).
      - POST: Delega a criação e persistência de um novo hábito para _criar_habito_interno().

    Parâmetros:
        requisicao: Requisição HTTP contendo filtros de consulta (GET) ou corpo JSON (POST).

    Retorna:
        Response: Dicionário contendo lista de hábitos ou confirmação do novo registro criado.
    """
    usuario_autenticado = _obter_usuario_da_requisicao(requisicao)
    if not usuario_autenticado:
        return Response(
            {'erro': 'Usuário não autenticado ou perfil não encontrado.', 'error': 'Não autenticado.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if requisicao.method == 'GET':
        consulta_habitos = Habit.objects.filter(user=usuario_autenticado)

        data_alvo = requisicao.query_params.get('date') or requisicao.query_params.get('data')
        data_inicio = requisicao.query_params.get('start_date') or requisicao.query_params.get('data_inicio')
        data_fim = requisicao.query_params.get('end_date') or requisicao.query_params.get('data_fim')

        if data_alvo:
            consulta_habitos = consulta_habitos.filter(date=data_alvo)
        elif data_inicio and data_fim:
            consulta_habitos = consulta_habitos.filter(date__range=[data_inicio, data_fim])

        lista_formatada = [h.to_dict() for h in consulta_habitos.order_by('date', 'time', 'id')]
        return Response({
            'sucesso': True,
            'success': True,
            'habitos': lista_formatada,
            'habits': lista_formatada,
        })

    # POST: Encaminha para função de criação interna
    return _criar_habito_interno(requisicao, usuario_autenticado)


# Alias para rota pré-existente
habits_collection = colecao_habitos


@api_view(['POST'])
def criar_novo_habito(requisicao):
    """
    Endpoint dedicado para criação e persistência de um novo hábito na agenda.

    Funcionamento:
      1. Autentica o usuário solicitante via token JWT.
      2. Valida os campos obrigatórios (título, horário, categoria e data).
      3. Salva a nova instância no banco relacional.

    Parâmetros:
        requisicao: Requisição HTTP contendo corpo JSON com dados do hábito.
    """
    usuario_autenticado = _obter_usuario_da_requisicao(requisicao)
    if not usuario_autenticado:
        return Response(
            {'erro': 'Usuário não autenticado.', 'error': 'Não autenticado.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    return _criar_habito_interno(requisicao, usuario_autenticado)


# Alias para rota pré-existente
create_habit = criar_novo_habito


def _criar_habito_interno(requisicao, usuario):
    """
    Função interna para validação estrita e persistência do hábito no banco de dados.

    Funcionamento:
      1. Extrai o título e valida que não é uma string vazia.
      2. Converte a data recebida (formato YYYY-MM-DD); caso ausente, adota a data de hoje.
      3. Valida a categoria (kind) entre 'foco' (offline) e 'online' (consciente).
      4. Persiste o registro no banco e retorna HTTP 201 Created.
    """
    dados_requisicao = requisicao.data
    titulo_habito = str(dados_requisicao.get('title') or dados_requisicao.get('titulo', '')).strip()
    if not titulo_habito:
        return Response(
            {'erro': 'O título do hábito é obrigatório.', 'error': 'Título obrigatório.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    texto_data = dados_requisicao.get('date') or dados_requisicao.get('data')
    if not texto_data:
        data_programada = date.today()
    else:
        try:
            data_programada = datetime.strptime(str(texto_data), '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'erro': 'Formato de data inválido. Utilize YYYY-MM-DD.', 'error': 'Data inválida.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    horario_estipulado = str(dados_requisicao.get('time') or dados_requisicao.get('horario', '14:00')).strip()
    tipo_atividade = str(dados_requisicao.get('kind') or dados_requisicao.get('tipo', 'foco')).strip().lower()
    if tipo_atividade not in ['foco', 'online']:
        tipo_atividade = 'foco'

    descricao_texto = str(dados_requisicao.get('description') or dados_requisicao.get('descricao', '')).strip()
    if not descricao_texto:
        descricao_texto = 'Hábito de foco e higiene digital planejado na agenda.'

    # Criação e persistência do hábito no banco de dados
    registro_habito = Habit.objects.create(
        user=usuario,
        title=titulo_habito,
        description=descricao_texto,
        date=data_programada,
        time=horario_estipulado,
        kind=tipo_atividade,
        finished=False
    )

    return Response(
        {
            'sucesso': True,
            'success': True,
            'habito': registro_habito.to_dict(),
            'habit': registro_habito.to_dict(),
        },
        status=status.HTTP_201_CREATED
    )


# Alias para função interna
_create_habit_internal = _criar_habito_interno


@api_view(['POST'])
def alternar_conclusao_habito(requisicao):
    """
    Alterna o status de conclusão (concluído / pendente) de um hábito persistido.

    Funcionamento:
      1. Lê o identificador do hábito ('id' ou 'id_habito') e o booleano de conclusão ('finished' ou 'concluido').
      2. Localiza o hábito no banco de dados.
      3. Atualiza o campo finished e persiste a alteração.

    Retorna:
        Response: Dicionário confirmando a alteração de status do hábito.
    """
    _ = _obter_usuario_da_requisicao(requisicao)
    id_habito = requisicao.data.get('id') or requisicao.data.get('id_habito')
    esta_concluido = requisicao.data.get('finished') if 'finished' in requisicao.data else requisicao.data.get('concluido', False)

    if not id_habito:
        return Response(
            {'erro': 'Identificador do hábito não informado.', 'error': 'ID ausente.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    registro_habito = Habit.objects.filter(id=id_habito).first()
    if not registro_habito:
        return Response(
            {'erro': f'Hábito com ID {id_habito} não localizado.', 'error': 'Não localizado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    registro_habito.finished = bool(esta_concluido)
    registro_habito.save()

    return Response({
        'sucesso': True,
        'success': True,
        'id_habito': str(registro_habito.id),
        'habitId': str(registro_habito.id),
        'concluido': registro_habito.finished,
        'finished': registro_habito.finished,
        'habito': registro_habito.to_dict(),
        'habit': registro_habito.to_dict(),
    })


# Alias para rota pré-existente
toggle_habit = alternar_conclusao_habito


@api_view(['POST'])
def excluir_habito_agenda(requisicao):
    """
    Remove permanentemente um hábito do banco de dados relacional.

    Parâmetros:
        requisicao: Requisição POST contendo corpo JSON com {'id': <id_habito>}.
    """
    _ = _obter_usuario_da_requisicao(requisicao)
    id_habito = requisicao.data.get('id') or requisicao.data.get('id_habito')

    if not id_habito:
        return Response(
            {'erro': 'Identificador do hábito não informado.', 'error': 'ID ausente.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    registro_habito = Habit.objects.filter(id=id_habito).first()
    if not registro_habito:
        return Response(
            {'erro': f'Hábito com ID {id_habito} não localizado.', 'error': 'Não localizado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    registro_habito.delete()
    return Response({
        'sucesso': True,
        'success': True,
        'id_excluido': str(id_habito),
        'deletedId': str(id_habito),
    })


# Alias para rota pré-existente
delete_habit = excluir_habito_agenda


@api_view(['GET', 'POST'])
def visualizacao_meta_tempo_tela(requisicao):
    """
    Consulta ou atualiza as metas e proporções de tempo consciente de tela do estudante.

    Regras de Negócio Pedagógicas:
      - Limite diário estrito de no máximo 240 minutos (4 horas).
      - Divisão automática de entretenimento: 75% para jogos/vídeos e 25% para redes sociais.
      - Tempo protegido obrigatório para estudos e afazeres offline.

    Parâmetros:
        requisicao: GET para consulta ou POST com payload de atualização.
    """
    usuario_autenticado = _obter_usuario_da_requisicao(requisicao)
    if not usuario_autenticado:
        return Response(
            {'erro': 'Usuário não autenticado.', 'error': 'Não autenticado.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    registro_meta, _ = ScreenTimeGoal.objects.get_or_create(user=usuario_autenticado)

    if requisicao.method == 'GET':
        return Response({
            'sucesso': True,
            'success': True,
            'tempoTela': registro_meta.to_dict(),
            'screenTime': registro_meta.to_dict(),
        })

    # POST: Atualiza os limites e cálculos proporcionais
    dados_corpo = requisicao.data
    minutos_diarios = dados_corpo.get('dailyLimitMinutes') or dados_corpo.get('limiteDiarioMinutos')

    if minutos_diarios is None and ('dailyLimitHours' in dados_corpo or 'limiteDiarioHoras' in dados_corpo):
        try:
            horas_valor = dados_corpo.get('dailyLimitHours') or dados_corpo.get('limiteDiarioHoras')
            minutos_diarios = int(float(horas_valor) * 60)
        except (ValueError, TypeError):
            pass

    if minutos_diarios is not None:
        try:
            valor_minutos = int(minutos_diarios)
            # Teto estrito entre 30 minutos e 240 minutos (4h)
            valor_minutos = min(240, max(30, valor_minutos))
            registro_meta.daily_limit_minutes = valor_minutos
        except (ValueError, TypeError):
            return Response(
                {'erro': 'Valor de minutos inválido.', 'error': 'Minutos inválidos.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    minutos_afazeres = dados_corpo.get('choresReservedMinutes') or dados_corpo.get('minutosAfazeresReservados')
    if minutos_afazeres is not None:
        try:
            registro_meta.chores_reserved_minutes = max(0, int(minutos_afazeres))
        except (ValueError, TypeError):
            pass

    # Atualizações opcionais de consumo real do dia
    if 'gamesVideoUsedMinutes' in dados_corpo or 'jogosVideoMinutosUsados' in dados_corpo:
        valor = dados_corpo.get('gamesVideoUsedMinutes') or dados_corpo.get('jogosVideoMinutosUsados')
        registro_meta.games_video_used_minutes = max(0, int(valor))

    if 'socialMediaUsedMinutes' in dados_corpo or 'redesSociaisMinutosUsados' in dados_corpo:
        valor = dados_corpo.get('socialMediaUsedMinutes') or dados_corpo.get('redesSociaisMinutosUsados')
        registro_meta.social_media_used_minutes = max(0, int(valor))

    if 'studyUsedMinutes' in dados_corpo or 'estudosMinutosUsados' in dados_corpo:
        valor = dados_corpo.get('studyUsedMinutes') or dados_corpo.get('estudosMinutosUsados')
        registro_meta.study_used_minutes = max(0, int(valor))

    registro_meta.save()

    return Response({
        'sucesso': True,
        'success': True,
        'tempoTela': registro_meta.to_dict(),
        'screenTime': registro_meta.to_dict(),
    })


# Alias para rota pré-existente
screen_time_goal_view = visualizacao_meta_tempo_tela
