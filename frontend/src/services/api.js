const API_BASE = 'http://localhost:8000/api';

export const apiService = {
  // Notifica o backend sobre a troca de seção da aplicação
  async switchSection(sectionId) {
    try {
      const response = await fetch(`${API_BASE}/navigation/switch/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ section: sectionId }),
      });
      if (response.ok) {
        return await response.json();
      }
    } catch {
      // Fallback local se o backend estiver offline
    }
    return { success: true, activeSection: sectionId };
  },

  // Obtém o estado inicial da aplicação
  async getInitialState() {
    try {
      const response = await fetch(`${API_BASE}/state/`);
      if (response.ok) {
        return await response.json();
      }
    } catch {
      // Fallback padrão
    }
    return {
      activeSection: 'menu',
      privacyProgress: 45,
      aiProgress: 25,
    };
  },

  // Consulta a lista de hábitos do usuário no backend (agenda persistente)
  async getHabits(dateFilter = '') {
    try {
      const token = localStorage.getItem('lumenlab_token');
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const url = dateFilter
        ? `${API_BASE}/digital-hygiene/habits/?date=${dateFilter}`
        : `${API_BASE}/digital-hygiene/habits/`;

      const response = await fetch(url, { headers });
      if (response.ok) {
        const data = await response.json();
        return data.habits || [];
      }
    } catch (err) {
      console.warn('Erro ao carregar hábitos do backend:', err);
    }
    return [];
  },

  // Cria um novo hábito no banco de dados vinculado ao estudante
  async createHabit(habitData) {
    try {
      const token = localStorage.getItem('lumenlab_token');
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await fetch(`${API_BASE}/digital-hygiene/habits/create/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(habitData),
      });
      if (response.ok) {
        const data = await response.json();
        return data.habit;
      }
    } catch (err) {
      console.error('Erro ao cadastrar hábito:', err);
    }
    return null;
  },

  // Alterna o status de um hábito de higiene digital no backend
  async toggleHabit(habitId, finished) {
    try {
      const token = localStorage.getItem('lumenlab_token');
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await fetch(`${API_BASE}/digital-hygiene/habits/toggle/`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ id: habitId, finished }),
      });
      if (response.ok) {
        return await response.json();
      }
    } catch (err) {
      console.error('Erro ao alternar status do hábito:', err);
    }
    return null;
  },

  // Exclui um hábito do banco de dados
  async deleteHabit(habitId) {
    try {
      const token = localStorage.getItem('lumenlab_token');
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await fetch(`${API_BASE}/digital-hygiene/habits/delete/`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ id: habitId }),
      });
      if (response.ok) {
        return await response.json();
      }
    } catch (err) {
      console.error('Erro ao excluir hábito:', err);
    }
    return null;
  },

  // Consulta as metas de tempo de tela e proporções do estudante
  async getScreenTimeGoal() {
    try {
      const token = localStorage.getItem('lumenlab_token');
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await fetch(`${API_BASE}/digital-hygiene/screen-time/`, { headers });
      if (response.ok) {
        const data = await response.json();
        return data.screenTime;
      }
    } catch (err) {
      console.warn('Erro ao carregar meta de tempo de tela:', err);
    }
    return null;
  },

  // Atualiza a meta de tempo de tela (máximo 4h) com divisão proporcional
  async updateScreenTimeGoal(goalData) {
    try {
      const token = localStorage.getItem('lumenlab_token');
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await fetch(`${API_BASE}/digital-hygiene/screen-time/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(goalData),
      });
      if (response.ok) {
        const data = await response.json();
        return data.screenTime;
      }
    } catch (err) {
      console.error('Erro ao salvar meta de tempo de tela:', err);
    }
    return null;
  },

  // Autenticação Google OAuth
  async googleAuth(credential) {
    try {
      const response = await fetch(`${API_BASE}/auth/google/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential }),
      });
      return await response.json();
    } catch (err) {
      console.error('Erro na autenticação Google:', err);
      return { error: 'Falha de comunicação com o servidor de autenticação.' };
    }
  },

  // Cadastro de novo estudante
  async register(data) {
    try {
      const response = await fetch(`${API_BASE}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      return await response.json();
    } catch (err) {
      console.error('Erro no cadastro:', err);
      return { error: 'Falha ao conectar com o servidor para cadastro.' };
    }
  },

  // Consulta o perfil do usuário logado através do token JWT
  async getProfile() {
    const token = localStorage.getItem('lumenlab_token');
    if (!token) return null;
    try {
      const response = await fetch(`${API_BASE}/auth/profile/`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        return data.profile;
      }
    } catch (err) {
      console.error('Erro ao buscar perfil:', err);
    }
    return null;
  },

  // Obtém configurações públicas de autenticação (Google Client ID vindo do .env)
  async getAuthConfig() {
    try {
      const response = await fetch(`${API_BASE}/auth/config/`);
      if (response.ok) {
        return await response.json();
      }
    } catch (err) {
      console.warn('Não foi possível carregar config de autenticação da API:', err);
    }
    return { google_client_id: '' };
  },

  // ---------------------------------------------------------------------------
  // Chatbot Lumia — SSE Streaming
  // ---------------------------------------------------------------------------

  /**
   * Envia uma mensagem à Lumia e retorna o texto completo da resposta.
   * Para streaming em tempo real, use streamLumiaMessage() diretamente.
   */
  async askLumia(message, sessionId = null) {
    const token = localStorage.getItem('lumenlab_token');
    if (!token) throw new Error('Usuário não autenticado');

    const response = await fetch(`${API_BASE}/chatbot/message/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ message, session_id: sessionId }),
    });

    if (!response.ok) {
      throw new Error(`Erro ${response.status}: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullText = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      for (const line of chunk.split('\n')) {
        if (!line.startsWith('data: ')) continue;
        try {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'token') fullText += data.token;
        } catch { /* ignora linhas inválidas */ }
      }
    }

    return fullText;
  },

  /** Lista as sessões de chat do usuário autenticado. */
  async getChatSessions() {
    const token = localStorage.getItem('lumenlab_token');
    if (!token) return [];
    try {
      const response = await fetch(`${API_BASE}/chatbot/sessions/`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        return data.sessions || [];
      }
    } catch (err) {
      console.error('Erro ao buscar sessões:', err);
    }
    return [];
  },

  /** Retorna o histórico de mensagens de uma sessão específica. */
  async getChatHistory(sessionId) {
    const token = localStorage.getItem('lumenlab_token');
    if (!token) return [];
    try {
      const response = await fetch(`${API_BASE}/chatbot/session/${sessionId}/`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        return data.messages || [];
      }
    } catch (err) {
      console.error('Erro ao buscar histórico:', err);
    }
    return [];
  },
};

