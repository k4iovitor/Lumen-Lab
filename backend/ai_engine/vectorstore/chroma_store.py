"""
Inicialização e acesso ao ChromaDB com embeddings do Google Gemini.

Fornece funções para obter o vectorstore persistente e o retriever
denso utilizado no pipeline de busca híbrida do chatbot Lumia.

Dependências externas (instalar via pip):
    pip install langchain-google-genai langchain-chroma
"""
from __future__ import annotations

import os


def get_embeddings():
    """Retorna o modelo de embeddings do Google Gemini (text-embedding-004)."""
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
    except ImportError as exc:
        raise ImportError(
            'langchain-google-genai não instalado. '
            'Execute: pip install langchain-google-genai'
        ) from exc

    from django.conf import settings
    api_key = getattr(settings, 'GOOGLE_API_KEY', '') or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY', '')
    api_key = api_key.strip().strip('\'"')

    return GoogleGenerativeAIEmbeddings(
        model='gemini-embedding-001',
        google_api_key=api_key,
    )


def get_vectorstore(persist_directory: str = None, collection_name: str = None):
    """
    Retorna o vectorstore ChromaDB persistente.

    Args:
        persist_directory: Caminho para o diretório de persistência do ChromaDB.
                           Se None, lê de settings.CHROMA_PERSIST_DIR.
        collection_name: Nome da coleção ChromaDB.
                         Se None, lê de settings.CHROMA_COLLECTION_NAME.
    Returns:
        Instância Chroma pronta para uso como retriever.
    """
    try:
        from langchain_chroma import Chroma
    except ImportError:
        try:
            from langchain_community.vectorstores import Chroma
        except ImportError as exc:
            raise ImportError(
                'langchain-chroma não instalado. '
                'Execute: pip install langchain-chroma'
            ) from exc

    from django.conf import settings

    persist_dir = persist_directory or getattr(settings, 'CHROMA_PERSIST_DIR', '/tmp/chroma_db')
    collection = collection_name or getattr(settings, 'CHROMA_COLLECTION_NAME', 'lumenlab_docs')

    return Chroma(
        collection_name=collection,
        embedding_function=get_embeddings(),
        persist_directory=persist_dir,
    )


def get_dense_retriever(k: int = 10):
    """
    Retorna o retriever denso baseado em ChromaDB.

    Args:
        k: Número de documentos a recuperar na busca por similaridade.
    Returns:
        Retriever ChromaDB configurado.
    """
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever(
        search_type='similarity',
        search_kwargs={'k': k},
    )
