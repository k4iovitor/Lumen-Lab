"""
Ferramentas de integração do Django para o agente de IA da Lumia em português brasileiro.

Permite que a assistente socrática consulte informações do banco de dados relacional,
como metas de tempo de tela e hábitos de higiene digital, e obtenha contatos de emergência.
"""
from __future__ import annotations

import os
from datetime import date
from langchain_core.tools import tool


@tool
def consultar_meta_tempo_tela(id_usuario: int) -> dict:
    """
    Consulta as metas e o consumo de tempo de tela do estudante para o dia atual.

    Funcionamento:
      1. Recebe o identificador do usuário Django.
      2. Busca no banco de dados o registro mais recente em ScreenTimeGoal.
      3. Se encontrado, retorna o dicionário com limites de jogos, redes e afazeres.
      4. Caso contrário, retorna mensagem informativa de ausência de metas.

    Parâmetros:
        id_usuario (int): ID da tabela auth_user do Django.

    Retorna:
        dict: Dicionário com limite diário, consumo realizado e minutos restantes.
    """
    try:
        from apps.digital_hygiene.models import ScreenTimeGoal

        registro_meta = ScreenTimeGoal.objects.filter(user_id=id_usuario).order_by('-updated_at').first()
        if registro_meta is None:
            return {'erro': 'Nenhuma meta de tempo de tela configurada até o momento.'}
        return registro_meta.to_dict()

    except Exception as erro_excecao:
        return {'erro': f'Falha ao consultar a meta de tempo de tela: {erro_excecao}'}


@tool
def obter_habitos_hoje(id_usuario: int) -> list:
    """
    Retorna a lista de hábitos e atividades programadas pelo estudante para o dia de hoje.

    Funcionamento:
      1. Obtém a data corrente do sistema operacional.
      2. Filtra as atividades da tabela Habit agendadas para essa data específica.
      3. Retorna a lista de hábitos ordenados cronologicamente pelo horário.

    Parâmetros:
        id_usuario (int): ID do usuário na tabela auth_user.

    Retorna:
        list: Lista de dicionários contendo título, horário, categoria e status de conclusão.
    """
    try:
        from apps.digital_hygiene.models import Habit

        data_de_hoje = date.today()
        lista_habitos = Habit.objects.filter(user_id=id_usuario, date=data_de_hoje).order_by('time')
        return [habito.to_dict() for habito in lista_habitos]

    except Exception as erro_excecao:
        return [{'erro': f'Falha ao consultar hábitos diários: {erro_excecao}'}]


@tool
def obter_contatos_emergencia() -> dict:
    """
    Fornece os canais oficiais e gratuitos de apoio para situações de risco e perigo digital.

    Funcionamento:
      - Retorna um catálogo seguro com contatos para denúncia de crimes cibernéticos,
        remoção emergencial de imagens íntimas sem consentimento e suporte emocional.

    Retorna:
        dict: Dicionário contendo lista de recursos com nome, canal de contato e descrição.
    """
    return {
        'recursos_apoio': [
            {
                'nome': 'SaferNet Brasil',
                'canal': 'https://safernet.org.br',
                'descricao': 'Canal anônimo para denúncia de crimes cibernéticos contra crianças e adolescentes.',
                'categoria': 'denúncia online',
            },
            {
                'nome': 'Take It Down',
                'canal': 'https://takeitdown.ncmec.org',
                'descricao': 'Plataforma para remover fotos ou vídeos íntimos compartilhados sem consentimento.',
                'categoria': 'remoção de conteúdo',
            },
            {
                'nome': 'Disque 100',
                'canal': '100',
                'descricao': 'Disque Direitos Humanos: serviço telefônico gratuito para denúncias de violações.',
                'categoria': 'telefone emergencial',
            },
            {
                'nome': 'CVV — Centro de Valorização da Vida',
                'canal': '188',
                'descricao': 'Apoio emocional e prevenção ao suicídio disponível 24 horas por dia.',
                'categoria': 'suporte psicológico',
            },
        ]
    }


# Aliases para retrocompatibilidade
check_screen_time_goal = consultar_meta_tempo_tela
get_today_habits = obter_habitos_hoje
get_emergency_contacts = obter_contatos_emergencia
