"""
Script de ingestão de documentos pedagógicos no ChromaDB em português brasileiro.

Carrega o relatório condensado do diretório ai_engine/knowledge/, divide em chunks
semânticos com sobreposição, infere metadados por capítulo e página, e persiste
os embeddings gerados pelo Gemini no ChromaDB com tratamento de rate-limit da API.

Uso:
    cd /home/KaioLima/Documentos/LumenLab/backend
    .venv/bin/python ai_engine/vectorstore/ingest.py
"""
import os
import sys
import time
import django

# Configura o ambiente Django antes de qualquer import de settings
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

from ai_engine.vectorstore.chroma_store import obter_modelo_embeddings


def carregar_documentos_pdf(diretorio_documentos: str) -> list:
    """
    Carrega todos os arquivos PDF presentes no diretório informado e anexa metadados.

    Funcionamento:
      1. Localiza todos os arquivos com extensão .pdf no diretório.
      2. Utiliza o PyPDFLoader para extrair o texto de cada página individual.
      3. Anexa aos metadados de cada página: nome do arquivo, número da página e tópico inferido.
      4. Retorna a lista completa de páginas prontas para segmentação.

    Parâmetros:
        diretorio_documentos (str): Caminho absoluto da pasta com os PDFs.

    Retorna:
        list: Lista de objetos Document do LangChain.
    """
    caminho_documentos = Path(diretorio_documentos)
    todos_documentos = []

    arquivos_pdf = list(caminho_documentos.glob('*.pdf'))
    if not arquivos_pdf:
        print(f'Nenhum documento PDF localizado em: {diretorio_documentos}')
        return []

    for arquivo_pdf in arquivos_pdf:
        print(f'Carregando arquivo: {arquivo_pdf.name}')
        carregador = PyPDFLoader(str(arquivo_pdf))
        documentos_pagina = carregador.load()

        for doc in documentos_pagina:
            numero_pagina = doc.metadata.get('page', 0)
            doc.metadata['source_file'] = arquivo_pdf.name
            doc.metadata['page_number'] = numero_pagina + 1
            doc.metadata['topic'] = _inferir_topico_pedagogico(
                arquivo_pdf.name,
                numero_pagina=numero_pagina,
                conteudo_texto=doc.page_content
            )

        todos_documentos.extend(documentos_pagina)
        print(f'  -> {len(documentos_pagina)} páginas extraídas com sucesso.')

    print(f'\nTotal consolidado: {len(todos_documentos)} páginas de {len(arquivos_pdf)} arquivo(s).')
    return todos_documentos


def _inferir_topico_pedagogico(nome_arquivo: str, numero_pagina: int = None, conteudo_texto: str = '') -> str:
    """
    Classifica o tópico temático do conteúdo com base no capítulo, página ou palavras-chave.

    Mapeamento para o documento unificado (RelatoriosLumenLab.pdf):
      - Páginas 1 a 3: Visão Geral do LumenLab e proposta pedagógica.
      - Páginas 4 a 24: Segurança Digital, Phishing, Senhas e Privacidade.
      - Páginas 25 a 42: Inteligência Artificial, Modelos e Alucinações.
      - Páginas 43+: Redes Sociais, Higiene Digital e Tempo de Tela.
    """
    nome_minusculo = nome_arquivo.lower()

    if 'relatorio' in nome_minusculo and numero_pagina is not None:
        if numero_pagina < 4:
            return 'geral_lumenlab'
        elif numero_pagina < 25:
            return 'seguranca_digital'
        elif numero_pagina < 43:
            return 'inteligencia_artificial'
        else:
            return 'redes_sociais'

    # Classificação por palavras-chave de segurança
    texto_minusculo = conteudo_texto.lower()
    if any(termo in texto_minusculo for termo in ['golpe', 'phishing', 'senha', 'privacidade', 'sextorsão', 'safernet']):
        return 'seguranca_digital'
    if any(termo in texto_minusculo for termo in ['machine learning', 'modelo', 'llm', 'alucinação', 'deepfake', 'neural']):
        return 'inteligencia_artificial'
    if any(termo in texto_minusculo for termo in ['algoritmo', 'feed', 'dopamina', 'tempo de tela', 'notificação']):
        return 'redes_sociais'

    return 'educacao_digital'


def dividir_documentos_em_trechos(documentos: list) -> list:
    """
    Segmenta os documentos carregados em blocos de texto menores (chunks) com sobreposição.

    Funcionamento:
      - Utiliza o RecursiveCharacterTextSplitter com chunk_size de 600 caracteres
        e sobreposição (overlap) de 120 caracteres para garantir continuidade de sentido.
      - Preserva a hierarquia natural de parágrafos e frases.

    Parâmetros:
        documentos (list): Lista de páginas brutas do PDF.

    Retorna:
        list: Lista de chunks semânticos preparados para vetorização.
    """
    divisor = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=120,
        separators=['\n\n', '\n', '. ', ' ', ''],
        length_function=len,
    )
    trechos_gerados = divisor.split_documents(documentos)
    print(f'Total de trechos (chunks) gerados: {len(trechos_gerados)}')
    return trechos_gerados


def ingerir_base_conhecimento(
    diretorio_documentos: str = None,
    diretorio_persistencia: str = None,
    nome_colecao: str = None,
    tamanho_lote: int = 20
):
    """
    Executa o pipeline completo de ingestão e indexação vetorial.

    Funcionamento passo a passo:
      1. Lê os caminhos configurados no settings.py do Django.
      2. Carrega e extrai as páginas dos arquivos PDF.
      3. Divide os textos em chunks de 600 caracteres com metadados.
      4. Conecta à base de dados vetorial ChromaDB persistente.
      5. Se o banco já contiver os documentos, encerra de forma idempotente.
      6. Processa a vetorização em lotes de 20 chunks com pausa de 1.5s entre requisições
         para respeitar a cota de 100 requisições por minuto do Free Tier da Gemini API.
      7. Em caso de resposta HTTP 429 (Resource Exhausted), aplica recuo exponencial automático.

    Parâmetros:
        diretorio_documentos: Diretório com os relatórios PDF originais.
        diretorio_persistencia: Pasta de destino da base ChromaDB.
        nome_colecao: Nome da coleção vetorial no ChromaDB.
        tamanho_lote: Quantidade de trechos vetorizados a cada requisição de lote.
    """
    pasta_docs = diretorio_documentos or getattr(settings, 'RAG_DOCS_DIR', None)
    pasta_chroma = diretorio_persistencia or getattr(settings, 'CHROMA_PERSIST_DIR', None)
    colecao = nome_colecao or getattr(settings, 'CHROMA_COLLECTION_NAME', 'lumenlab_docs')

    print(f'=== Ingestão da Base de Conhecimento do LumenLab ===')
    print(f'Pasta de Documentos: {pasta_docs}')
    print(f'Pasta ChromaDB:     {pasta_chroma}')
    print(f'Coleção Vetorial:   {colecao}\n')

    documentos_brutos = carregar_documentos_pdf(pasta_docs)
    if not documentos_brutos:
        print('Nenhum documento carregado. Processo abortado.')
        return None

    trechos_chunks = dividir_documentos_em_trechos(documentos_brutos)
    total_trechos = len(trechos_chunks)

    print('\nInicializando banco vetorial ChromaDB com modelo de embeddings...')
    modelo_embeddings = obter_modelo_embeddings()

    banco_vetorial = Chroma(
        collection_name=colecao,
        embedding_function=modelo_embeddings,
        persist_directory=str(pasta_chroma),
    )

    contagem_atual = banco_vetorial._collection.count()
    if contagem_atual >= total_trechos:
        print(f'A coleção já possui {contagem_atual} trechos indexados. Base já está atualizada!')
        return banco_vetorial

    print(f'\nIndexando {total_trechos} trechos em lotes de {tamanho_lote} com controle de taxa...')

    for indice_inicio in range(0, total_trechos, tamanho_lote):
        lote_atual = trechos_chunks[indice_inicio:indice_inicio + tamanho_lote]
        numero_lote = (indice_inicio // tamanho_lote) + 1
        total_lotes = (total_trechos + tamanho_lote - 1) // tamanho_lote
        progresso_percentual = int((indice_inicio + len(lote_atual)) / total_trechos * 100)

        # Loop de retentativas para tratamento de limite de cota 429
        limite_tentativas = 5
        for tentativa in range(limite_tentativas):
            try:
                banco_vetorial.add_documents(lote_atual)
                print(f'  -> [Lote {numero_lote}/{total_lotes}] {len(lote_atual)} trechos indexados ({progresso_percentual}%)')
                time.sleep(1.5)
                break
            except Exception as erro_lote:
                mensagem_erro = str(erro_lote)
                if '429' in mensagem_erro or 'RESOURCE_EXHAUSTED' in mensagem_erro:
                    tempo_espera = 15 + (tentativa * 5)
                    print(f'     [Cota 429 Excedida] Aguardando {tempo_espera}s antes de tentar novamente (tentativa {tentativa + 1}/{limite_tentativas})...')
                    time.sleep(tempo_espera)
                else:
                    print(f'     [ERRO] Falha no lote {numero_lote}: {erro_lote}')
                    raise erro_lote

    total_final = banco_vetorial._collection.count()
    print(f'\nIngestão finalizada com sucesso! Total no ChromaDB: {total_final} trechos.')
    return banco_vetorial


# Aliases para compatibilidade retroativa
load_pdfs = carregar_documentos_pdf
_infer_topic = _inferir_topico_pedagogico
split_documents = dividir_documentos_em_trechos
ingest = ingerir_base_conhecimento

if __name__ == '__main__':
    ingerir_base_conhecimento()
