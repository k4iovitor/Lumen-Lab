"""
Pipeline de recuperação híbrida para o chatbot Lumia.

Implementa busca híbrida combinando:
- ChromaDB (busca densa por similaridade semântica, peso 60%)
- BM25 (busca esparsa por palavras-chave, peso 40%)
- FlashRank (reranking cruzado para seleção dos top-k mais relevantes)
- MultiQueryRetriever (reescrita do prompt para robustez semântica)
"""
from __future__ import annotations

import os
from typing import List

from langchain_classic.retrievers import EnsembleRetriever, MultiQueryRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate


def _get_llm(temperature: float = 0.3):
    """Retorna LLM Gemini Flash para uso interno no retriever."""
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
        raise ImportError('langchain-google-genai necessário. pip install langchain-google-genai') from exc


def _get_vectorstore():
    """Importa e retorna o vectorstore ChromaDB."""
    from ai_engine.vectorstore.chroma_store import get_vectorstore
    return get_vectorstore()


def build_bm25_retriever(k: int = 10) -> BM25Retriever:
    """
    Constrói o retriever BM25 carregando todos os documentos do ChromaDB.

    O BM25 opera sobre o corpus completo armazenado no vectorstore,
    garantindo coerência com os documentos já indexados.

    Args:
        k: Número de documentos a retornar.
    Returns:
        Retriever BM25 configurado.
    """
    vectorstore = _get_vectorstore()
    collection = vectorstore._collection
    result = collection.get(include=['documents', 'metadatas'])

    documents = [
        Document(page_content=text, metadata=meta or {})
        for text, meta in zip(result['documents'], result['metadatas'])
        if text
    ]

    if not documents:
        raise ValueError('ChromaDB está vazio. Execute o script de ingestão primeiro.')

    bm25 = BM25Retriever.from_documents(documents)
    bm25.k = k
    return bm25


def build_hybrid_retriever(dense_k: int = 10, sparse_k: int = 10) -> EnsembleRetriever:
    """
    Constrói o retriever híbrido combinando ChromaDB (denso) e BM25 (esparso).

    Pesos:
    - ChromaDB (semântico): 60%
    - BM25 (lexical): 40%

    Args:
        dense_k: Número de docs do retriever denso.
        sparse_k: Número de docs do retriever esparso.
    Returns:
        EnsembleRetriever configurado.
    """
    from ai_engine.vectorstore.chroma_store import get_dense_retriever

    dense_retriever = get_dense_retriever(k=dense_k)
    bm25_retriever = build_bm25_retriever(k=sparse_k)

    return EnsembleRetriever(
        retrievers=[dense_retriever, bm25_retriever],
        weights=[0.6, 0.4],
    )


def rerank_documents(query: str, documents: List[Document], top_k: int = 3) -> List[Document]:
    """
    Rerankeia os documentos recuperados usando FlashRank (cross-encoder leve).

    Args:
        query: Consulta original do usuário.
        documents: Lista de documentos candidatos.
        top_k: Número de documentos a retornar após reranking.
    Returns:
        Top-k documentos ordenados por relevância.
    """
    if not documents:
        return []

    try:
        from flashrank import Ranker, RerankRequest
        from django.conf import settings

        cache_dir = getattr(settings, 'BASE_DIR', None)
        if cache_dir:
            model_dir = str(cache_dir / 'data' / 'flashrank_cache')
        else:
            model_dir = '/tmp/flashrank_cache'
        os.makedirs(model_dir, exist_ok=True)

        ranker = Ranker(
            model_name='ms-marco-TinyBERT-L-2-v2',
            cache_dir=model_dir,
        )

        passages = [
            {'id': i, 'text': doc.page_content, 'meta': doc.metadata}
            for i, doc in enumerate(documents)
        ]

        rerank_request = RerankRequest(query=query, passages=passages)
        results = ranker.rerank(rerank_request)

        reranked = []
        for result in results[:top_k]:
            original_doc = documents[result['id']]
            original_doc.metadata['rerank_score'] = result.get('score', 0.0)
            reranked.append(original_doc)

        return reranked

    except ImportError:
        print('[WARN] FlashRank não instalado. pip install flashrank. Usando fallback sem reranking.')
        return documents[:top_k]
    except Exception as exc:
        print(f'[WARN] FlashRank falhou ({exc}). Usando fallback sem reranking.')
        return documents[:top_k]


def _multiquery_prompt_template() -> PromptTemplate:
    """Constrói o PromptTemplate para o MultiQueryRetriever."""
    return PromptTemplate(
        input_variables=['question'],
        template=(
            'Você é um assistente que ajuda a reformular perguntas de adolescentes '
            'de 10 a 14 anos sobre segurança digital, inteligência artificial e redes sociais. '
            'Gere 3 versões alternativas da pergunta abaixo para melhorar a busca. '
            'Retorne apenas as 3 versões, uma por linha, sem numeração.\n\n'
            'Pergunta original: {question}'
        ),
    )


def build_multiquery_retriever(llm=None) -> MultiQueryRetriever:
    """
    Constrói o MultiQueryRetriever para reescrita robusta de consultas ambíguas.

    Usa o Gemini Flash para gerar variações da pergunta do usuário,
    expandindo termos coloquiais e adolescentes para vocabulário técnico.

    Args:
        llm: Instância do LLM. Se None, usa Gemini Flash.
    Returns:
        MultiQueryRetriever configurado sobre o retriever híbrido.
    """
    if llm is None:
        llm = _get_llm(temperature=0.3)

    base_retriever = build_hybrid_retriever()

    return MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm,
        prompt=_multiquery_prompt_template(),
    )


def retrieve_and_rerank(query: str, top_k: int = 3, llm=None) -> List[Document]:
    """
    Pipeline completo: MultiQuery -> Híbrido (ChromaDB + BM25) -> FlashRank.

    Função principal chamada pelo grafo LangGraph.

    Args:
        query: Pergunta do usuário.
        top_k: Documentos finais após reranking.
        llm: LLM para MultiQueryRetriever (opcional).
    Returns:
        Lista de documentos mais relevantes.
    """
    multiquery_retriever = build_multiquery_retriever(llm=llm)
    candidates = multiquery_retriever.invoke(query)

    # Remove duplicatas mantendo ordem de relevância
    seen: set[str] = set()
    unique_candidates: List[Document] = []
    for doc in candidates:
        key = doc.page_content[:100]
        if key not in seen:
            seen.add(key)
            unique_candidates.append(doc)

    return rerank_documents(query, unique_candidates, top_k=top_k)
