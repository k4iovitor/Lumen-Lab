"""
Script de geração e avaliação estatística do pipeline RAG da Lumia em português brasileiro.

Carrega os trechos documentais indexados no ChromaDB, gera pares de perguntas e respostas
esperadas usando o Gemini Flash, e mensura a acurácia de intenção e recuperação do agente.

Uso:
    cd /home/KaioLima/Documentos/LumenLab/backend
    .venv/bin/python scripts/generate_qa_evaluation.py
"""
import os
import sys
import json
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from ai_engine.vectorstore.chroma_store import obter_banco_vetorial
from ai_engine.agents.lumia_graph import obter_modelo_linguagem

PROMPT_GERACAO_PARES_QA = """Com base no trecho factual abaixo, formule {quantidade} perguntas realistas que um adolescente de 10 a 14 anos faria sobre o tema, juntamente com a resposta esperada e a classificação de intenção pedagógica.

TRECHO FACTUAL:
{contexto}

Retorne ESTRITAMENTE um array JSON contendo objetos com a seguinte estrutura, sem blocos markdown ou explicações adicionais:
[
  {{
    "pergunta": "...",
    "resposta_esperada": "...",
    "intencao_esperada": "pergunta_conceitual",
    "question": "...",
    "expected_answer": "...",
    "expected_intent": "concept_question"
  }}
]
"""


def gerar_pares_pergunta_resposta(quantidade_por_chunk: int = 3, maximo_chunks: int = 15) -> list:
    """
    Gera dataset sintético de perguntas e respostas para benchmarking do RAG.

    Parâmetros:
        quantidade_por_chunk: Número de questões a formular por trecho documental.
        maximo_chunks: Quantidade máxima de chunks a analisar no ChromaDB.

    Retorna:
        list: Coleção de pares de pergunta/resposta e intenção esperada.
    """
    modelo_llm = obter_modelo_linguagem(temperatura=0.5)
    banco_vetorial = obter_banco_vetorial()

    resultado_colecao = banco_vetorial._collection.get(include=['documents'])
    lista_documentos = resultado_colecao['documents'][:maximo_chunks]

    todos_pares = []

    for indice, texto_doc in enumerate(lista_documentos):
        print(f'Formulando questões para o trecho {indice + 1}/{len(lista_documentos)}...')

        prompt_formatado = PROMPT_GERACAO_PARES_QA.format(
            contexto=texto_doc[:800],
            quantidade=quantidade_por_chunk,
        )

        try:
            resposta = modelo_llm.invoke(prompt_formatado)
            conteudo_texto = resposta.content.strip()

            if conteudo_texto.startswith('```'):
                conteudo_texto = conteudo_texto.split('\n', 1)[1]
                conteudo_texto = conteudo_texto.rsplit('```', 1)[0].strip()

            pares_json = json.loads(conteudo_texto)
            if isinstance(pares_json, list):
                todos_pares.extend(pares_json)

        except Exception as erro_geracao:
            print(f'  [AVISO] Falha ao processar trecho {indice + 1}: {erro_geracao}')
            continue

    print(f'\nTotal de pares gerados: {len(todos_pares)}')
    return todos_pares


def avaliar_pipeline_rag(pares_qa: list) -> dict:
    """
    Submete os pares gerados ao grafo LangGraph para cálculo de métricas de precisão.

    Parâmetros:
        pares_qa: Coleção de perguntas e respostas de teste.

    Retorna:
        dict: Métricas estatísticas de acurácia de intenção e taxa de recuperação.
    """
    from ai_engine.agents.lumia_graph import construir_grafo_lumia
    from langchain_core.messages import HumanMessage

    grafo = construir_grafo_lumia(usar_memoria=False)

    intencoes_corretas = 0
    recuperacoes_sucesso = 0
    total_avaliado = len(pares_qa)
    resultados_detalhados = []

    for indice, item_par in enumerate(pares_qa):
        pergunta = item_par.get('pergunta') or item_par.get('question', '')
        intencao_esperada = item_par.get('intencao_esperada') or item_par.get('expected_intent', '')

        print(f'Avaliando {indice + 1}/{total_avaliado}: {pergunta[:50]}...')

        try:
            estado_resultado = grafo.invoke({
                'mensagens': [HumanMessage(content=pergunta)],
                'id_usuario': 1,
                'nome_estudante': 'Estudante de Teste',
                'idade': 13,
                'intencao': None,
                'nivel_seguranca': 'seguro',
                'contexto_recuperado': [],
                'dados_habito': None,
                'geracao': None,
            })

            intencao_obtida = estado_resultado.get('intencao') or estado_resultado.get('intent', 'conversa_casual')
            trechos_obtidos = estado_resultado.get('contexto_recuperado') or estado_resultado.get('retrieved_context', [])

            acerto_intencao = (intencao_obtida == intencao_esperada) or (
                intencao_obtida in ('pergunta_conceitual', 'concept_question') and
                intencao_esperada in ('pergunta_conceitual', 'concept_question')
            )

            recuperacao_valida = (
                len(trechos_obtidos) > 0
                if intencao_esperada in ('pergunta_conceitual', 'concept_question')
                else True
            )

            if acerto_intencao:
                intencoes_corretas += 1
            if recuperacao_valida:
                recuperacoes_sucesso += 1

            resultados_detalhados.append({
                'pergunta': pergunta,
                'intencao_esperada': intencao_esperada,
                'intencao_obtida': intencao_obtida,
                'acerto_intencao': acerto_intencao,
                'trechos_recuperados': len(trechos_obtidos),
            })

        except Exception as erro_teste:
            print(f'  [AVISO] Falha no teste: {erro_teste}')
            resultados_detalhados.append({'pergunta': pergunta, 'erro': str(erro_teste)})

    metricas = {
        'total_avaliado': total_avaliado,
        'acuracia_intencao': round(intencoes_corretas / total_avaliado, 4) if total_avaliado > 0 else 0,
        'taxa_recuperacao': round(recuperacoes_sucesso / total_avaliado, 4) if total_avaliado > 0 else 0,
        'resultados_detalhados': resultados_detalhados,
    }

    return metricas


def executar_avaliacao_principal():
    """Função mestre que executa a geração e consolidação das métricas de IA."""
    diretorio_saida = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'data', 'qa_evaluation',
    )
    os.makedirs(diretorio_saida, exist_ok=True)

    print('=== Geração de Dataset QA para Avaliação da Lumia ===\n')

    pares_qa = gerar_pares_pergunta_resposta(quantidade_por_chunk=3, maximo_chunks=15)

    caminho_dataset = os.path.join(diretorio_saida, 'qa_dataset.json')
    with open(caminho_dataset, 'w', encoding='utf-8') as arquivo_saida:
        json.dump(pares_qa, arquivo_saida, ensure_ascii=False, indent=2)
    print(f'\nDataset salvo em: {caminho_dataset}')

    print('\n=== Execução da Avaliação do Pipeline RAG ===\n')
    amostra_teste = pares_qa[:10]
    metricas = avaliar_pipeline_rag(amostra_teste)

    caminho_metricas = os.path.join(diretorio_saida, 'evaluation_metrics.json')
    with open(caminho_metricas, 'w', encoding='utf-8') as arquivo_metricas:
        json.dump(metricas, arquivo_metricas, ensure_ascii=False, indent=2)

    print(f'\nMétricas Finais de Qualidade:')
    print(f'  Acurácia de Intenção:  {metricas["acuracia_intencao"]:.1%}')
    print(f'  Taxa de Recuperação:   {metricas["taxa_recuperacao"]:.1%}')
    print(f'  Total Avaliado:        {metricas["total_avaliado"]}')
    print(f'\nRelatório salvo com sucesso em: {caminho_metricas}')


if __name__ == '__main__':
    executar_avaliacao_principal()
