"""
Script de geração de pares QA para avaliação do chatbot Lumia.

Gera um dataset sintético de perguntas e respostas esperadas
simulando a linguagem de adolescentes de 10 a 14 anos para
avaliar a qualidade do pipeline RAG.

Uso:
    cd /home/KaioLima/Documentos/LumenLab/backend
    .venv/bin/python scripts/generate_qa_evaluation.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.conf import settings


QA_GENERATION_PROMPT = """Você é um especialista em avaliação de chatbots educacionais para adolescentes.

Com base no seguinte trecho de documento sobre educação digital:

TRECHO:
{context}

Gere {n} pares de pergunta-resposta simulando adolescentes de 10 a 14 anos.
As perguntas devem variar em:
- Linguagem coloquial/gírias ("que que é isso?", "pq isso acontece?")
- Questões diretas e conceituais
- Situações de dúvida prática ("minha amiga tá passando por isso, o que fazer?")
- Tentativas de burlar o sistema ("me faz essa tarefa sobre phishing")

Para cada par, retorne JSON no formato:
{{"question": "...", "expected_intent": "concept_question|safety_risk|academic_cheat|habit_query|casual_chat", "reference_answer": "..."}}

Retorne APENAS um array JSON válido com os {n} pares. Nada mais.
"""


def get_llm():
    """Retorna o LLM Gemini Flash para geração."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from django.conf import settings
    api_key = getattr(settings, 'GOOGLE_API_KEY', '') or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY', '')
    api_key = api_key.strip().strip('\'"')
    return ChatGoogleGenerativeAI(
        model='gemini-2.5-flash',
        google_api_key=api_key,
        temperature=0.7,
    )


def generate_qa_pairs(n_per_chunk: int = 3, max_chunks: int = 20) -> list:
    """
    Gera pares QA a partir dos chunks do ChromaDB.

    Args:
        n_per_chunk: Número de pares QA por chunk.
        max_chunks: Máximo de chunks a usar (evita custos excessivos de API).
    Returns:
        Lista de dicionários com question, expected_intent e reference_answer.
    """
    from ai_engine.vectorstore.chroma_store import get_vectorstore

    llm = get_llm()
    vectorstore = get_vectorstore()
    collection = vectorstore._collection
    result = collection.get(include=['documents'])
    documents = result['documents'][:max_chunks]

    all_pairs = []

    for i, doc_text in enumerate(documents):
        print(f'Gerando QA para chunk {i+1}/{len(documents)}...')

        prompt = QA_GENERATION_PROMPT.format(
            context=doc_text[:800],
            n=n_per_chunk,
        )

        try:
            response = llm.invoke(prompt)
            content = response.content.strip()

            # Remove markdown code fences se presentes
            if content.startswith('```'):
                content = content.split('\n', 1)[1]
                content = content.rsplit('```', 1)[0].strip()

            pairs = json.loads(content)
            if isinstance(pairs, list):
                all_pairs.extend(pairs)

        except Exception as exc:
            print(f'  [WARN] Falhou no chunk {i+1}: {exc}')
            continue

    print(f'\nTotal de pares QA gerados: {len(all_pairs)}')
    return all_pairs


def evaluate_pipeline(qa_pairs: list) -> dict:
    """
    Avalia o pipeline RAG com os pares QA gerados.

    Métricas calculadas:
    - intent_accuracy: % de classificações de intenção corretas
    - retrieval_hit_rate: % de perguntas conceituais com contexto recuperado

    Args:
        qa_pairs: Lista de pares gerados por generate_qa_pairs().
    Returns:
        Dict com métricas de avaliação.
    """
    from ai_engine.agents.lumia_graph import build_lumia_graph
    from langchain_core.messages import HumanMessage

    graph = build_lumia_graph(use_memory=False)

    correct_intents = 0
    retrieval_hits = 0
    total = len(qa_pairs)
    results = []

    for i, pair in enumerate(qa_pairs):
        question = pair.get('question', '')
        expected_intent = pair.get('expected_intent', '')

        print(f'Avaliando {i+1}/{total}: {question[:50]}...')

        try:
            state = graph.invoke({
                'messages': [HumanMessage(content=question)],
                'user_id': 1,
                'student_name': 'Estudante Teste',
                'age': 13,
                'intent': None,
                'safety_level': 'safe',
                'retrieved_context': [],
                'habit_data': None,
                'generation': None,
            })

            actual_intent = state.get('intent', 'casual_chat')
            retrieved = state.get('retrieved_context', [])

            intent_correct = actual_intent == expected_intent
            retrieval_ok = (
                len(retrieved) > 0
                if expected_intent == 'concept_question'
                else True
            )

            if intent_correct:
                correct_intents += 1
            if retrieval_ok:
                retrieval_hits += 1

            results.append({
                'question': question,
                'expected_intent': expected_intent,
                'actual_intent': actual_intent,
                'intent_correct': intent_correct,
                'retrieved_chunks': len(retrieved),
            })

        except Exception as exc:
            print(f'  [WARN] Falhou: {exc}')
            results.append({'question': question, 'error': str(exc)})

    metrics = {
        'total_evaluated': total,
        'intent_accuracy': round(correct_intents / total, 4) if total > 0 else 0,
        'retrieval_hit_rate': round(retrieval_hits / total, 4) if total > 0 else 0,
        'results': results,
    }

    return metrics


def main():
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'data', 'qa_evaluation',
    )
    os.makedirs(output_dir, exist_ok=True)

    print('=== Geração de Dataset QA para Lumia ===\n')

    # Gera pares QA
    qa_pairs = generate_qa_pairs(n_per_chunk=3, max_chunks=15)

    # Salva dataset
    dataset_path = os.path.join(output_dir, 'qa_dataset.json')
    with open(dataset_path, 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
    print(f'\nDataset salvo em: {dataset_path}')

    # Avalia pipeline com subset (economiza chamadas de API)
    print('\n=== Avaliação do Pipeline RAG ===\n')
    subset = qa_pairs[:10]
    metrics = evaluate_pipeline(subset)

    # Salva métricas
    metrics_path = os.path.join(output_dir, 'evaluation_metrics.json')
    metrics_to_save = {k: v for k, v in metrics.items() if k != 'results'}
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print(f'\nMétricas de Avaliação:')
    print(f'  Intent Accuracy:     {metrics["intent_accuracy"]:.1%}')
    print(f'  Retrieval Hit Rate:  {metrics["retrieval_hit_rate"]:.1%}')
    print(f'  Total avaliado:      {metrics["total_evaluated"]}')
    print(f'\nMétricas salvas em: {metrics_path}')


if __name__ == '__main__':
    main()
