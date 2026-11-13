"""
Ferramentas Django integradas ao grafo LangGraph da Lumia.

Define as ferramentas que a Lumia pode invocar para acessar dados
dos modelos de higiene digital e fornecer recursos de emergência.
"""
from __future__ import annotations

import os
from datetime import date

from langchain_core.tools import tool


@tool
def check_screen_time_goal(user_id: int) -> dict:
    """
    Consulta as metas de tempo de tela configuradas pelo estudante.

    Retorna os limites diários, uso atual e status de cada categoria
    (jogos/vídeos, redes sociais, estudos).

    Args:
        user_id: ID do usuário Django (auth_user.id).
    Returns:
        Dicionário com os dados de meta e uso do dia.
    """
    try:
        from apps.digital_hygiene.models import ScreenTimeGoal

        goal = ScreenTimeGoal.objects.filter(user_id=user_id).order_by('-updated_at').first()
        if goal is None:
            return {'error': 'Nenhuma meta de tempo de tela configurada.'}
        return goal.to_dict()

    except Exception as exc:
        return {'error': f'Erro ao consultar meta de tela: {exc}'}


@tool
def get_today_habits(user_id: int) -> list:
    """
    Retorna os hábitos agendados para o dia atual do estudante.

    Lista atividades de foco offline e uso consciente programadas para hoje,
    indicando quais já foram concluídas.

    Args:
        user_id: ID do usuário Django (auth_user.id).
    Returns:
        Lista de dicionários com os hábitos do dia.
    """
    try:
        from apps.digital_hygiene.models import Habit

        today = date.today()
        habits = Habit.objects.filter(user_id=user_id, date=today).order_by('time')
        return [habit.to_dict() for habit in habits]

    except Exception as exc:
        return [{'error': f'Erro ao consultar habitos: {exc}'}]


@tool
def get_emergency_contacts() -> dict:
    """
    Retorna os recursos de apoio em situações de risco digital.

    Fornece links e contatos para denúncia de crimes online,
    remoção de conteúdo íntimo e suporte emocional.

    Returns:
        Dicionário com nome, URL/contato e descrição de cada recurso.
    """
    return {
        'recursos': [
            {
                'nome': 'SaferNet Brasil',
                'contato': 'https://safernet.org.br',
                'descricao': 'Denuncie crimes e violações de direitos humanos na internet',
                'tipo': 'denúncia online',
            },
            {
                'nome': 'Take It Down',
                'contato': 'https://takeitdown.ncmec.org',
                'descricao': 'Remova fotos ou vídeos íntimos que foram compartilhados sem consentimento',
                'tipo': 'remoção de conteúdo',
            },
            {
                'nome': 'Disque 100',
                'contato': '100',
                'descricao': 'Canal gratuito para denúncias de violações contra crianças e adolescentes',
                'tipo': 'denúncia telefônica',
            },
            {
                'nome': 'CVV — Centro de Valorização da Vida',
                'contato': '188',
                'descricao': 'Apoio emocional e prevenção ao suicídio, 24 horas, gratuito',
                'tipo': 'apoio emocional',
            },
        ]
    }
