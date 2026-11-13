"""
Interface de conexão com o banco de dados vetorial ChromaDB em português brasileiro.

Gerencia a inicialização do modelo de embeddings da Google (Gemini) e a instância
persistente do ChromaDB utilizada para busca vetorial densa por similaridade de cosseno.
"""
from __future__ import annotations

import os


def obter_modelo_embeddings():
    """
    Inicializa e retorna o modelo de geração de representações vetoriais (embeddings).

    Funcionamento:
      1. Tenta importar a biblioteca GoogleGenerativeAIEmbeddings do LangChain.
      2. Obtém a chave de API (GEMINI_API_KEY ou GOOGLE_API_KEY) das configurações Django ou do sistema.
      3. Instancia o modelo 'gemini-embedding-001' homologado na plataforma.
      4. Retorna o objeto pronto para converter textos em vetores numéricos de alta dimensão.

    Retorna:
        GoogleGenerativeAIEmbeddings: Instância configurada para vetorização semântica.
    """
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
    except ImportError as erro_import:
        raise ImportError(
            'Pacote langchain-google-genai não encontrado. '
            'Instale com: pip install langchain-google-genai'
        ) from erro_import

    from django.conf import settings
    chave_api = getattr(settings, 'GOOGLE_API_KEY', '') or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY', '')
    chave_api_limpa = chave_api.strip().strip('\'"')

    return GoogleGenerativeAIEmbeddings(
        model='gemini-embedding-001',
        google_api_key=chave_api_limpa,
    )


def obter_banco_vetorial(diretorio_persistencia: str = None, nome_colecao: str = None):
    """
    Inicializa ou recupera a instância do banco vetorial ChromaDB armazenada em disco.

    Funcionamento:
      1. Define o diretório de armazenamento e o nome da coleção a partir das configurações do Django.
      2. Conecta ao banco de dados SQLite interno do ChromaDB na pasta persistente.
      3. Atribui a função de embedding para cálculo automático de similaridade.
      4. Retorna a coleção Chroma pronta para operações de busca e inserção.

    Parâmetros:
        diretorio_persistencia (str, opcional): Caminho absoluto da pasta do banco de dados vetorial.
        nome_colecao (str, opcional): Nome da coleção no ChromaDB (padrão: lumenlab_docs).

    Retorna:
        Chroma: Objeto de armazenamento vetorial persistente.
    """
    try:
        from langchain_chroma import Chroma
    except ImportError:
        try:
            from langchain_community.vectorstores import Chroma
        except ImportError as erro_import:
            raise ImportError(
                'Biblioteca ChromaDB para LangChain não encontrada. '
                'Instale com: pip install langchain-chroma'
            ) from erro_import

    from django.conf import settings

    caminho_diretorio = diretorio_persistencia or getattr(settings, 'CHROMA_PERSIST_DIR', '/tmp/chroma_db')
    identificador_colecao = nome_colecao or getattr(settings, 'CHROMA_COLLECTION_NAME', 'lumenlab_docs')

    return Chroma(
        collection_name=identificador_colecao,
        embedding_function=obter_modelo_embeddings(),
        persist_directory=str(caminho_diretorio),
    )


def obter_recuperador_denso(limite_documentos: int = 10):
    """
    Cria um recuperador semântico (Retriever) baseado na proximidade vetorial por cosseno.

    Funcionamento:
      1. Obtém o banco vetorial ChromaDB persistido.
      2. Converte a coleção em um retriever com busca por similaridade semântica.
      3. Define a quantidade máxima de trechos candidatos a serem recuperados.

    Parâmetros:
        limite_documentos (int): Número máximo de chunks candidatos a retornar (padrão: 10).

    Retorna:
        VectorStoreRetriever: Recuperador semântico pronto para integração em pipelines LangChain.
    """
    banco_vetorial = obter_banco_vetorial()
    return banco_vetorial.as_retriever(
        search_type='similarity',
        search_kwargs={'k': limite_documentos},
    )


# Aliases para retrocompatibilidade
get_embeddings = obter_modelo_embeddings
get_vectorstore = obter_banco_vetorial
get_dense_retriever = obter_recuperador_denso
