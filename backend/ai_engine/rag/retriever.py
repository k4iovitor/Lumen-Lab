"""
Pipeline de recuperação híbrida e reranking para a assistente Lumia em português brasileiro.

Combina quatro estratégias complementares para máxima precisão na resposta socrática:
  1. MultiQueryRetriever: reescreve perguntas coloquiais de adolescentes em variações técnicas.
  2. EnsembleRetriever: busca híbrida combinando vetores densos (ChromaDB 60%) e palavras-chave (BM25 40%).
  3. Deduplicação semântica de trechos redundantes.
  4. FlashRank (Cross-Encoder): reranking leve local via TinyBERT para selecionar o top-3 ideal.
"""
from __future__ import annotations

import os
from typing import List

from langchain_classic.retrievers import EnsembleRetriever, MultiQueryRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate


def obter_modelo_gemini(temperatura: float = 0.3):
    """
    Inicializa o modelo de linguagem Gemini Flash para tarefas auxiliares de recuperação e reescrita.

    Funcionamento:
      1. Lê a chave de API cadastrada nas configurações do Django.
      2. Instancia o ChatGoogleGenerativeAI apontando para o modelo 'gemini-2.5-flash'.
      3. Define temperatura baixa para geração consistente de variações de busca.

    Parâmetros:
        temperatura (float): Grau de variabilidade nas respostas do LLM (padrão: 0.3).

    Retorna:
        ChatGoogleGenerativeAI: Cliente do Gemini configurado.
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
        raise ImportError('Biblioteca langchain-google-genai necessária. Execute: pip install langchain-google-genai') from erro_import


def obter_banco_vetorial_local():
    """
    Recupera a coleção local do ChromaDB contendo os documentos indexados.

    Retorna:
        Chroma: Objeto de armazenamento vetorial persistido.
    """
    from ai_engine.vectorstore.chroma_store import obter_banco_vetorial
    return obter_banco_vetorial()


def construir_recuperador_bm25(limite_documentos: int = 10) -> BM25Retriever:
    """
    Constrói o recuperador esparso BM25 carregando o corpus de documentos do ChromaDB.

    Funcionamento passo a passo:
      1. Obtém a coleção bruta de documentos e metadados persistida no ChromaDB.
      2. Converte os registros em instâncias de Document do LangChain.
      3. Valida se o banco não está vazio; caso esteja, dispara alerta para executar a ingestão.
      4. Instancia o BM25Retriever indexando a frequência invertida de palavras-chave (TF-IDF aprimorado).
      5. Configura a quantidade de documentos a retornar (k).

    Parâmetros:
        limite_documentos (int): Número de documentos candidatos com maiores scores de correspondência exata.

    Retorna:
        BM25Retriever: Recuperador lexical baseado em correspondência de termos.
    """
    banco_vetorial = obter_banco_vetorial_local()
    colecao = banco_vetorial._collection
    resultado_bruto = colecao.get(include=['documents', 'metadatas'])

    lista_documentos = [
        Document(page_content=texto, metadata=metadados or {})
        for texto, metadados in zip(resultado_bruto['documents'], resultado_bruto['metadatas'])
        if texto
    ]

    if not lista_documentos:
        raise ValueError('O banco ChromaDB está vazio. Execute o script de ingestão de PDFs primeiro.')

    recuperador_bm25 = BM25Retriever.from_documents(lista_documentos)
    recuperador_bm25.k = limite_documentos
    return recuperador_bm25


def construir_recuperador_hibrido(quantidade_denso: int = 10, quantidade_esparso: int = 10) -> EnsembleRetriever:
    """
    Monta o recuperador híbrido que combina busca vetorial semântica e busca lexical.

    Funcionamento:
      1. Cria o recuperador denso (ChromaDB) com peso de 60% (0.6) para apreensão do contexto e significado.
      2. Cria o recuperador esparso (BM25) com peso de 40% (0.4) para busca por jargões e palavras-chave.
      3. Unifica os dois recuperadores através do EnsembleRetriever com fusão ponderada de posições (RRF).

    Parâmetros:
        quantidade_denso (int): Número de trechos candidatos da busca semântica.
        quantidade_esparso (int): Número de trechos candidatos da busca por palavras-chave.

    Retorna:
        EnsembleRetriever: Recuperador integrado com fusão híbrida.
    """
    from ai_engine.vectorstore.chroma_store import obter_recuperador_denso

    recuperador_denso = obter_recuperador_denso(limite_documentos=quantidade_denso)
    recuperador_esparso = construir_recuperador_bm25(limite_documentos=quantidade_esparso)

    return EnsembleRetriever(
        retrievers=[recuperador_denso, recuperador_esparso],
        weights=[0.6, 0.4],
    )


def reranquear_documentos(consulta_usuario: str, documentos_candidatos: List[Document], limite_k: int = 3) -> List[Document]:
    """
    Reclassifica os documentos candidatos utilizando o modelo leve de Cross-Encoder FlashRank.

    Funcionamento passo a passo:
      1. Se a lista de candidatos for vazia, retorna imediatamente uma lista vazia.
      2. Inicializa o Ranker da biblioteca FlashRank apontando para o modelo 'ms-marco-TinyBERT-L-2-v2'
         salvo no cache local (evita qualquer latência de download da internet).
      3. Transforma os documentos candidatos em passagens estruturadas com identificador e texto.
      4. Dispara a reavaliação de relevância mútua entre a consulta e cada passagem.
      5. Ordena os documentos e anexa o 'rerank_score' aos metadados de cada chunk.
      6. Retorna apenas os top-k trechos com maior índice de aderência à dúvida do estudante.

    Parâmetros:
        consulta_usuario (str): Dúvida original formulada pelo estudante.
        documentos_candidatos (List[Document]): Lista de trechos pré-selecionados pela busca híbrida.
        limite_k (int): Quantidade final de documentos a serem entregues à assistente (padrão: 3).

    Retorna:
        List[Document]: Lista refinada contendo os trechos mais estritamente relevantes.
    """
    if not documentos_candidatos:
        return []

    try:
        from flashrank import Ranker, RerankRequest
        from django.conf import settings

        diretorio_raiz = getattr(settings, 'BASE_DIR', None)
        if diretorio_raiz:
            diretorio_modelo = str(diretorio_raiz / 'data' / 'flashrank_cache')
        else:
            diretorio_modelo = '/tmp/flashrank_cache'
        os.makedirs(diretorio_modelo, exist_ok=True)

        classificador_rerank = Ranker(
            model_name='ms-marco-TinyBERT-L-2-v2',
            cache_dir=diretorio_modelo,
        )

        passagens_formatadas = [
            {'id': indice, 'text': doc.page_content, 'meta': doc.metadata}
            for indice, doc in enumerate(documentos_candidatos)
        ]

        requisicao_rerank = RerankRequest(query=consulta_usuario, passages=passagens_formatadas)
        resultados_reordenados = classificador_rerank.rerank(requisicao_rerank)

        documentos_finais = []
        for item in resultados_reordenados[:limite_k]:
            documento_original = documentos_candidatos[item['id']]
            documento_original.metadata['rerank_score'] = item.get('score', 0.0)
            documentos_finais.append(documento_original)

        return documentos_finais

    except ImportError:
        print('[AVISO] FlashRank não instalado. Usando fallback de ordenação original.')
        return documentos_candidatos[:limite_k]
    except Exception as erro_execucao:
        print(f'[AVISO] Falha no FlashRank ({erro_execucao}). Usando fallback de ordenação original.')
        return documentos_candidatos[:limite_k]


def _montar_modelo_prompt_multiquery() -> PromptTemplate:
    """
    Gera o template de prompt para instruir o Gemini a expandir perguntas de adolescentes.

    Retorna:
        PromptTemplate: Modelo de prompt configurado para o MultiQueryRetriever.
    """
    return PromptTemplate(
        input_variables=['question'],
        template=(
            'Você é um assistente educacional que ajuda a reformular dúvidas de adolescentes '
            'de 10 a 14 anos sobre segurança digital, inteligência artificial e redes sociais. '
            'Gere 3 versões alternativas da dúvida abaixo para maximizar o alcance da busca vetorial. '
            'Retorne apenas as 3 versões, uma por linha, sem numeração ou texto adicional.\n\n'
            'Dúvida original: {question}'
        ),
    )


def construir_recuperador_multiquery(modelo_llm=None) -> MultiQueryRetriever:
    """
    Cria o recuperador MultiQuery que amplia a cobertura semântica de dúvidas ambíguas.

    Funcionamento:
      1. Se o modelo LLM não for fornecido, inicializa o Gemini Flash padrão.
      2. Constrói o recuperador híbrido (ChromaDB + BM25).
      3. Acopla o gerador de consultas alternativas ao recuperador híbrido.

    Parâmetros:
        modelo_llm (opcional): Instância do modelo de linguagem generativa.

    Retorna:
        MultiQueryRetriever: Recuperador inteligente com expansão de consultas.
    """
    if modelo_llm is None:
        modelo_llm = obter_modelo_gemini(temperatura=0.3)

    recuperador_base = construir_recuperador_hibrido()

    return MultiQueryRetriever.from_llm(
        retriever=recuperador_base,
        llm=modelo_llm,
        prompt=_montar_modelo_prompt_multiquery(),
    )


def recuperar_e_reranquear(consulta_usuario: str, limite_k: int = 3, modelo_llm=None) -> List[Document]:
    """
    Executa o fluxo completo do pipeline RAG:
      MultiQuery (3 variações) -> Busca Híbrida (Chroma + BM25) -> Deduplicação -> Reranking (FlashRank).

    Funcionamento passo a passo:
      1. Gera as variações semânticas da dúvida do estudante.
      2. Coleta todos os candidatos recuperados da busca densa e da busca esparsa.
      3. Remove trechos duplicados ou sobrepostos mantendo a precedência dos primeiros 100 caracteres.
      4. Submete os trechos únicos ao modelo Cross-Encoder FlashRank.
      5. Retorna a lista final com os 3 trechos mais precisos para apoiar a resposta socrática da Lumia.

    Parâmetros:
        consulta_usuario (str): Texto da pergunta enviada pelo estudante.
        limite_k (int): Quantidade final de trechos a serem selecionados.
        modelo_llm (opcional): Instância de LLM para reescrita de prompt.

    Retorna:
        List[Document]: Lista dos melhores trechos documentais encontrados.
    """
    recuperador_multiquery = construir_recuperador_multiquery(modelo_llm=modelo_llm)
    candidatos_brutos = recuperador_multiquery.invoke(consulta_usuario)

    # Deduplicação baseada nos primeiros 100 caracteres do texto
    trechos_vistos: set[str] = set()
    candidatos_unicos: List[Document] = []
    for doc in candidatos_brutos:
        chave_identificadora = doc.page_content[:100]
        if chave_identificadora not in trechos_vistos:
            trechos_vistos.add(chave_identificadora)
            candidatos_unicos.append(doc)

    return reranquear_documentos(consulta_usuario, candidatos_unicos, limite_k=limite_k)


# Aliases para compatibilidade retroativa
_get_llm = obter_modelo_gemini
_get_vectorstore = obter_banco_vetorial_local
build_bm25_retriever = construir_recuperador_bm25
build_hybrid_retriever = construir_recuperador_hibrido
rerank_documents = reranquear_documentos
build_multiquery_retriever = construir_recuperador_multiquery
retrieve_and_rerank = recuperar_e_reranquear
