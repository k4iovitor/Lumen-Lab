"""
Cliente de busca factual em tempo real via API do Tavily em português brasileiro.

Permite que a assistente Lumia efetue verificações de fatos na web aberta,
auxiliando os estudantes a comparar informações suspeitas com fontes oficiais e científicas.
"""
from __future__ import annotations

import os
from typing import List, Dict, Any


def pesquisar_fatos_web(consulta_busca: str, maximo_resultados: int = 3) -> List[Dict[str, Any]]:
    """
    Executa uma busca factual em fontes abertas da internet através da API do Tavily.

    Funcionamento passo a passo:
      1. Obtém a chave da API TAVILY_API_KEY a partir das variáveis de ambiente.
      2. Se a chave não estiver configurada, retorna uma lista vazia sem interromper o sistema.
      3. Instancia o cliente TavilyClient e dispara a pesquisa contextual.
      4. Extrai título, URL de referência e o resumo textual de cada resultado encontrado.
      5. Retorna a lista estruturada de fontes para apoio à checagem de fatos.

    Parâmetros:
        consulta_busca (str): Pergunta ou termo a ser pesquisado na internet.
        maximo_resultados (int): Número máximo de links a recuperar (padrão: 3).

    Retorna:
        List[Dict[str, Any]]: Lista de dicionários contendo titulo, url e trecho_conteudo.
    """
    chave_api_tavily = os.getenv('TAVILY_API_KEY', '').strip()
    if not chave_api_tavily:
        return []

    try:
        from tavily import TavilyClient

        cliente_tavily = TavilyClient(api_key=chave_api_tavily)
        resposta_busca = cliente_tavily.search(
            query=consulta_busca,
            search_depth='basic',
            max_results=maximo_resultados,
        )

        resultados_formatados = []
        for item in resposta_busca.get('results', []):
            resultados_formatados.append({
                'titulo': item.get('title', ''),
                'url': item.get('url', ''),
                'trecho_conteudo': item.get('content', ''),
                'pontuacao_relevancia': item.get('score', 0.0),
            })

        return resultados_formatados

    except Exception as erro_pesquisa:
        print(f'[AVISO] Falha ao consultar o serviço Tavily: {erro_pesquisa}')
        return []


# Aliases para compatibilidade
search_facts = pesquisar_fatos_web
