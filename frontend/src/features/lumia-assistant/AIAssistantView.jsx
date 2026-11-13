import React, { useState, useRef, useEffect, useCallback } from 'react';

const API_BASE = 'http://localhost:8000/api';

const QUICK_PROMPTS = [
  'Como sei se um link é phishing ou confiável?',
  'Por que as IAs cometem erros e inventam coisas?',
  'Como os algoritmos do feed prendem nossa atenção?',
  'Preciso de ajuda com segurança online',
];

const WELCOME_MESSAGE = {
  id: 'welcome',
  sender: 'lumia',
  text: 'Olá! Eu sou a Lumia, sua companheira digital no LumenLab. Meu papel não é te dar respostas prontas, mas te ajudar a investigar e questionar o mundo digital. O que você gostaria de explorar hoje?',
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
};

// ---------------------------------------------------------------------------
// Componente principal
// ---------------------------------------------------------------------------

export const AIAssistantView = () => {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [streamingText, setStreamingText] = useState('');
  const chatBottomRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Scroll automático ao fundo
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText, isStreaming]);

  const getToken = () => localStorage.getItem('lumenlab_token');

  const handleSend = useCallback(async (textToSend) => {
    const text = (textToSend || input).trim();
    if (!text || isStreaming) return;

    const token = getToken();
    if (!token) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        sender: 'lumia',
        text: 'Você precisa estar logado para conversar comigo. Faça login e volte!',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
      return;
    }

    // Adiciona mensagem do usuário
    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsStreaming(true);
    setStreamingText('');

    // AbortController para cancelar se necessário
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${API_BASE}/chatbot/message/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ message: text, session_id: sessionId }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`Erro ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));

            if (data.type === 'start') {
              setSessionId(data.session_id);
            } else if (data.type === 'token') {
              accumulated += data.token;
              setStreamingText(accumulated);
            } else if (data.type === 'done') {
              // Finaliza: move streamingText para messages
              const finalMsg = {
                id: (Date.now() + 1).toString(),
                sender: 'lumia',
                text: accumulated,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                intent: data.intent,
                safetyLevel: data.safety_level,
              };
              setMessages(prev => [...prev, finalMsg]);
              setStreamingText('');
            } else if (data.type === 'error') {
              const errMsg = {
                id: (Date.now() + 1).toString(),
                sender: 'lumia',
                text: data.message || 'Algo deu errado. Tente novamente.',
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                isError: true,
              };
              setMessages(prev => [...prev, errMsg]);
              setStreamingText('');
            }
          } catch {
            // JSON inválido — ignora linha
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        const errMsg = {
          id: (Date.now() + 1).toString(),
          sender: 'lumia',
          text: 'Não consegui conectar ao servidor. Verifique sua conexão e tente novamente.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isError: true,
        };
        setMessages(prev => [...prev, errMsg]);
        setStreamingText('');
      }
    } finally {
      setIsStreaming(false);
    }
  }, [input, isStreaming, sessionId]);

  // Cancela stream em andamento
  const handleCancel = () => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
    if (streamingText) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        sender: 'lumia',
        text: streamingText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
      setStreamingText('');
    }
  };

  // Submissão por Enter
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto', paddingTop: '10px' }}>

      {/* Cabeçalho */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <div style={{
          width: '54px', height: '54px', borderRadius: '16px',
          background: 'linear-gradient(135deg, #7042f4, #ec4899)',
          display: 'grid', placeItems: 'center', color: 'white',
          boxShadow: '0 8px 24px rgba(112, 66, 244, 0.35)',
        }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z" />
          </svg>
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h2 style={{ fontSize: '22px', fontWeight: 800, color: '#1e1435' }}>
              Lumia · Companheira Digital
            </h2>
            <span style={{
              fontSize: '10px', background: '#ede8ff', color: '#7042f4',
              border: '1px solid #ddd6fe', padding: '3px 8px', borderRadius: '12px', fontWeight: 800,
            }}>
              SOCRÁTICA
            </span>
          </div>
          <p style={{ fontSize: '13px', color: '#635b77', marginTop: '4px' }}>
            Orientação guiada por perguntas para transformar dúvidas em autonomia crítica.
          </p>
        </div>
      </div>

      {/* Caixa de Mensagens */}
      <div style={{
        background: 'white', border: '1.5px solid #e9d5ff', borderRadius: '18px',
        padding: '24px', minHeight: '440px', maxHeight: '520px', overflowY: 'auto',
        display: 'flex', flexDirection: 'column', gap: '18px',
        boxShadow: '0 6px 24px rgba(112, 66, 244, 0.06)',
      }}>
        {messages.map(msg => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}

        {/* Bubble de streaming em tempo real */}
        {isStreaming && streamingText && (
          <MessageBubble msg={{
            id: 'streaming',
            sender: 'lumia',
            text: streamingText,
            timestamp: '',
            isStreaming: true,
          }} />
        )}

        {/* Indicador de digitação quando ainda não chegou nenhum token */}
        {isStreaming && !streamingText && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#7042f4', fontSize: '13px', padding: '8px', fontWeight: 600 }}>
            <TypingDots />
            <span>Lumia está pensando...</span>
          </div>
        )}

        <div ref={chatBottomRef} />
      </div>

      {/* Sugestões Rápidas */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '16px' }}>
        {QUICK_PROMPTS.map((prompt, i) => (
          <QuickPromptButton key={i} text={prompt} onClick={() => handleSend(prompt)} disabled={isStreaming} />
        ))}
      </div>

      {/* Input de Envio */}
      <form
        onSubmit={e => { e.preventDefault(); handleSend(); }}
        style={{ display: 'flex', gap: '10px', marginTop: '16px' }}
      >
        <input
          type="text"
          placeholder="Tire uma dúvida sobre cybersegurança, IA ou hábitos digitais..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isStreaming}
          style={{
            flex: 1, padding: '14px 18px', borderRadius: '12px',
            border: '1.5px solid #e9d5ff', fontSize: '13px', color: '#1e1435',
            background: 'white', outline: 'none', transition: 'border-color 0.2s',
          }}
          onFocus={e => (e.target.style.borderColor = '#7042f4')}
          onBlur={e => (e.target.style.borderColor = '#e9d5ff')}
        />

        {isStreaming ? (
          <button
            type="button"
            onClick={handleCancel}
            style={{
              background: '#fee2e2', color: '#dc2626', border: '1.5px solid #fca5a5',
              borderRadius: '12px', padding: '0 20px', fontWeight: 700, fontSize: '13px', cursor: 'pointer',
            }}
          >
            Cancelar
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim()}
            style={{
              background: 'linear-gradient(135deg, #7042f4, #6366f1)', color: 'white',
              border: 'none', borderRadius: '12px', padding: '0 26px', fontWeight: 750,
              fontSize: '13px', cursor: !input.trim() ? 'not-allowed' : 'pointer',
              opacity: !input.trim() ? 0.6 : 1,
              boxShadow: '0 4px 16px rgba(112, 66, 244, 0.3)', transition: 'all 0.2s',
            }}
          >
            Enviar
          </button>
        )}
      </form>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Sub-componentes
// ---------------------------------------------------------------------------

const MessageBubble = ({ msg }) => {
  const isUser = msg.sender === 'user';
  const isError = msg.isError;

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      alignItems: isUser ? 'flex-end' : 'flex-start',
    }}>
      <div style={{
        maxWidth: '82%', padding: '16px 20px',
        borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
        background: isUser
          ? 'linear-gradient(135deg, #7042f4, #6366f1)'
          : isError
            ? '#fee2e2'
            : '#faf8ff',
        color: isUser ? '#ffffff' : isError ? '#dc2626' : '#1e1435',
        border: isUser ? 'none' : isError ? '1.5px solid #fca5a5' : '1.5px solid #ede9fe',
        fontSize: '14px', lineHeight: 1.7,
        boxShadow: isUser ? '0 4px 16px rgba(112, 66, 244, 0.25)' : 'none',
        whiteSpace: 'pre-wrap',
      }}>
        {msg.text}
        {msg.isStreaming && <span style={{ display: 'inline-block', animation: 'blink 1s step-end infinite' }}>|</span>}
      </div>
      {msg.timestamp && (
        <span style={{ fontSize: '10px', color: '#8b849c', marginTop: '4px', padding: '0 4px', fontWeight: 500 }}>
          {msg.timestamp}
          {msg.safetyLevel === 'warning' && ' · atencao'}
          {msg.safetyLevel === 'critical_danger' && ' · emergencia'}
        </span>
      )}
    </div>
  );
};

const QuickPromptButton = ({ text, onClick, disabled }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    style={{
      background: '#ffffff', border: '1.5px solid #e9d5ff', borderRadius: '20px',
      padding: '8px 14px', fontSize: '11px', color: '#5b21b6', fontWeight: 600,
      cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.5 : 1,
      transition: 'all 0.2s', boxShadow: '0 2px 6px rgba(112, 66, 244, 0.04)',
    }}
    onMouseEnter={e => {
      if (!disabled) {
        e.currentTarget.style.borderColor = '#7042f4';
        e.currentTarget.style.background = '#ede8ff';
        e.currentTarget.style.color = '#7042f4';
      }
    }}
    onMouseLeave={e => {
      e.currentTarget.style.borderColor = '#e9d5ff';
      e.currentTarget.style.background = '#ffffff';
      e.currentTarget.style.color = '#5b21b6';
    }}
  >
    {text}
  </button>
);

const TypingDots = () => (
  <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
    {[0, 1, 2].map(i => (
      <div key={i} style={{
        width: '6px', height: '6px', borderRadius: '50%', background: '#7042f4',
        animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
      }} />
    ))}
    <style>{`
      @keyframes bounce {
        0%, 100% { transform: translateY(0); opacity: 0.4; }
        50% { transform: translateY(-4px); opacity: 1; }
      }
      @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
      }
    `}</style>
  </div>
);
