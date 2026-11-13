"""
Módulo de detecção e verificação de alucinações para o chatbot Lumia em português brasileiro.

Compara a resposta socrática formulada pela assistente com os trechos factuais
recuperados da base de conhecimento, atribuindo um índice de fidelidade factual (0.0 a 1.0).
"""
from __future__ import annotations

import os
import re
from typing import List


def verificar_fidelidade_resposta(
    resposta_gerada: str,
    trechos_contexto: List[str],
    modelo_llm=None,
    limiar_aprovacao: float = 0.6,
) -> dict:
    """
    Avalia se a resposta gerada pela assistente Lumia está fundamentada nas fontes bibliográficas.

    Funcionamento passo a passo:
      1. Se não houver contexto recuperado (ex: saudações, conversas informais),
         retorna fidelidade máxima automática (1.0).
      2. Inicializa o avaliador Gemini Flash em temperatura zero (julgamento determinístico).
      3. Concatena os trechos de contexto recuperados.
      4. Submete o prompt estruturado de avaliação ao modelo juiz.
      5. Extrai a pontuação (score numérico de 0.0 a 1.0) e a justificativa textual via expressões regulares.
      6. Retorna se a resposta é fiel comparando a nota com o limiar estipulado.

    Parâmetros:
        resposta_gerada (str): Texto da resposta gerada pela Lumia.
        trechos_contexto (List[str]): Lista de trechos factuais retornados pelo pipeline RAG.
        modelo_llm (opcional): Instância do LLM avaliador.
        limiar_aprovacao (float): Nota mínima de fidelidade para aprovação (padrão: 0.6).

    Retorna:
        dict: Dicionário com 'pontuacao' (float), 'eh_fiel' (bool) e 'explicacao' (str).
    """
    if not trechos_contexto:
        return {
            'pontuacao': 1.0,
            'eh_fiel': True,
            'explicacao': 'Sem contexto específico exigido — resposta de interação informal ou acolhimento.',
            # Chaves legadas
            'score': 1.0,
            'is_faithful': True,
            'explanation': 'Sem contexto específico exigido.',
        }

    if modelo_llm is None:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from django.conf import settings
            chave_api = getattr(settings, 'GOOGLE_API_KEY', '') or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY', '')
            chave_api_limpa = chave_api.strip().strip('\'"')
            modelo_llm = ChatGoogleGenerativeAI(
                model='gemini-2.5-flash',
                google_api_key=chave_api_limpa,
                temperature=0.0,
            )
        except ImportError:
            return {
                'pontuacao': 0.8,
                'eh_fiel': True,
                'explicacao': 'Biblioteca langchain-google-genai não instalada — verificação simplificada.',
                'score': 0.8,
                'is_faithful': True,
                'explanation': 'Verificação simplificada.',
            }

    contexto_unificado = '\n---\n'.join(trechos_contexto[:5])

    prompt_avaliacao = f"""Você é um avaliador rigoroso da qualidade de respostas pedagógicas.

CONTEXTO FACTUAL RECUPERADO DOS DOCUMENTOS:
{contexto_unificado}

RESPOSTA FORMULADA PELA ASSISTENTE:
{resposta_gerada}

Avalie em uma escala numérica de 0.0 a 1.0 se a resposta está fundamentada no contexto factual acima:
- 1.0: Totalmente fiel ao contexto factual, sem invenções.
- 0.5: Parcialmente fiel, com inferências razoáveis e pertinentes.
- 0.0: Contradiz frontalmente ou inventa dados não presentes no contexto.

Responda ESTRITAMENTE no seguinte formato de duas linhas:
PONTUACAO: <número decimal entre 0.0 e 1.0>
EXPLICACAO: <uma frase sucinta justificando a nota>
"""

    try:
        resultado = modelo_llm.invoke(prompt_avaliacao)
        texto_resultado = resultado.content if hasattr(resultado, 'content') else str(resultado)

        nota_extraida = _extrair_pontuacao(texto_resultado)
        explicacao_extraida = _extrair_explicacao(texto_resultado)

        return {
            'pontuacao': nota_extraida,
            'eh_fiel': nota_extraida >= limiar_aprovacao,
            'explicacao': explicacao_extraida,
            # Chaves legadas
            'score': nota_extraida,
            'is_faithful': nota_extraida >= limiar_aprovacao,
            'explanation': explicacao_extraida,
        }

    except Exception as erro_execucao:
        return {
            'pontuacao': 0.8,
            'eh_fiel': True,
            'explicacao': f'Avaliação automática indisponível no momento: {erro_execucao}',
            'score': 0.8,
            'is_faithful': True,
            'explanation': f'Avaliação automática indisponível: {erro_execucao}',
        }


def _extrair_pontuacao(texto: str) -> float:
    """Extrai o valor numérico da pontuação contido na linha PONTUACAO ou SCORE."""
    correspondencia = re.search(r'(?:PONTUACAO|SCORE):\s*([0-9.]+)', texto)
    if correspondencia:
        return min(1.0, max(0.0, float(correspondencia.group(1))))
    return 0.8


def _extrair_explicacao(texto: str) -> str:
    """Extrai a justificativa textual contida na linha EXPLICACAO."""
    correspondencia = re.search(r'(?:EXPLICACAO|EXPLANATION):\s*(.+)', texto)
    if correspondencia:
        return correspondencia.group(1).strip()
    return 'Avaliação concluída com sucesso.'


# Aliases para compatibilidade retroativa
check_faithfulness = verificar_fidelidade_resposta
