"""
Controladores e endpoints da API de progresso pedagógico, hábitos e assistente socrática.

Gerencia o estado geral da aplicação do estudante, a telemetria das
trocas de tela, a marcação de hábitos de higiene digital e as conversas
orientadas pelo método socrático com a assistente pedagógica Lumia.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime

# Estado central em memória para persistência de navegação e progresso de fases
CURRENT_STATE = {
    'activeSection': 'menu',
    'privacyProgress': 45,
    'aiProgress': 25,
    'habits': [],
}


@api_view(['GET'])
def get_state(request):
    """
    Retorna o estado atual da aplicação e o progresso do estudante nas trilhas.

    Retorna:
        Response: Objeto JSON contendo a seção ativa, as porcentagens de
                  progresso em privacidade e IA, e a lista de hábitos do dia.
    """
    return Response(CURRENT_STATE)


@api_view(['POST'])
def switch_navigation(request):
    """
    Registra a navegação e a mudança de tela do estudante no frontend.

    Acionado sempre que o usuário clica em links da barra lateral, botões
    de continuação de fase ou atalhos do dashboard.

    Parâmetros da Requisição (JSON):
        section (str): Identificador da tela de destino (ex.: 'menu', 'modulos', 'agente-ia').

    Retorna:
        Response: Confirmação de navegação registrada com carimbo de data/hora (ISO 8601).
    """
    section = request.data.get('section', 'menu')
    CURRENT_STATE['activeSection'] = section
    return Response({
        'success': True,
        'activeSection': section,
        'timestamp': datetime.now().isoformat(),
        'message': f'Navegação para [{section}] registrada com sucesso no backend.'
    })


@api_view(['POST'])
def assistant_chat(request):
    """
    Ponto de entrada para diálogo pedagógico conversacional com a assistente Lumia.

    Emprega uma abordagem fundamentada no método socrático: em vez de entregar
    respostas expositivas prontas, a assistente formula perguntas reflexivas
    para instigar o pensamento crítico e a autonomia do estudante.

    Parâmetros da Requisição (JSON):
        message (str): Pergunta ou comentário digitado pelo estudante.

    Retorna:
        Response: Objeto JSON contendo a réplica pedagógica (`reply`).
    """
    message = request.data.get('message', '').lower()

    if 'senha' in message or 'blind' in message:
        reply = (
            'Ótima pergunta! Senhas fortes funcionam como cadeados digitais com muitas combinações. '
            'O que você acha que torna uma senha mais difícil de quebrar: uma palavra comum com números '
            'no final, ou uma frase inteira misturando letras maiúsculas, minúsculas e símbolos?'
        )
    elif 'alucina' in message or 'erro' in message or 'ia' in message:
        reply = (
            'As inteligências artificiais geram respostas prevendo palavras estatisticamente, mas elas não '
            '"pensam" como nós. Quando você lê algo curioso gerado por uma IA, qual é o seu primeiro passo '
            'para confirmar se aquilo é um fato real?'
        )
    elif 'rede' in message or 'feed' in message or 'algoritmo' in message:
        reply = (
            'Os algoritmos foram feitos para manter nossa atenção pelo maior tempo possível. Você já reparou '
            'quais tipos de postagens o seu aplicativo costuma te mostrar quando você passa mais de 30 minutos navegando?'
        )
    else:
        reply = (
            'Entendi o seu ponto! No LumenLab, acreditamos que questionar é o primeiro passo para o '
            'letramento digital. Que tal explorarmos juntos o que está por trás dessa tecnologia? '
            'O que mais te chamou atenção?'
        )

    return Response({'reply': reply})
