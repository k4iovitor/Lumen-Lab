"""
Grafo LangGraph do chatbot Lumia.

Define o estado, os nós de processamento e o fluxo condicional
da assistente socrática para jovens de 10 a 14 anos.

Arquitetura:
  entrada -> guardrail -> (router) -> [rag | habit | socratic | emergency | chat]
                                                    |
                                               generation -> saída
"""
from __future__ import annotations

import os
from typing import Annotated, List, Literal, Optional, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from ai_engine.agents.prompts import (
    LUMIA_SYSTEM_PROMPT,
    INTENT_CLASSIFICATION_PROMPT,
    SAFETY_GUARDRAIL_PROMPT,
    SOCRATIC_REFUSAL_PROMPT,
    EMERGENCY_RESPONSE_PROMPT,
)
from ai_engine.agents.tools import check_screen_time_goal, get_today_habits, get_emergency_contacts


# ---------------------------------------------------------------------------
# Estado do Grafo
# ---------------------------------------------------------------------------

class LumiaState(TypedDict):
    """Estado compartilhado entre os nós do grafo Lumia."""
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: int
    student_name: str
    age: int
    intent: Optional[Literal['safety_risk', 'academic_cheat', 'concept_question', 'habit_query', 'casual_chat']]
    safety_level: Literal['safe', 'warning', 'critical_danger']
    retrieved_context: List[str]
    habit_data: Optional[dict]
    generation: Optional[str]


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

def _get_llm(temperature: float = 0.4):
    """Retorna instância do Gemini Flash configurada via GOOGLE_API_KEY ou GEMINI_API_KEY."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from django.conf import settings
        api_key = getattr(settings, 'GOOGLE_API_KEY', '') or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY', '')
        api_key = api_key.strip().strip('\'"')
        return ChatGoogleGenerativeAI(
            model='gemini-2.5-flash',
            google_api_key=api_key,
            temperature=temperature,
        )
    except ImportError as exc:
        raise ImportError(
            'langchain-google-genai não instalado. '
            'Execute: pip install langchain-google-genai'
        ) from exc


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def _get_last_human_message(messages: List[BaseMessage]) -> Optional[str]:
    """Retorna o conteúdo da última mensagem humana."""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return msg.content if isinstance(msg.content, str) else str(msg.content)
    return None


# ---------------------------------------------------------------------------
# Nós do Grafo
# ---------------------------------------------------------------------------

def guardrail_node(state: LumiaState) -> dict:
    """
    Nó de segurança: classifica o nível de risco da mensagem.

    Analisa a última mensagem em busca de sinais de perigo
    (sextorsão, assédio, autolesão) antes de qualquer processamento.
    """
    last_message = _get_last_human_message(state['messages'])
    if not last_message:
        return {'safety_level': 'safe', 'intent': 'casual_chat'}

    llm = _get_llm(temperature=0.0)
    prompt = SAFETY_GUARDRAIL_PROMPT.format(message=last_message)

    response = llm.invoke(prompt)
    safety_text = response.content.strip().lower()

    if 'critical_danger' in safety_text:
        safety_level = 'critical_danger'
    elif 'warning' in safety_text:
        safety_level = 'warning'
    else:
        safety_level = 'safe'

    return {'safety_level': safety_level}


def intent_router_node(state: LumiaState) -> dict:
    """
    Nó de classificação de intenção.

    Classifica a mensagem em uma das 5 intenções para rotear
    ao nó de processamento adequado.
    """
    if state.get('safety_level') == 'critical_danger':
        return {'intent': 'safety_risk'}

    last_message = _get_last_human_message(state['messages'])
    if not last_message:
        return {'intent': 'casual_chat'}

    llm = _get_llm(temperature=0.0)
    prompt = INTENT_CLASSIFICATION_PROMPT.format(message=last_message)

    response = llm.invoke(prompt)
    intent_text = response.content.strip().lower()

    valid_intents = ['safety_risk', 'academic_cheat', 'concept_question', 'habit_query', 'casual_chat']
    intent = next((i for i in valid_intents if i in intent_text), 'casual_chat')

    # Warnings de segurança forçam tratamento como pergunta conceitual para ser cuidadoso
    if state.get('safety_level') == 'warning' and intent not in ('safety_risk', 'concept_question'):
        intent = 'concept_question'

    return {'intent': intent}


def rag_node(state: LumiaState) -> dict:
    """
    Nó de recuperação RAG com busca híbrida e reranking.

    Executa: MultiQueryRetriever -> EnsembleRetriever (ChromaDB+BM25) -> FlashRank.
    """
    last_message = _get_last_human_message(state['messages'])
    if not last_message:
        return {'retrieved_context': []}

    try:
        from ai_engine.rag.retriever import retrieve_and_rerank
        docs = retrieve_and_rerank(query=last_message, top_k=3, llm=_get_llm(temperature=0.3))
        context = [doc.page_content for doc in docs]
    except Exception as exc:
        print(f'[WARN] RAG falhou: {exc}')
        context = []

    return {'retrieved_context': context}


def habit_tool_node(state: LumiaState) -> dict:
    """
    Nó de consulta de hábitos e metas de tempo de tela.

    Invoca ferramentas Django para buscar dados personalizados do estudante.
    """
    user_id = state.get('user_id', 0)
    habit_data = {
        'screen_goal': check_screen_time_goal.invoke({'user_id': user_id}),
        'today_habits': get_today_habits.invoke({'user_id': user_id}),
    }
    return {'habit_data': habit_data}


def emergency_node(state: LumiaState) -> dict:
    """
    Nó de emergência: resposta acolhedora com recursos de apoio.

    Nunca culpabiliza o estudante. Sempre direciona para ajuda profissional.
    """
    llm = _get_llm(temperature=0.3)
    contacts = get_emergency_contacts.invoke({})
    context = f'Estudante em possível situação de risco. Recursos disponíveis: {contacts}'
    prompt = EMERGENCY_RESPONSE_PROMPT.format(context=context)

    response = llm.invoke(prompt)
    generation = response.content

    new_message = AIMessage(content=generation)
    return {'generation': generation, 'messages': [new_message]}


def socratic_refusal_node(state: LumiaState) -> dict:
    """
    Nó socrático: recusa gentil de fazer tarefas, com perguntas reflexivas.
    """
    last_message = _get_last_human_message(state['messages'])
    llm = _get_llm(temperature=0.5)
    prompt = SOCRATIC_REFUSAL_PROMPT.format(task=last_message or 'tarefa escolar')

    response = llm.invoke(prompt)
    generation = response.content

    new_message = AIMessage(content=generation)
    return {'generation': generation, 'messages': [new_message]}


def generation_node(state: LumiaState) -> dict:
    """
    Nó de geração: combina contexto RAG e dados de hábitos para resposta final.
    """
    retrieved_context = state.get('retrieved_context', [])
    habit_data = state.get('habit_data')

    # Monta contexto do estudante
    student_context = (
        f'Nome: {state.get("student_name", "Estudante")}\n'
        f'Idade: {state.get("age", 12)} anos'
    )
    if habit_data:
        student_context += f'\nDados de rotina: {habit_data}'

    # Monta contexto recuperado
    retrieved_str = (
        '\n---\n'.join(retrieved_context)
        if retrieved_context
        else 'Sem contexto específico disponível na base de conhecimento.'
    )

    system_prompt = LUMIA_SYSTEM_PROMPT.format(
        student_context=student_context,
        retrieved_context=retrieved_str,
    )

    llm = _get_llm(temperature=0.4)
    messages_to_send = [SystemMessage(content=system_prompt)] + list(state['messages'])

    response = llm.invoke(messages_to_send)
    generation = response.content

    new_message = AIMessage(content=generation)
    return {'generation': generation, 'messages': [new_message]}


def chitchat_node(state: LumiaState) -> dict:
    """
    Nó de conversa informal: mantém a persona Lumia sem RAG.
    """
    student_context = (
        f'Nome: {state.get("student_name", "Estudante")}, '
        f'Idade: {state.get("age", 12)} anos'
    )
    system_prompt = LUMIA_SYSTEM_PROMPT.format(
        student_context=student_context,
        retrieved_context='Sem contexto específico — conversa informal.',
    )

    llm = _get_llm(temperature=0.6)
    messages_to_send = [SystemMessage(content=system_prompt)] + list(state['messages'])

    response = llm.invoke(messages_to_send)
    generation = response.content

    new_message = AIMessage(content=generation)
    return {'generation': generation, 'messages': [new_message]}


# ---------------------------------------------------------------------------
# Roteamento Condicional
# ---------------------------------------------------------------------------

def route_after_intent(state: LumiaState) -> str:
    """Define o próximo nó com base na intenção classificada."""
    intent = state.get('intent', 'casual_chat')
    routing = {
        'safety_risk': 'emergency',
        'academic_cheat': 'socratic_refusal',
        'concept_question': 'rag',
        'habit_query': 'habit_tool',
        'casual_chat': 'chitchat',
    }
    return routing.get(intent, 'chitchat')


# ---------------------------------------------------------------------------
# Montagem do Grafo
# ---------------------------------------------------------------------------

def build_lumia_graph(use_memory: bool = True):
    """
    Constrói e compila o grafo LangGraph da Lumia.

    Args:
        use_memory: Se True, usa SqliteSaver para persistência de sessão.
    Returns:
        Grafo compilado pronto para invocar.
    """
    workflow = StateGraph(LumiaState)

    # Registra os nós
    workflow.add_node('guardrail', guardrail_node)
    workflow.add_node('intent_router', intent_router_node)
    workflow.add_node('rag', rag_node)
    workflow.add_node('habit_tool', habit_tool_node)
    workflow.add_node('emergency', emergency_node)
    workflow.add_node('socratic_refusal', socratic_refusal_node)
    workflow.add_node('generation', generation_node)
    workflow.add_node('chitchat', chitchat_node)

    # Ponto de entrada
    workflow.set_entry_point('guardrail')

    # Arestas fixas
    workflow.add_edge('guardrail', 'intent_router')

    # Aresta condicional: router -> nó específico
    workflow.add_conditional_edges(
        'intent_router',
        route_after_intent,
        {
            'emergency': 'emergency',
            'socratic_refusal': 'socratic_refusal',
            'rag': 'rag',
            'habit_tool': 'habit_tool',
            'chitchat': 'chitchat',
        },
    )

    # Após RAG e habit_tool, vai para geração
    workflow.add_edge('rag', 'generation')
    workflow.add_edge('habit_tool', 'generation')

    # Nós terminais
    workflow.add_edge('generation', END)
    workflow.add_edge('socratic_refusal', END)
    workflow.add_edge('chitchat', END)
    workflow.add_edge('emergency', END)

    # Compilacao com persistencia de sessao.
    # Prioridade: SqliteSaver > MemorySaver > sem persistencia
    if use_memory:
        # 1. SqliteSaver (pip install langgraph-checkpoint-sqlite)
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
            import sqlite3
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'data', 'lumia_sessions.db',
            )
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            conn = sqlite3.connect(db_path, check_same_thread=False)
            checkpointer = SqliteSaver(conn)
            print('[INFO] Persistencia: SqliteSaver')
            return workflow.compile(checkpointer=checkpointer)
        except ImportError:
            pass
        except Exception as exc:
            print(f'[WARN] SqliteSaver falhou: {exc}')

        # 2. MemorySaver (incluido no langgraph base)
        try:
            from langgraph.checkpoint.memory import MemorySaver
            checkpointer = MemorySaver()
            print('[INFO] Persistencia: MemorySaver (instale langgraph-checkpoint-sqlite para persistencia em disco)')
            return workflow.compile(checkpointer=checkpointer)
        except Exception as exc:
            print(f'[WARN] MemorySaver falhou: {exc}')

    return workflow.compile()


# Instância global do grafo (lazy init singleton)
_lumia_graph = None


def get_lumia_graph():
    """Retorna a instância global do grafo Lumia (singleton com lazy init)."""
    global _lumia_graph
    if _lumia_graph is None:
        _lumia_graph = build_lumia_graph(use_memory=True)
    return _lumia_graph
