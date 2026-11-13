"""
Grafo computacional LangGraph do chatbot Lumia em português brasileiro.

Orquestra o fluxo de raciocínio, guardrails de segurança, classificação de intenções,
recuperação de contexto RAG e geração socrática para estudantes de 10 a 14 anos.

Arquitetura do Grafo:
  Entrada do Estudante
           │
           ▼
    [Guardião de Segurança]
           │
           ▼
    [Roteador de Intenções] ──────┬───────────────┬──────────────┬──────────────┐
           │                      │               │              │              │
           ▼                      ▼               ▼              ▼              ▼
     [Emergência]         [Recusa Socrática]    [RAG]     [Hábitos]   [Conversa Informal]
           │                      │               │              │              │
           │                      │               ▼              ▼              │
           │                      │            [Geração Socrática]              │
           │                      │                    │                        │
           └──────────────────────┴────────────────────┴────────────────────────┴──► Resposta Final
"""
from __future__ import annotations

import os
from typing import Annotated, List, Literal, Optional, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from ai_engine.agents.prompts import (
    PROMPT_SISTEMA_LUMIA,
    PROMPT_CLASSIFICACAO_INTENCAO,
    PROMPT_GUARDIAO_SEGURANCA,
    PROMPT_RECUSA_SOCRATICA,
    PROMPT_RESPOSTA_EMERGENCIA,
)
from ai_engine.agents.tools import (
    consultar_meta_tempo_tela,
    obter_habitos_hoje,
    obter_contatos_emergencia,
)


# ---------------------------------------------------------------------------
# Estado do Grafo
# ---------------------------------------------------------------------------

class EstadoLumia(TypedDict, total=False):
    """
    Estado estruturado compartilhado entre todos os nós de processamento do grafo Lumia.

    Campos em português:
        mensagens: Histórico acumulado de mensagens da conversa (HumanMessage e AIMessage).
        id_usuario: Chave primária do usuário no Django.
        nome_estudante: Primeiro nome ou apelido do estudante para saudação personalizada.
        idade: Idade calculada do estudante para calibrar a linguagem pedagógica.
        intencao: Categoria de intenção classificada pelo modelo de roteamento.
        nivel_seguranca: Nível de risco da mensagem ('seguro', 'alerta', 'perigo_critico').
        contexto_recuperado: Trechos factuais obtidos da base de conhecimento via RAG.
        dados_habito: Dados de agenda e tempo de tela retornados pelas ferramentas.
        geracao: Resposta socrática final elaborada pela assistente.
    """
    mensagens: Annotated[List[BaseMessage], add_messages]
    id_usuario: int
    nome_estudante: str
    idade: int
    intencao: Optional[Literal['risco_seguranca', 'cola_academica', 'pergunta_conceitual', 'consulta_habito', 'conversa_casual',
                               'safety_risk', 'academic_cheat', 'concept_question', 'habit_query', 'casual_chat']]
    nivel_seguranca: Literal['seguro', 'alerta', 'perigo_critico', 'safe', 'warning', 'critical_danger']
    contexto_recuperado: List[str]
    dados_habito: Optional[dict]
    geracao: Optional[str]

    # Campos de compatibilidade para código legado
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: int
    student_name: str
    age: int
    intent: Optional[str]
    safety_level: str
    retrieved_context: List[str]
    habit_data: Optional[dict]
    generation: Optional[str]


# ---------------------------------------------------------------------------
# Inicialização do Modelo de Linguagem (LLM)
# ---------------------------------------------------------------------------

def obter_modelo_linguagem(temperatura: float = 0.4):
    """
    Instancia o modelo de linguagem Gemini 2.5 Flash com chave de API e temperatura definidas.

    Funcionamento:
      1. Lê a chave de API de settings.GOOGLE_API_KEY ou do ambiente (.env).
      2. Configura a temperatura (0.0 para decisões de segurança; 0.4 para socrático).
      3. Retorna o cliente LangChain ChatGoogleGenerativeAI pronto para invocação.

    Parâmetros:
        temperatura (float): Controle de criatividade estocástica do modelo.

    Retorna:
        ChatGoogleGenerativeAI: Instância configurada do LLM.
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from django.conf import settings
        chave_api = getattr(settings, 'GOOGLE_API_KEY', '') or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY', '')
        chave_api_limpa = chave_api.strip().strip('\'"')
        return ChatGoogleGenerativeAI(
            model='gemini-2.5-flash',
            google_api_key=chave_api_limpa,
            temperature=temperatura,
        )
    except ImportError as erro_import:
        raise ImportError(
            'Biblioteca langchain-google-genai não encontrada. '
            'Instale com: pip install langchain-google-genai'
        ) from erro_import


# ---------------------------------------------------------------------------
# Funções Utilitárias de Leitura do Histórico
# ---------------------------------------------------------------------------

def obter_ultima_mensagem_humana(mensagens: List[BaseMessage]) -> Optional[str]:
    """
    Percorre o histórico de mensagens em ordem reversa para extrair o texto da última fala do usuário.

    Parâmetros:
        mensagens: Lista de instâncias BaseMessage.

    Retorna:
        Optional[str]: Conteúdo textual da mensagem ou None caso ausente.
    """
    for msg in reversed(mensagens):
        if isinstance(msg, HumanMessage):
            return msg.content if isinstance(msg.content, str) else str(msg.content)
    return None


# ---------------------------------------------------------------------------
# Nós do Grafo LangGraph
# ---------------------------------------------------------------------------

def no_guardiao_seguranca(estado: EstadoLumia) -> dict:
    """
    Nó de Segurança e Guardrail: Avalia riscos e proteção do menor antes de qualquer resposta.

    Funcionamento passo a passo:
      1. Recupera o histórico de mensagens procurando a última interação do estudante.
      2. Invoca o Gemini com temperatura zero utilizando o PROMPT_GUARDIAO_SEGURANCA.
      3. Identifica sinais críticos de abuso, extorsão, assédio ou autolesão.
      4. Atualiza o estado com o nível de segurança ('seguro', 'alerta' ou 'perigo_critico').

    Parâmetros:
        estado (EstadoLumia): Estado compartilhado do grafo.

    Retorna:
        dict: Dicionário de mutação com o nível de segurança avaliado.
    """
    lista_mensagens = estado.get('mensagens') or estado.get('messages', [])
    ultima_mensagem = obter_ultima_mensagem_humana(lista_mensagens)
    if not ultima_mensagem:
        return {'nivel_seguranca': 'seguro', 'intencao': 'conversa_casual', 'safety_level': 'safe', 'intent': 'casual_chat'}

    modelo_seguro = obter_modelo_linguagem(temperatura=0.0)
    prompt_seguranca = PROMPT_GUARDIAO_SEGURANCA.format(mensagem=ultima_mensagem)

    resposta_modelo = modelo_seguro.invoke(prompt_seguranca)
    texto_seguranca = resposta_modelo.content.strip().lower()

    if 'perigo_critico' in texto_seguranca or 'critical_danger' in texto_seguranca:
        nivel_seguranca = 'perigo_critico'
        nivel_seguranca_legado = 'critical_danger'
    elif 'alerta' in texto_seguranca or 'warning' in texto_seguranca:
        nivel_seguranca = 'alerta'
        nivel_seguranca_legado = 'warning'
    else:
        nivel_seguranca = 'seguro'
        nivel_seguranca_legado = 'safe'

    return {
        'nivel_seguranca': nivel_seguranca,
        'safety_level': nivel_seguranca_legado,
    }


def no_roteador_intencao(estado: EstadoLumia) -> dict:
    """
    Nó Classificador de Intenção: Determina a rota pedagógica da dúvida do estudante.

    Funcionamento:
      1. Se o Guardrail apontou 'perigo_critico', desvia imediatamente para emergência.
      2. Caso contrário, submete o texto ao classificador de intenção.
      3. Classifica a mensagem em: pergunta_conceitual, consulta_habito, cola_academica ou conversa_casual.

    Parâmetros:
        estado (EstadoLumia): Estado compartilhado.

    Retorna:
        dict: Dicionário atualizando o campo 'intencao'.
    """
    nivel = estado.get('nivel_seguranca') or estado.get('safety_level')
    if nivel in ('perigo_critico', 'critical_danger'):
        return {'intencao': 'risco_seguranca', 'intent': 'safety_risk'}

    lista_mensagens = estado.get('mensagens') or estado.get('messages', [])
    ultima_mensagem = obter_ultima_mensagem_humana(lista_mensagens)
    if not ultima_mensagem:
        return {'intencao': 'conversa_casual', 'intent': 'casual_chat'}

    modelo_classificador = obter_modelo_linguagem(temperatura=0.0)
    prompt_intencao = PROMPT_CLASSIFICACAO_INTENCAO.format(mensagem=ultima_mensagem)

    resposta_modelo = modelo_classificador.invoke(prompt_intencao)
    texto_intencao = resposta_modelo.content.strip().lower()

    # Mapeamento com tolerância a múltiplos sinônimos
    if 'risco' in texto_intencao or 'safety' in texto_intencao:
        intencao_definida = 'risco_seguranca'
    elif 'cola' in texto_intencao or 'cheat' in texto_intencao:
        intencao_definida = 'cola_academica'
    elif 'conceito' in texto_intencao or 'concept' in texto_intencao:
        intencao_definida = 'pergunta_conceitual'
    elif 'habito' in texto_intencao or 'habit' in texto_intencao:
        intencao_definida = 'consulta_habito'
    else:
        intencao_definida = 'conversa_casual'

    # Mapeamento para chaves em inglês para manter o roteador funcional
    mapeamento_legado = {
        'risco_seguranca': 'safety_risk',
        'cola_academica': 'academic_cheat',
        'pergunta_conceitual': 'concept_question',
        'consulta_habito': 'habit_query',
        'conversa_casual': 'casual_chat',
    }

    return {
        'intencao': intencao_definida,
        'intent': mapeamento_legado.get(intencao_definida, 'casual_chat'),
    }


def no_recuperador_rag(estado: EstadoLumia) -> dict:
    """
    Nó RAG: Executa a busca vetorial híbrida e o reranking dos relatórios pedagógicos.

    Funcionamento:
      1. Extrai a dúvida do estudante.
      2. Invoca o pipeline recuperar_e_reranquear() (MultiQuery + ChromaDB + BM25 + FlashRank).
      3. Extrai o conteúdo dos 3 chunks mais relevantes.
      4. Armazena a lista de trechos em 'contexto_recuperado'.

    Parâmetros:
        estado (EstadoLumia): Estado atual.

    Retorna:
        dict: Chunks factuais prontos para guiar a resposta socrática.
    """
    from ai_engine.rag.retriever import recuperar_e_reranquear

    lista_mensagens = estado.get('mensagens') or estado.get('messages', [])
    ultima_mensagem = obter_ultima_mensagem_humana(lista_mensagens)
    if not ultima_mensagem:
        return {'contexto_recuperado': [], 'retrieved_context': []}

    documentos_recuperados = recuperar_e_reranquear(ultima_mensagem, limite_k=3)
    textos_contexto = [doc.page_content for doc in documentos_recuperados]

    return {
        'contexto_recuperado': textos_contexto,
        'retrieved_context': textos_contexto,
    }


def no_ferramentas_habito(estado: EstadoLumia) -> dict:
    """
    Nó de Hábitos: Invoca as ferramentas Django para ler hábitos e limites de tempo de tela.

    Funcionamento:
      1. Obtém o id_usuario do estudante.
      2. Executa as funções obter_habitos_hoje() e consultar_meta_tempo_tela().
      3. Consolida os dados em um dicionário estruturado.

    Parâmetros:
        estado (EstadoLumia): Estado atual.

    Retorna:
        dict: Dicionário contendo dados reais de rotina do estudante.
    """
    id_usuario = estado.get('id_usuario') or estado.get('user_id', 1)

    try:
        dados_habitos = obter_habitos_hoje.invoke({'id_usuario': id_usuario})
    except Exception:
        dados_habitos = []

    try:
        dados_meta = consultar_meta_tempo_tela.invoke({'id_usuario': id_usuario})
    except Exception:
        dados_meta = {}

    dados_consolidados = {
        'habitos_hoje': dados_habitos,
        'meta_tempo_tela': dados_meta,
    }

    return {
        'dados_habito': dados_consolidados,
        'habit_data': dados_consolidados,
    }


def no_resposta_emergencia(estado: EstadoLumia) -> dict:
    """
    Nó de Emergência: Emite acolhimento imediato e fornece os canais oficiais de denúncia e apoio.

    Parâmetros:
        estado (EstadoLumia): Estado atual.

    Retorna:
        dict: Resposta empática com contatos do SaferNet, CVV 188 e Disque 100.
    """
    lista_mensagens = estado.get('mensagens') or estado.get('messages', [])
    ultima_mensagem = obter_ultima_mensagem_humana(lista_mensagens) or 'Situação de risco informada.'

    modelo_emergencia = obter_modelo_linguagem(temperatura=0.2)
    prompt_emergencia = PROMPT_RESPOSTA_EMERGENCIA.format(contexto=ultima_mensagem)

    resposta = modelo_emergencia.invoke(prompt_emergencia)
    texto_gerado = resposta.content

    nova_mensagem = AIMessage(content=texto_gerado)
    return {
        'geracao': texto_gerado,
        'generation': texto_gerado,
        'mensagens': [nova_mensagem],
        'messages': [nova_mensagem],
    }


def no_recusa_socratica(estado: EstadoLumia) -> dict:
    """
    Nó de Recusa Pedagógica: Converte tentativas de cola escolar em perguntas reflexivas.

    Parâmetros:
        estado (EstadoLumia): Estado atual.

    Retorna:
        dict: 2 a 3 perguntas socráticas formuladas para guiar o estudante.
    """
    lista_mensagens = estado.get('mensagens') or estado.get('messages', [])
    tarefa_estudante = obter_ultima_mensagem_humana(lista_mensagens) or 'exercício escolar'

    modelo_recusa = obter_modelo_linguagem(temperatura=0.4)
    prompt_recusa = PROMPT_RECUSA_SOCRATICA.format(tarefa=tarefa_estudante)

    resposta = modelo_recusa.invoke(prompt_recusa)
    texto_gerado = resposta.content

    nova_mensagem = AIMessage(content=texto_gerado)
    return {
        'geracao': texto_gerado,
        'generation': texto_gerado,
        'mensagens': [nova_mensagem],
        'messages': [nova_mensagem],
    }


def no_geracao_socratica(estado: EstadoLumia) -> dict:
    """
    Nó de Geração Socrática: Formula a resposta pedagógica principal fundamentada nas fontes.

    Funcionamento:
      1. Prepara o contexto personalizado do estudante (nome e idade).
      2. Concatena os trechos de fontes RAG ou dados de hábitos.
      3. Injeta o PROMPT_SISTEMA_LUMIA como mensagem de sistema.
      4. Invoca o Gemini para gerar uma resposta com perguntas instigantes ao final.

    Parâmetros:
        estado (EstadoLumia): Estado consolidado.

    Retorna:
        dict: Resposta pedagógica pronta para streaming SSE.
    """
    nome_aluno = estado.get('nome_estudante') or estado.get('student_name', 'Estudante')
    idade_aluno = estado.get('idade') or estado.get('age', 12)
    contexto_estudante = f'Nome: {nome_aluno}, Idade: {idade_aluno} anos'

    trechos = estado.get('contexto_recuperado') or estado.get('retrieved_context', [])
    if trechos:
        contexto_factual = '\n---\n'.join(trechos)
    elif estado.get('dados_habito') or estado.get('habit_data'):
        contexto_factual = f'Dados da Rotina do Estudante: {estado.get("dados_habito") or estado.get("habit_data")}'
    else:
        contexto_factual = 'Sem contexto específico. Aplique princípios socráticos gerais.'

    prompt_sistema = PROMPT_SISTEMA_LUMIA.format(
        contexto_estudante=contexto_estudante,
        contexto_recuperado=contexto_factual,
        student_context=contexto_estudante,
        retrieved_context=contexto_factual,
    )

    modelo_socratica = obter_modelo_linguagem(temperatura=0.4)
    historico = estado.get('mensagens') or estado.get('messages', [])
    mensagens_para_envio = [SystemMessage(content=prompt_sistema)] + list(historico)

    resposta = modelo_socratica.invoke(mensagens_para_envio)
    texto_gerado = resposta.content

    nova_mensagem = AIMessage(content=texto_gerado)
    return {
        'geracao': texto_gerado,
        'generation': texto_gerado,
        'mensagens': [nova_mensagem],
        'messages': [nova_mensagem],
    }


def no_conversa_informal(estado: EstadoLumia) -> dict:
    """
    Nó de Conversa Casual: Responde com cordialidade mantendo a persona da Lumia sem acionar RAG.

    Parâmetros:
        estado (EstadoLumia): Estado atual.

    Retorna:
        dict: Resposta amigável e descontraída.
    """
    nome_aluno = estado.get('nome_estudante') or estado.get('student_name', 'Estudante')
    idade_aluno = estado.get('idade') or estado.get('age', 12)
    contexto_estudante = f'Nome: {nome_aluno}, Idade: {idade_aluno} anos'

    prompt_sistema = PROMPT_SISTEMA_LUMIA.format(
        contexto_estudante=contexto_estudante,
        contexto_recuperado='Conversa informal sem necessidade de dados técnicos.',
        student_context=contexto_estudante,
        retrieved_context='Conversa informal.',
    )

    modelo_casual = obter_modelo_linguagem(temperatura=0.6)
    historico = estado.get('mensagens') or estado.get('messages', [])
    mensagens_para_envio = [SystemMessage(content=prompt_sistema)] + list(historico)

    resposta = modelo_casual.invoke(mensagens_para_envio)
    texto_gerado = resposta.content

    nova_mensagem = AIMessage(content=texto_gerado)
    return {
        'geracao': texto_gerado,
        'generation': texto_gerado,
        'mensagens': [nova_mensagem],
        'messages': [nova_mensagem],
    }


# ---------------------------------------------------------------------------
# Função de Roteamento Condicional
# ---------------------------------------------------------------------------

def rotear_apos_intencao(estado: EstadoLumia) -> str:
    """
    Mapeia a intenção classificada para o nó de destino no grafo.

    Parâmetros:
        estado (EstadoLumia): Estado com o campo 'intencao' preenchido.

    Retorna:
        str: Identificador do nó de destino.
    """
    intencao = estado.get('intencao') or estado.get('intent', 'conversa_casual')
    tabela_rotas = {
        'risco_seguranca': 'emergencia',
        'safety_risk': 'emergencia',
        'cola_academica': 'recusa_socratica',
        'academic_cheat': 'recusa_socratica',
        'pergunta_conceitual': 'rag',
        'concept_question': 'rag',
        'consulta_habito': 'ferramenta_habito',
        'habit_query': 'ferramenta_habito',
        'conversa_casual': 'conversa_informal',
        'casual_chat': 'conversa_informal',
    }
    return tabela_rotas.get(intencao, 'conversa_informal')


# ---------------------------------------------------------------------------
# Montagem e Compilação do Grafo LangGraph
# ---------------------------------------------------------------------------

def construir_grafo_lumia(usar_memoria: bool = True):
    """
    Constrói a topologia do grafo de agentes LangGraph e anexa o checkpointer de persistência.

    Parâmetros:
        usar_memoria (bool): Se verdadeiro, inicializa persistência de sessão SQLite.

    Retorna:
        CompiledStateGraph: Grafo executável pronto para chamadas .invoke().
    """
    fluxo = StateGraph(EstadoLumia)

    # Registro de todos os nós de processamento
    fluxo.add_node('guardiao', no_guardiao_seguranca)
    fluxo.add_node('roteador_intencao', no_roteador_intencao)
    fluxo.add_node('rag', no_recuperador_rag)
    fluxo.add_node('ferramenta_habito', no_ferramentas_habito)
    fluxo.add_node('emergencia', no_resposta_emergencia)
    fluxo.add_node('recusa_socratica', no_recusa_socratica)
    fluxo.add_node('geracao_socratica', no_geracao_socratica)
    fluxo.add_node('conversa_informal', no_conversa_informal)

    # Ponto de entrada padrão
    fluxo.set_entry_point('guardiao')

    # Arestas fixas e condicionais
    fluxo.add_edge('guardiao', 'roteador_intencao')

    fluxo.add_conditional_edges(
        'roteador_intencao',
        rotear_apos_intencao,
        {
            'emergencia': 'emergencia',
            'recusa_socratica': 'recusa_socratica',
            'rag': 'rag',
            'ferramenta_habito': 'ferramenta_habito',
            'conversa_informal': 'conversa_informal',
        },
    )

    fluxo.add_edge('rag', 'geracao_socratica')
    fluxo.add_edge('ferramenta_habito', 'geracao_socratica')

    # Nós terminais
    fluxo.add_edge('geracao_socratica', END)
    fluxo.add_edge('recusa_socratica', END)
    fluxo.add_edge('conversa_informal', END)
    fluxo.add_edge('emergencia', END)

    if usar_memoria:
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
            import sqlite3
            caminho_banco = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'data', 'lumia_sessions.db',
            )
            os.makedirs(os.path.dirname(caminho_banco), exist_ok=True)
            conexao = sqlite3.connect(caminho_banco, check_same_thread=False)
            salvador_sqlite = SqliteSaver(conexao)
            return fluxo.compile(checkpointer=salvador_sqlite)
        except Exception as erro_sqlite:
            print(f'[AVISO] SqliteSaver não disponível ({erro_sqlite}). Usando MemorySaver.')

        try:
            from langgraph.checkpoint.memory import MemorySaver
            return fluxo.compile(checkpointer=MemorySaver())
        except Exception:
            pass

    return fluxo.compile()


# Instância global do grafo (Padrão Singleton Lazy Init)
_instancia_grafo_lumia = None


def obter_grafo_lumia():
    """Retorna a instância única do grafo compilado da Lumia."""
    global _instancia_grafo_lumia
    if _instancia_grafo_lumia is None:
        _instancia_grafo_lumia = construir_grafo_lumia(usar_memoria=True)
    return _instancia_grafo_lumia


# Aliases para compatibilidade retroativa
LumiaState = EstadoLumia
_get_llm = obter_modelo_linguagem
_get_last_human_message = obter_ultima_mensagem_humana
guardrail_node = no_guardiao_seguranca
intent_router_node = no_roteador_intencao
rag_node = no_recuperador_rag
habit_tool_node = no_ferramentas_habito
emergency_node = no_resposta_emergencia
socratic_refusal_node = no_recusa_socratica
generation_node = no_geracao_socratica
chitchat_node = no_conversa_informal
route_after_intent = rotear_apos_intencao
build_lumia_graph = construir_grafo_lumia
get_lumia_graph = obter_grafo_lumia
