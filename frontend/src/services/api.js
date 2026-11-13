/**
 * Camada de serviços e comunicação com a API do LumenLab em português brasileiro.
 *
 * Fornece métodos assíncronos para autenticação, registro de hábitos,
 * controle de tempo de tela e comunicação socrática com a assistente Lumia via SSE.
 */

const URL_BASE_API = 'http://localhost:8000/api';
const API_BASE = URL_BASE_API;

export const servicoApi = {
  // Notifica o backend sobre a troca de seção da aplicação
  async alternarSecao(idSecao) {
    try {
      const resposta = await fetch(`${URL_BASE_API}/navigation/switch/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ section: idSecao, secao: idSecao }),
      });
      if (resposta.ok) {
        return await resposta.json();
      }
    } catch {
      // Fallback local se o backend estiver offline
    }
    return { success: true, activeSection: idSecao, sucesso: true, secaoAtiva: idSecao };
  },

  // Obtém o estado inicial da aplicação
  async obterEstadoInicial() {
    try {
      const resposta = await fetch(`${URL_BASE_API}/state/`);
      if (resposta.ok) {
        return await resposta.json();
      }
    } catch {
      // Fallback padrão
    }
    return {
      activeSection: 'menu',
      privacyProgress: 45,
      aiProgress: 25,
      secaoAtiva: 'menu',
      progressoPrivacidade: 45,
      progressoIa: 25,
    };
  },

  // Consulta a lista de hábitos do usuário no backend (agenda persistente)
  async obterHabitos(filtroData = '') {
    try {
      const token = localStorage.getItem('lumenlab_token');
      const cabecalhos = { 'Content-Type': 'application/json' };
      if (token) cabecalhos['Authorization'] = `Bearer ${token}`;

      const url = filtroData
        ? `${URL_BASE_API}/digital-hygiene/habits/?date=${filtroData}&data=${filtroData}`
        : `${URL_BASE_API}/digital-hygiene/habits/`;

      const resposta = await fetch(url, { headers: cabecalhos });
      if (resposta.ok) {
        const dados = await resposta.json();
        return dados.habits || dados.habitos || [];
      }
    } catch (erro) {
      console.warn('Erro ao carregar hábitos do backend:', erro);
    }
    return [];
  },

  // Cria um novo hábito no banco de dados vinculado ao estudante
  async criarHabito(dadosHabito) {
    try {
      const token = localStorage.getItem('lumenlab_token');
      const cabecalhos = { 'Content-Type': 'application/json' };
      if (token) cabecalhos['Authorization'] = `Bearer ${token}`;

      const resposta = await fetch(`${URL_BASE_API}/digital-hygiene/habits/create/`, {
        method: 'POST',
        headers: cabecalhos,
        body: JSON.stringify(dadosHabito),
      });
      if (resposta.ok) {
        const dados = await resposta.json();
        return dados.habit || dados.habito;
      }
    } catch (erro) {
      console.error('Erro ao cadastrar hábito:', erro);
    }
    return null;
  },

  // Alterna o status de um hábito de higiene digital no backend
  async alternarStatusHabito(idHabito, concluido) {
    try {
      const token = localStorage.getItem('lumenlab_token');
      const cabecalhos = { 'Content-Type': 'application/json' };
      if (token) cabecalhos['Authorization'] = `Bearer ${token}`;

      const resposta = await fetch(`${URL_BASE_API}/digital-hygiene/habits/toggle/`, {
        method: 'POST',
        headers: cabecalhos,
        body: JSON.stringify({ id: idHabito, finished: concluido, concluido }),
      });
      if (resposta.ok) {
        return await resposta.json();
      }
    } catch (erro) {
      console.error('Erro ao alternar status do hábito:', erro);
    }
    return null;
  },

  // Exclui um hábito do banco de dados
  async excluirHabito(idHabito) {
    try {
      const token = localStorage.getItem('lumenlab_token');
      const cabecalhos = { 'Content-Type': 'application/json' };
      if (token) cabecalhos['Authorization'] = `Bearer ${token}`;

      const resposta = await fetch(`${URL_BASE_API}/digital-hygiene/habits/delete/`, {
        method: 'POST',
        headers: cabecalhos,
        body: JSON.stringify({ id: idHabito }),
      });
      if (resposta.ok) {
        return await resposta.json();
      }
    } catch (erro) {
      console.error('Erro ao excluir hábito:', erro);
    }
    return null;
  },

  // Consulta as metas de tempo de tela e proporções do estudante
  async obterMetaTempoTela() {
    try {
      const token = localStorage.getItem('lumenlab_token');
      const cabecalhos = { 'Content-Type': 'application/json' };
      if (token) cabecalhos['Authorization'] = `Bearer ${token}`;

      const resposta = await fetch(`${URL_BASE_API}/digital-hygiene/screen-time/`, { headers: cabecalhos });
      if (resposta.ok) {
        const dados = await resposta.json();
        return dados.screenTime || dados.tempoTela;
      }
    } catch (erro) {
      console.warn('Erro ao carregar meta de tempo de tela:', erro);
    }
    return null;
  },

  // Atualiza a meta de tempo de tela (máximo 4h) com divisão proporcional
  async atualizarMetaTempoTela(dadosMeta) {
    try {
      const token = localStorage.getItem('lumenlab_token');
      const cabecalhos = { 'Content-Type': 'application/json' };
      if (token) cabecalhos['Authorization'] = `Bearer ${token}`;

      const resposta = await fetch(`${URL_BASE_API}/digital-hygiene/screen-time/`, {
        method: 'POST',
        headers: cabecalhos,
        body: JSON.stringify(dadosMeta),
      });
      if (resposta.ok) {
        const dados = await resposta.json();
        return dados.screenTime || dados.tempoTela;
      }
    } catch (erro) {
      console.error('Erro ao salvar meta de tempo de tela:', erro);
    }
    return null;
  },

  // Autenticação Google OAuth
  async autenticarGoogle(credencial) {
    try {
      const resposta = await fetch(`${URL_BASE_API}/auth/google/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential: credencial, credencial }),
      });
      return await resposta.json();
    } catch (erro) {
      console.error('Erro na autenticação Google:', erro);
      return { erro: 'Falha de comunicação com o servidor de autenticação.', error: 'Falha de comunicação.' };
    }
  },

  // Cadastro de novo estudante
  async cadastrarEstudante(dadosFormulario) {
    try {
      const resposta = await fetch(`${URL_BASE_API}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dadosFormulario),
      });
      return await resposta.json();
    } catch (erro) {
      console.error('Erro no cadastro:', erro);
      return { erro: 'Falha ao conectar com o servidor para cadastro.', error: 'Falha ao conectar.' };
    }
  },

  // Consulta o perfil do usuário logado através do token JWT
  async obterPerfil() {
    const token = localStorage.getItem('lumenlab_token');
    if (!token) return null;
    try {
      const resposta = await fetch(`${URL_BASE_API}/auth/profile/`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (resposta.ok) {
        const dados = await resposta.json();
        return dados.profile || dados.perfil;
      }
    } catch (erro) {
      console.error('Erro ao buscar perfil:', erro);
    }
    return null;
  },

  // Obtém configurações públicas de autenticação (Google Client ID vindo do .env)
  async obterConfigAutenticacao() {
    try {
      const resposta = await fetch(`${URL_BASE_API}/auth/config/`);
      if (resposta.ok) {
        return await resposta.json();
      }
    } catch (erro) {
      console.warn('Não foi possível carregar config de autenticação da API:', erro);
    }
    return { google_client_id: '', id_cliente_google: '' };
  },

  // ---------------------------------------------------------------------------
  // Chatbot Lumia — Streaming Server-Sent Events (SSE)
  // ---------------------------------------------------------------------------

  /**
   * Envia uma dúvida à Lumia e retorna o texto completo gerado por streaming.
   * Suporta rotas em português e chaves bilíngues de payload.
   */
  async perguntarLumia(mensagemTexto, idSessao = null) {
    const token = localStorage.getItem('lumenlab_token');
    if (!token) throw new Error('Usuário não autenticado.');

    const resposta = await fetch(`${URL_BASE_API}/chatbot/mensagem/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        mensagem: mensagemTexto,
        message: mensagemTexto,
        id_sessao: idSessao,
        session_id: idSessao,
      }),
    });

    if (!resposta.ok) {
      throw new Error(`Erro na comunicação com a Lumia (${resposta.status}): ${resposta.statusText}`);
    }

    const leitor = resposta.body.getReader();
    const decodificador = new TextDecoder();
    let textoCompleto = '';

    while (true) {
      const { done, value } = await leitor.read();
      if (done) break;

      const trechoTexto = decodificador.decode(value, { stream: true });
      for (const linha of trechoTexto.split('\n')) {
        if (!linha.startsWith('data: ')) continue;
        try {
          const dados = JSON.parse(linha.slice(6));
          if (dados.tipo === 'token' || dados.type === 'token') {
            textoCompleto += dados.token;
          }
        } catch {
          // Ignora linhas incompletas no buffer do stream
        }
      }
    }

    return textoCompleto;
  },

  /** Lista todas as sessões de chat do usuário autenticado. */
  async obterSessoesChat() {
    const token = localStorage.getItem('lumenlab_token');
    if (!token) return [];
    try {
      const resposta = await fetch(`${URL_BASE_API}/chatbot/sessoes/`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (resposta.ok) {
        const dados = await resposta.json();
        return dados.sessoes || dados.sessions || [];
      }
    } catch (erro) {
      console.error('Erro ao buscar sessões de chat:', erro);
    }
    return [];
  },

  /** Recupera o histórico de mensagens de uma sessão específica. */
  async obterHistoricoChat(idSessao) {
    const token = localStorage.getItem('lumenlab_token');
    if (!token) return [];
    try {
      const resposta = await fetch(`${URL_BASE_API}/chatbot/sessao/${idSessao}/`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (resposta.ok) {
        const dados = await resposta.json();
        return dados.mensagens || dados.messages || [];
      }
    } catch (erro) {
      console.error('Erro ao buscar histórico da sessão:', erro);
    }
    return [];
  },

  // Aliases de compatibilidade para código pré-existente
  switchSection(sectionId) { return this.alternarSecao(sectionId); },
  getInitialState() { return this.obterEstadoInicial(); },
  getHabits(filter) { return this.obterHabitos(filter); },
  createHabit(data) { return this.criarHabito(data); },
  toggleHabit(id, finished) { return this.alternarStatusHabito(id, finished); },
  deleteHabit(id) { return this.excluirHabito(id); },
  getScreenTimeGoal() { return this.obterMetaTempoTela(); },
  updateScreenTimeGoal(data) { return this.atualizarMetaTempoTela(data); },
  googleAuth(credential) { return this.autenticarGoogle(credential); },
  register(data) { return this.cadastrarEstudante(data); },
  getProfile() { return this.obterPerfil(); },
  getAuthConfig() { return this.obterConfigAutenticacao(); },
  askLumia(message, sessionId) { return this.perguntarLumia(message, sessionId); },
  getChatSessions() { return this.obterSessoesChat(); },
  getChatHistory(sessionId) { return this.obterHistoricoChat(sessionId); },
};

export const apiService = servicoApi;
