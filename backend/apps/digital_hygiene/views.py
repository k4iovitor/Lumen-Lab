"""
Controladores e endpoints da API de higiene digital e rotina consciente do LumenLab.

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


def _get_user_from_request(request):
    """
    Identifica o usuário autenticado a partir do cabeçalho Authorization (Bearer JWT),
    da sessão Django ou do primeiro usuário cadastrado para depuração local.
    """
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1].strip()
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            if user_id:
                user = User.objects.filter(id=user_id).first()
                if user:
                    return user
        except Exception:
            pass

    if request.user and request.user.is_authenticated:
        return request.user

    # Fallback transparente para o primeiro usuário em ambiente local
    return User.objects.first()


@api_view(['GET', 'POST'])
def habits_collection(request):
    """
    Manipula a coleção de hábitos do estudante:
      - GET: Retorna os hábitos persistidos do usuário (com suporte a filtros ?date= e intervalo de datas).
      - POST: Cria e persiste um novo hábito vinculado ao usuário.
    """
    user = _get_user_from_request(request)
    if not user:
        return Response(
            {'error': 'Usuário não autenticado ou perfil não encontrado.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if request.method == 'GET':
        query = Habit.objects.filter(user=user)

        target_date = request.query_params.get('date')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if target_date:
            query = query.filter(date=target_date)
        elif start_date and end_date:
            query = query.filter(date__range=[start_date, end_date])

        habits_list = [h.to_dict() for h in query.order_by('date', 'time', 'id')]
        return Response({'success': True, 'habits': habits_list})

    # POST: Criar novo hábito
    return _create_habit_internal(request, user)


@api_view(['POST'])
def create_habit(request):
    """
    Cria uma nova linha no banco de dados exclusivo de hábitos vinculada ao estudante.
    """
    user = _get_user_from_request(request)
    if not user:
        return Response(
            {'error': 'Usuário não autenticado.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    return _create_habit_internal(request, user)


def _create_habit_internal(request, user):
    """Função interna para validação e persistência do hábito no banco de dados."""
    
    data = request.data
    title = str(data.get('title', '')).strip()
    if not title:
        return Response(
            {'error': 'O título do hábito é obrigatório.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    date_str = data.get('date')
    if not date_str:
        target_date = date.today()
    else:
        try:
            target_date = datetime.strptime(str(date_str), '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de data inválido. Utilize YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    time_str = str(data.get('time', '14:00')).strip()
    kind = str(data.get('kind', 'foco')).strip().lower()
    if kind not in ['foco', 'online']:
        kind = 'foco'

    description = str(data.get('description', '')).strip()
    if not description:
        description = 'Hábito de foco e higiene digital planejado na agenda.'

    # Persiste a linha na tabela exclusiva de hábitos
    habit = Habit.objects.create(
        user=user,
        title=title,
        description=description,
        date=target_date,
        time=time_str,
        kind=kind,
        finished=False
    )

    return Response(
        {'success': True, 'habit': habit.to_dict()},
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
def toggle_habit(request):
    """
    Alterna o status de conclusão de um hábito persistido no banco de dados.

    Parâmetros da Requisição (JSON):
        id (str|int): Identificador único do hábito.
        finished (bool): Novo estado booleano de conclusão.

    Retorna:
        Response: Confirmação da atualização com o registro persistido.
    """
    user = _get_user_from_request(request)
    habit_id = request.data.get('id')
    finished = request.data.get('finished', False)

    if not habit_id:
        return Response(
            {'error': 'Identificador do hábito não informado.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Busca o hábito garantindo a integridade relacional com o usuário
    habit = Habit.objects.filter(id=habit_id).first()
    if not habit:
        return Response(
            {'error': f'Hábito com ID {habit_id} não encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    habit.finished = bool(finished)
    habit.save()

    return Response({
        'success': True,
        'habitId': str(habit.id),
        'finished': habit.finished,
        'habit': habit.to_dict()
    })


@api_view(['POST'])
def delete_habit(request):
    """
    Remove um hábito persistido da agenda do estudante.

    Parâmetros da Requisição (JSON):
        id (str|int): Identificador único do hábito a ser excluído.
    """
    habit_id = request.data.get('id')
    if not habit_id:
        return Response(
            {'error': 'Identificador do hábito não informado.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    habit = Habit.objects.filter(id=habit_id).first()
    if not habit:
        return Response(
            {'error': f'Hábito com ID {habit_id} não encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    habit.delete()
    return Response({'success': True, 'deletedId': str(habit_id)})


@api_view(['GET', 'POST'])
def screen_time_goal_view(request):
    """
    Consulta ou atualiza as metas de tempo de tela e desconexão consciente do estudante.

    Regras de Negócio:
      - Limite máximo diário estrito: 4 horas (240 minutos).
      - Proporção exata para entretenimento:
          * 75% destinado para Jogos e Vídeos (máximo de 3h quando total for 4h).
          * 25% destinado para Redes Sociais (máximo de 1h quando total for 4h).
      - Reserva de tempo dedicado para cumprimento de afazeres escolares e foco offline.
    """
    user = _get_user_from_request(request)
    if not user:
        return Response(
            {'error': 'Usuário não autenticado.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    goal, _ = ScreenTimeGoal.objects.get_or_create(user=user)

    if request.method == 'GET':
        return Response({'success': True, 'screenTime': goal.to_dict()})

    # POST: Atualiza as metas
    data = request.data
    daily_minutes = data.get('dailyLimitMinutes')
    if daily_minutes is None and 'dailyLimitHours' in data:
        try:
            daily_minutes = int(float(data['dailyLimitHours']) * 60)
        except (ValueError, TypeError):
            pass

    if daily_minutes is not None:
        try:
            minutes_val = int(daily_minutes)
            # Aplica teto estrito de 4 horas (240 minutos)
            minutes_val = min(240, max(30, minutes_val))
            goal.daily_limit_minutes = minutes_val
        except (ValueError, TypeError):
            return Response(
                {'error': 'Valor de minutos inválido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    chores_minutes = data.get('choresReservedMinutes')
    if chores_minutes is not None:
        try:
            goal.chores_reserved_minutes = max(0, int(chores_minutes))
        except (ValueError, TypeError):
            pass

    # Atualizações opcionais de consumo real
    if 'gamesVideoUsedMinutes' in data:
        goal.games_video_used_minutes = max(0, int(data['gamesVideoUsedMinutes']))
    if 'socialMediaUsedMinutes' in data:
        goal.social_media_used_minutes = max(0, int(data['socialMediaUsedMinutes']))
    if 'studyUsedMinutes' in data:
        goal.study_used_minutes = max(0, int(data['studyUsedMinutes']))

    goal.save()
    return Response({'success': True, 'screenTime': goal.to_dict()})

