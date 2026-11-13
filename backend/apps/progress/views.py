"""
Controladores e endpoints da API de progresso pedagógico e navegação do LumenLab em português brasileiro.

Gerencia o estado geral da aplicação do estudante, a telemetria das
trocas de tela, a marcação de hábitos de higiene digital e a assistência socrática inicial.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime

# Estado central em memória para persistência de navegação e progresso de fases
ESTADO_ATUAL_APLICACAO = {
    'activeSection': 'menu',
    'secaoAtiva': 'menu',
    'privacyProgress': 45,
    'progressoPrivacidade': 45,
    'aiProgress': 25,
    'progressoIa': 25,
    'habits': [],
    'habitos': [],
}

CURRENT_STATE = ESTADO_ATUAL_APLICACAO


@api_view(['GET'])
def obter_estado_aplicacao(requisicao):
    """
    Retorna o estado global da aplicação e o percentual de progresso nas trilhas pedagógicas.

    Funcionamento:
      - Resgata os indicadores consolidados de avanço do aluno em Cibersegurança e IA.
      - Retorna dicionário bilíngue para compatibilidade integral com o frontend React.

    Retorna:
        Response: Objeto JSON contendo a seção ativa e os percentuais de progresso.
    """
    return Response(ESTADO_ATUAL_APLICACAO)


# Alias para rota pré-existente
get_state = obter_estado_aplicacao


@api_view(['POST'])
def alternar_secao_navegacao(requisicao):
    """
    Registra a telemetria de navegação e mudança de tela do estudante no frontend.

    Funcionamento:
      1. Extrai o identificador da tela ('section' ou 'secao').
      2. Atualiza o estado em memória da aplicação.
      3. Registra o timestamp em formato ISO 8601 para auditoria.

    Parâmetros:
        requisicao: Requisição POST contendo {'section': 'nome_da_secao'}.
    """
    identificador_secao = requisicao.data.get('section') or requisicao.data.get('secao', 'menu')
    ESTADO_ATUAL_APLICACAO['activeSection'] = identificador_secao
    ESTADO_ATUAL_APLICACAO['secaoAtiva'] = identificador_secao

    return Response({
        'sucesso': True,
        'success': True,
        'secaoAtiva': identificador_secao,
        'activeSection': identificador_secao,
        'registro_horario': datetime.now().isoformat(),
        'timestamp': datetime.now().isoformat(),
        'mensagem': f'Navegação para [{identificador_secao}] registrada com sucesso no backend.',
        'message': f'Navegação para [{identificador_secao}] registrada com sucesso no backend.',
    })


# Alias para rota pré-existente
switch_navigation = alternar_secao_navegacao


@api_view(['POST'])
def dialogo_assistente_socratica(requisicao):
    """
    Endpoint alternativo de diálogo pedagógico socrático simplificado.

    Funcionamento:
      1. Extrai a dúvida enviada pelo estudante ('message' ou 'mensagem').
      2. Identifica palavras-chave conceituais (senha, alucinação, algoritmo).
      3. Retorna uma réplica pedagógica que devolve uma pergunta reflexiva para estimular o raciocínio.

    Parâmetros:
        requisicao: Requisição POST com o texto da dúvida.

    Retorna:
        Response: Objeto JSON contendo a réplica socrática ('resposta' ou 'reply').
    """
    texto_mensagem = str(requisicao.data.get('message') or requisicao.data.get('mensagem', '')).lower()

    if 'senha' in texto_mensagem or 'blind' in texto_mensagem:
        replica = (
            'Ótima pergunta! Senhas fortes funcionam como cadeados digitais com muitas combinações. '
            'O que você acha que torna uma senha mais difícil de quebrar: uma palavra comum com números '
            'no final, ou uma frase inteira misturando letras maiúsculas, minúsculas e símbolos?'
        )
    elif 'alucina' in texto_mensagem or 'erro' in texto_mensagem or 'ia' in texto_mensagem:
        replica = (
            'As inteligências artificiais geram respostas prevendo palavras estatisticamente, mas elas não '
            '"pensam" como nós. Quando você lê algo curioso gerado por uma IA, qual é o seu primeiro passo '
            'para confirmar se aquilo é um fato real?'
        )
    elif 'rede' in texto_mensagem or 'feed' in texto_mensagem or 'algoritmo' in texto_mensagem:
        replica = (
            'Os algoritmos foram feitos para manter nossa atenção pelo maior tempo possível. Você já reparou '
            'quais tipos de postagens o seu aplicativo costuma te mostrar quando você passa mais de 30 minutos navegando?'
        )
    else:
        replica = (
            'Entendi o seu ponto! No LumenLab, acreditamos que questionar é o primeiro passo para o '
            'letramento digital. Que tal explorarmos juntos o que está por trás dessa tecnologia? '
            'O que mais te chamou atenção?'
        )

    return Response({
        'resposta': replica,
        'reply': replica,
    })


# Alias para rota pré-existente
assistant_chat = dialogo_assistente_socratica
