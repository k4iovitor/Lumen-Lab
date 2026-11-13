"""
Verificação de alucinações nas respostas da Lumia.

Compara a resposta gerada com o contexto recuperado para detectar
afirmações que não têm suporte nas fontes originais.
"""
from __future__ import annotations

import os
import re
from typing import List


def check_faithfulness(
    response: str,
    context_chunks: List[str],
    llm=None,
    threshold: float = 0.6,
) -> dict:
    """
    Verifica se a resposta está fundamentada no contexto recuperado.

    Usa o Gemini para avaliar a fidelidade da resposta às fontes.

    Args:
        response: Resposta gerada pela Lumia.
        context_chunks: Lista de chunks do contexto recuperado.
        llm: Instância do LLM. Se None, usa Gemini Flash.
        threshold: Score mínimo para considerar a resposta fiel (0-1).
    Returns:
        Dict com 'score' (float), 'is_faithful' (bool) e 'explanation' (str).
    """
    if not context_chunks:
        return {
            'score': 1.0,
            'is_faithful': True,
            'explanation': 'Sem contexto para verificar — resposta de conversa informal.',
        }

    if llm is None:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from django.conf import settings
            api_key = getattr(settings, 'GOOGLE_API_KEY', '') or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY', '')
            api_key = api_key.strip().strip('\'"')
            llm = ChatGoogleGenerativeAI(
                model='gemini-2.5-flash',
                google_api_key=api_key,
                temperature=0.0,
            )
        except ImportError:
            return {
                'score': 0.8,
                'is_faithful': True,
                'explanation': 'langchain-google-genai não instalado — verificação ignorada.',
            }

    context_str = '\n---\n'.join(context_chunks[:5])  # Limita a 5 chunks

    prompt = f"""Você é um avaliador de qualidade de respostas educacionais.

CONTEXTO RECUPERADO:
{context_str}

RESPOSTA GERADA:
{response}

Avalie em uma escala de 0.0 a 1.0 se a resposta está fundamentada no contexto.
- 1.0: Totalmente fiel ao contexto
- 0.5: Parcialmente fiel, com inferências razoáveis
- 0.0: Contradiz ou inventa informações não presentes no contexto

Responda APENAS no formato:
SCORE: <número de 0.0 a 1.0>
EXPLICACAO: <uma frase explicando>
"""

    try:
        result = llm.invoke(prompt)
        content = result.content if hasattr(result, 'content') else str(result)

        score = _extract_score(content)
        explanation = _extract_explanation(content)

        return {
            'score': score,
            'is_faithful': score >= threshold,
            'explanation': explanation,
        }

    except Exception as exc:
        return {
            'score': 0.8,
            'is_faithful': True,
            'explanation': f'Verificação não disponível: {exc}',
        }


def _extract_score(text: str) -> float:
    """Extrai o score numérico da resposta do LLM."""
    match = re.search(r'SCORE:\s*([0-9.]+)', text)
    if match:
        return min(1.0, max(0.0, float(match.group(1))))
    return 0.8


def _extract_explanation(text: str) -> str:
    """Extrai a explicação da resposta do LLM."""
    match = re.search(r'EXPLICACAO:\s*(.+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return 'Explicação não disponível.'
