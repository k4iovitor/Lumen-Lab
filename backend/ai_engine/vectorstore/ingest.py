"""
Script de ingestão de documentos PDF no ChromaDB.

Carrega os relatórios técnico-pedagógicos do diretório ai_engine/knowledge/,
divide em chunks semânticos com metadados de tópico e capítulo,
e persiste os embeddings no ChromaDB local.

Uso:
    cd /home/KaioLima/Documentos/LumenLab/backend
    .venv/bin/python ai_engine/vectorstore/ingest.py
    # ou:
    python -m ai_engine.vectorstore.ingest
"""
import os
import sys
import django

# Configura Django antes de qualquer import de settings/models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
from django.conf import settings

from ai_engine.vectorstore.chroma_store import get_embeddings


def load_pdfs(docs_dir: str) -> list:
    """
    Carrega todos os PDFs do diretório informado.

    Args:
        docs_dir: Caminho absoluto do diretório com os PDFs.
    Returns:
        Lista de Document objects do LangChain.
    """
    docs_path = Path(docs_dir)
    all_documents = []

    pdf_files = list(docs_path.glob('*.pdf'))
    if not pdf_files:
        print(f'Nenhum PDF encontrado em {docs_dir}')
        return []

    for pdf_file in pdf_files:
        print(f'Carregando: {pdf_file.name}')
        loader = PyPDFLoader(str(pdf_file))
        documents = loader.load()

        # Adiciona metadados de fonte e tópico
        for doc in documents:
            page_num = doc.metadata.get('page', 0)
            doc.metadata['source_file'] = pdf_file.name
            doc.metadata['page_number'] = page_num + 1  # 1-indexed para humanos
            doc.metadata['topic'] = _infer_topic(pdf_file.name, page_number=page_num, content=doc.page_content)

        all_documents.extend(documents)
        print(f'  -> {len(documents)} paginas carregadas')

    print(f'\nTotal: {len(all_documents)} paginas de {len(pdf_files)} PDFs')
    return all_documents


def _infer_topic(filename: str, page_number: int = None, content: str = '') -> str:
    """
    Infere o tópico educacional com base no capítulo/página do documento condensado
    ou no nome do arquivo e análise contextual do texto.
    """
    filename_lower = filename.lower()

    # Mapeamento preciso para o documento mestre condensado (RelatoriosLumenLab.pdf)
    if 'relatorio' in filename_lower and page_number is not None:
        if page_number < 4:
            return 'geral_lumenlab'
        elif page_number < 25:
            return 'seguranca_digital'
        elif page_number < 43:
            return 'inteligencia_artificial'
        else:
            return 'redes_sociais'

    # Fallback por nome do arquivo
    if 'seguranca' in filename_lower or 'higiene' in filename_lower:
        return 'seguranca_digital'
    if 'inteligencia' in filename_lower or 'ia' in filename_lower:
        return 'inteligencia_artificial'
    if 'redes' in filename_lower or 'algoritmo' in filename_lower:
        return 'redes_sociais'

    # Fallback por análise do conteúdo do texto
    content_lower = content.lower()
    if any(k in content_lower for k in ['golpe', 'phishing', 'senha', 'privacidade', 'sextorsão', 'take it down', 'safernet']):
        return 'seguranca_digital'
    if any(k in content_lower for k in ['machine learning', 'modelo', 'llm', 'alucinação', 'deepfake', 'redes neurais']):
        return 'inteligencia_artificial'
    if any(k in content_lower for k in ['algoritmo', 'feed', 'dopamina', 'tempo de tela', 'rolagem infinita', 'notificação']):
        return 'redes_sociais'

    return 'educacao_digital'


def split_documents(documents: list) -> list:
    """
    Divide os documentos em chunks semânticos com sobreposição.

    Args:
        documents: Lista de Document objects.
    Returns:
        Lista de chunks prontos para embedding.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=120,
        separators=['\n\n', '\n', '. ', ' ', ''],
        length_function=len,
    )
    chunks = splitter.split_documents(documents)
    print(f'Chunks gerados: {len(chunks)}')
    return chunks


def ingest(docs_dir: str = None, persist_dir: str = None, collection_name: str = None, batch_size: int = 20):
    """
    Pipeline completo: carrega PDFs, divide, embeda e persiste no ChromaDB
    em lotes controlados com tratamento de rate-limit (quota 429).

    Args:
        docs_dir: Diretório dos PDFs (padrão: settings.RAG_DOCS_DIR).
        persist_dir: Diretório de persistência ChromaDB (padrão: settings.CHROMA_PERSIST_DIR).
        collection_name: Nome da coleção (padrão: settings.CHROMA_COLLECTION_NAME).
        batch_size: Tamanho do lote de documentos por requisição.
    """
    import time
    docs_dir = docs_dir or settings.RAG_DOCS_DIR
    persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
    collection_name = collection_name or settings.CHROMA_COLLECTION_NAME

    print('=== Ingestão de Documentos Lumia ===')
    print(f'Diretório PDFs: {docs_dir}')
    print(f'ChromaDB: {persist_dir}/{collection_name}')
    print()

    # 1. Carrega PDFs
    documents = load_pdfs(docs_dir)
    if not documents:
        print('Nenhum documento para ingerir.')
        return

    # 2. Divide em chunks
    chunks = split_documents(documents)
    total_chunks = len(chunks)

    # 3. Inicializa vectorstore
    print('\nInicializando vectorstore ChromaDB...')
    embeddings = get_embeddings()

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )

    # Se a coleção já tiver documentos, avisa
    current_count = vectorstore._collection.count()
    if current_count > 0:
        print(f'Coleção já possui {current_count} chunks indexados.')
        if current_count >= total_chunks:
            print('Documentos já parecem estar totalmente ingeridos. Concluído!')
            return vectorstore

    print(f'\nIndexando {total_chunks} chunks em lotes de {batch_size} com controle de rate limit...')

    for i in range(0, total_chunks, batch_size):
        batch = chunks[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_chunks + batch_size - 1) // batch_size
        progress = int((i + len(batch)) / total_chunks * 100)

        # Retry loop para contornar limites 429 do Free Tier
        max_retries = 5
        for attempt in range(max_retries):
            try:
                vectorstore.add_documents(batch)
                print(f'  -> [Lote {batch_num}/{total_batches}] {len(batch)} chunks indexados ({progress}%)')
                time.sleep(1.5)  # Intervalo de segurança para 100 RPM
                break
            except Exception as exc:
                err_str = str(exc)
                if '429' in err_str or 'RESOURCE_EXHAUSTED' in err_str:
                    wait_time = 15 + (attempt * 5)
                    print(f'     [429 Quota Rate-Limit] Aguardando {wait_time}s antes de tentar novamente (tentativa {attempt + 1}/{max_retries})...')
                    time.sleep(wait_time)
                else:
                    print(f'     [ERRO] Falha no lote {batch_num}: {exc}')
                    raise exc

    final_count = vectorstore._collection.count()
    print(f'\nIngestão concluída com sucesso!')
    print(f'Total de documentos no ChromaDB: {final_count}')
    return vectorstore


if __name__ == '__main__':
    ingest()
