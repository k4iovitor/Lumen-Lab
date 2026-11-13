/**
 * Componente de Interface do Chatbot Socrático Lumia em português brasileiro.
 *
 * Oferece interface de chat com animação de streaming de tokens em tempo real (SSE),
 * botões de sugestões pedagógicas, cancelamento de requisição e persistência relacional.
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';

const URL_BASE_API = 'http://localhost:8000/api';

// Dúvidas rápidas de sugestão para engajamento pedagógico inicial
const SUGESTOES_RAPIDAS = [
  'Como sei se um link é phishing ou confiável?',
  'Por que as IAs cometem erros e inventam coisas?',
  'Como os algoritmos do feed prendem nossa atenção?',
  'Preciso de ajuda com segurança online',
];

// Mensagem inicial de boas-vindas da assistente socrática
const MENSAGEM_BOAS_VINDAS = {
  id: 'boas-vindas',
  emissor: 'lumia',
  sender: 'lumia',
  texto: 'Olá! Eu sou a Lumia, sua companheira digital no LumenLab. Meu papel não é te dar respostas prontas, mas te ajudar a investigar e questionar o mundo digital. O que você gostaria de explorar hoje?',
  text: 'Olá! Eu sou a Lumia, sua companheira digital no LumenLab. Meu papel não é te dar respostas prontas, mas te ajudar a investigar e questionar o mundo digital. O que você gostaria de explorar hoje?',
  horario: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
};

export const AIAssistantView = () => {
  // Estados do componente em português brasileiro
  const [mensagens, definirMensagens] = useState([MENSAGEM_BOAS_VINDAS]);
  const [entradaTexto, definirEntradaTexto] = useState('');
  const [estaTransmitindo, definirEstaTransmitindo] = useState(false);
  const [idSessao, definirIdSessao] = useState(null);
  const [textoTransmitindo, definirTextoTransmitindo] = useState('');

  // Referências para manipulação do scroll e cancelamento da requisição HTTP
  const referenciaFinalChat = useRef(null);
  const referenciaControladorAbort = useRef(null);

  // Scroll suave automático até o final da conversa quando novas palavras chegam
  useEffect(() => {
    referenciaFinalChat.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensagens, textoTransmitindo, estaTransmitindo]);

  // Recupera o token de autenticação JWT armazenado no navegador
  const obterToken = () => localStorage.getItem('lumenlab_token');

  // Manipula o envio de dúvidas para a Lumia com consumo de streaming SSE
  const lidarComEnvio = useCallback(async (textoParaEnviar) => {
    const textoMensagem = (textoParaEnviar || entradaTexto).trim();
    if (!textoMensagem || estaTransmitindo) return;

    const tokenJwt = obterToken();
    if (!tokenJwt) {
      definirMensagens(anteriores => [...anteriores, {
        id: Date.now().toString(),
        emissor: 'lumia',
        sender: 'lumia',
        texto: 'Você precisa estar conectado à sua conta para conversar comigo. Por favor, faça login!',
        text: 'Você precisa estar conectado à sua conta para conversar comigo. Por favor, faça login!',
        horario: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
      return;
    }

    // Registra visualmente a mensagem do estudante na lista
    const mensagemEstudante = {
      id: Date.now().toString(),
      emissor: 'usuario',
      sender: 'user',
      texto: textoMensagem,
      text: textoMensagem,
      horario: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    definirMensagens(anteriores => [...anteriores, mensagemEstudante]);
    definirEntradaTexto('');
    definirEstaTransmitindo(true);
    definirTextoTransmitindo('');

    // Cria controlador para permitir cancelamento do streaming pelo usuário
    referenciaControladorAbort.current = new AbortController();

    try {
      const respostaHttp = await fetch(`${URL_BASE_API}/chatbot/mensagem/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tokenJwt}`,
        },
        body: JSON.stringify({
          mensagem: textoMensagem,
          message: textoMensagem,
          id_sessao: idSessao,
          session_id: idSessao,
        }),
        signal: referenciaControladorAbort.current.signal,
      });

      if (!respostaHttp.ok) {
        throw new Error(`Erro de resposta do servidor: ${respostaHttp.status}`);
      }

      const leitorStream = respostaHttp.body.getReader();
      const decodificador = new TextDecoder();
      let textoAcumulado = '';

      while (true) {
        const { done, value } = await leitorStream.read();
        if (done) break;

        const blocoBytes = decodificador.decode(value, { stream: true });
        const linhasEvento = blocoBytes.split('\n');

        for (const linha of linhasEvento) {
          if (!linha.startsWith('data: ')) continue;
          try {
            const evento = JSON.parse(linha.slice(6));

            // Início do processamento: captura ou confirmação do ID da sessão
            if (evento.tipo === 'inicio' || evento.type === 'start') {
              definirIdSessao(evento.id_sessao || evento.session_id);
            }
            // Chegada progressiva de tokens da resposta
            else if (evento.tipo === 'token' || evento.type === 'token') {
              textoAcumulado += evento.token;
              definirTextoTransmitindo(textoAcumulado);
            }
            // Conclusão com sucesso do raciocínio socrático
            else if (evento.tipo === 'concluido' || evento.type === 'done') {
              const mensagemFinalLumia = {
                id: (Date.now() + 1).toString(),
                emissor: 'lumia',
                sender: 'lumia',
                texto: textoAcumulado,
                text: textoAcumulado,
                horario: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                intencao: evento.intencao || evento.intent,
                nivelSeguranca: evento.nivel_seguranca || evento.safety_level,
              };
              definirMensagens(anteriores => [...anteriores, mensagemFinalLumia]);
              definirTextoTransmitindo('');
            }
            // Evento de tratamento de erro informado pelo backend
            else if (evento.tipo === 'erro' || evento.type === 'error') {
              const mensagemErro = {
                id: (Date.now() + 1).toString(),
                emissor: 'lumia',
                sender: 'lumia',
                texto: evento.mensagem || evento.message || 'Ocorreu uma instabilidade. Tente novamente.',
                text: evento.mensagem || evento.message || 'Ocorreu uma instabilidade. Tente novamente.',
                horario: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                ehErro: true,
                isError: true,
              };
              definirMensagens(anteriores => [...anteriores, mensagemErro]);
              definirTextoTransmitindo('');
            }
          } catch {
            // Linhas intermediárias do buffer são ignoradas
          }
        }
      }
    } catch (erroExcecao) {
      if (erroExcecao.name === 'AbortError') {
        if (textoAcumulado) {
          definirMensagens(anteriores => [...anteriores, {
            id: (Date.now() + 1).toString(),
            emissor: 'lumia',
            sender: 'lumia',
            texto: textoAcumulado + ' [interrompido]',
            text: textoAcumulado + ' [interrompido]',
            horario: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          }]);
        }
      } else {
        definirMensagens(anteriores => [...anteriores, {
          id: (Date.now() + 1).toString(),
          emissor: 'lumia',
          sender: 'lumia',
          texto: 'Não foi possível se comunicar com a Lumia no momento. Verifique sua conexão.',
          text: 'Não foi possível se comunicar com a Lumia no momento.',
          horario: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          ehErro: true,
          isError: true,
        }]);
      }
    } finally {
      definirEstaTransmitindo(false);
      definirTextoTransmitindo('');
      referenciaControladorAbort.current = null;
    }
  }, [entradaTexto, estaTransmitindo, idSessao]);

  // Cancela a geração em tempo real caso o aluno clique em cancelar
  const lidarComCancelamento = () => {
    referenciaControladorAbort.current?.abort();
  };

  // Envio rápido pelo teclado com tecla Enter
  const lidarComTecla = (eventoTeclado) => {
    if (eventoTeclado.key === 'Enter' && !eventoTeclado.shiftKey) {
      eventoTeclado.preventDefault();
      lidarComEnvio();
    }
  };

  return (
    <div style={{
      maxWidth: '920px',
      margin: '0 auto',
      height: 'calc(100vh - 120px)',
      display: 'flex',
      flexDirection: 'column',
      padding: '16px 20px',
      boxSizing: 'border-box',
    }}>
      {/* Cabeçalho da Assistente */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        paddingBottom: '16px',
        borderBottom: '1.5px solid #ede9fe',
        marginBottom: '16px',
      }}>
        <div style={{
          width: '42px', height: '42px', borderRadius: '12px',
          background: 'linear-gradient(135deg, #7042f4, #a855f7)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(112, 66, 244, 0.3)',
        }}>
          <span style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>✦</span>
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '17px', fontWeight: 700, color: '#1e1435' }}>
              Lumia · Companheira Digital
            </span>
            <span style={{
              fontSize: '11px', fontWeight: 600, padding: '2px 8px', borderRadius: '20px',
              background: '#f3e8ff', color: '#7e22ce', textTransform: 'uppercase', letterSpacing: '0.5px',
            }}>
              Socrática
            </span>
          </div>
          <p style={{ margin: 0, fontSize: '12px', color: '#8b849c', marginTop: '2px' }}>
            Orientação guiada por perguntas reflexivas para autonomia e pensamento crítico.
          </p>
        </div>
      </div>

      {/* Área de rolagem com as mensagens */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        paddingRight: '6px',
      }}>
        {mensagens.map(msg => (
          <BalaoMensagem key={msg.id} msg={msg} />
        ))}

        {/* Efeito de digitação em streaming */}
        {estaTransmitindo && textoTransmitindo && (
          <BalaoMensagem
            msg={{
              id: 'transmitindo',
              emissor: 'lumia',
              sender: 'lumia',
              texto: textoTransmitindo,
              text: textoTransmitindo,
              estaTransmitindo: true,
              isStreaming: true,
            }}
          />
        )}

        {/* Indicador de carregamento enquanto o modelo pensa */}
        {estaTransmitindo && !textoTransmitindo && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '12px 16px', borderRadius: '16px', background: '#f5f3ff',
            width: 'fit-content', border: '1px solid #ede9fe',
          }}>
            <PontosDigitando />
            <span style={{ fontSize: '12px', color: '#7042f4', fontWeight: 500 }}>
              Lumia está pensando na melhor reflexão...
            </span>
          </div>
        )}

        <div ref={referenciaFinalChat} />
      </div>

      {/* Sugestões de Dúvidas Rápidas */}
      {mensagens.length <= 1 && !estaTransmitindo && (
        <div style={{
          display: 'flex', flexWrap: 'wrap', gap: '8px',
          padding: '12px 0 8px 0', borderTop: '1px solid #f3f0ff',
        }}>
          {SUGESTOES_RAPIDAS.map((sugestao, indice) => (
            <BotaoSugestaoRapida
              key={indice}
              texto={sugestao}
              aoClicar={() => lidarComEnvio(sugestao)}
              desabilitado={estaTransmitindo}
            />
          ))}
        </div>
      )}

      {/* Campo de Entrada e Envio */}
      <form
        onSubmit={e => { e.preventDefault(); lidarComEnvio(); }}
        style={{ display: 'flex', gap: '10px', marginTop: '16px' }}
      >
        <input
          type="text"
          placeholder="Tire uma dúvida sobre cibersegurança, IA ou hábitos digitais..."
          value={entradaTexto}
          onChange={e => definirEntradaTexto(e.target.value)}
          onKeyDown={lidarComTecla}
          disabled={estaTransmitindo}
          style={{
            flex: 1, padding: '14px 18px', borderRadius: '12px',
            border: '1.5px solid #e9d5ff', fontSize: '13px', color: '#1e1435',
            background: 'white', outline: 'none', transition: 'border-color 0.2s',
          }}
          onFocus={e => (e.target.style.borderColor = '#7042f4')}
          onBlur={e => (e.target.style.borderColor = '#e9d5ff')}
        />

        {estaTransmitindo ? (
          <button
            type="button"
            onClick={lidarComCancelamento}
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
            disabled={!entradaTexto.trim()}
            style={{
              background: 'linear-gradient(135deg, #7042f4, #6366f1)', color: 'white',
              border: 'none', borderRadius: '12px', padding: '0 26px', fontWeight: 750,
              fontSize: '13px', cursor: !entradaTexto.trim() ? 'not-allowed' : 'pointer',
              opacity: !entradaTexto.trim() ? 0.6 : 1,
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
// Subcomponentes Auxiliares
// ---------------------------------------------------------------------------

const BalaoMensagem = ({ msg }) => {
  const ehUsuario = msg.emissor === 'usuario' || msg.sender === 'user';
  const ehErro = msg.ehErro || msg.isError;
  const textoExibicao = msg.texto || msg.text;

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      alignItems: ehUsuario ? 'flex-end' : 'flex-start',
    }}>
      <div style={{
        maxWidth: '82%', padding: '16px 20px',
        borderRadius: ehUsuario ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
        background: ehUsuario
          ? 'linear-gradient(135deg, #7042f4, #6366f1)'
          : ehErro
            ? '#fee2e2'
            : '#faf8ff',
        color: ehUsuario ? '#ffffff' : ehErro ? '#dc2626' : '#1e1435',
        border: ehUsuario ? 'none' : ehErro ? '1.5px solid #fca5a5' : '1.5px solid #ede9fe',
        fontSize: '14px', lineHeight: 1.7,
        boxShadow: ehUsuario ? '0 4px 16px rgba(112, 66, 244, 0.25)' : 'none',
        whiteSpace: 'pre-wrap',
      }}>
        {textoExibicao}
        {(msg.estaTransmitindo || msg.isStreaming) && (
          <span style={{ display: 'inline-block', animation: 'piscar 1s step-end infinite' }}>|</span>
        )}
      </div>
      {(msg.horario || msg.timestamp) && (
        <span style={{ fontSize: '10px', color: '#8b849c', marginTop: '4px', padding: '0 4px', fontWeight: 500 }}>
          {msg.horario || msg.timestamp}
          {(msg.nivelSeguranca === 'alerta' || msg.safetyLevel === 'warning') && ' · atenção'}
          {(msg.nivelSeguranca === 'perigo_critico' || msg.safetyLevel === 'critical_danger') && ' · emergência'}
        </span>
      )}
    </div>
  );
};

const BotaoSugestaoRapida = ({ texto, aoClicar, desabilitado }) => (
  <button
    onClick={aoClicar}
    disabled={desabilitado}
    style={{
      background: '#ffffff', border: '1.5px solid #e9d5ff', borderRadius: '20px',
      padding: '8px 14px', fontSize: '11px', color: '#5b21b6', fontWeight: 600,
      cursor: desabilitado ? 'not-allowed' : 'pointer', opacity: desabilitado ? 0.5 : 1,
      transition: 'all 0.2s', boxShadow: '0 2px 6px rgba(112, 66, 244, 0.04)',
    }}
    onMouseEnter={e => {
      if (!desabilitado) {
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
    {texto}
  </button>
);

const PontosDigitando = () => (
  <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
    {[0, 1, 2].map(i => (
      <div key={i} style={{
        width: '6px', height: '6px', borderRadius: '50%', background: '#7042f4',
        animation: `puloAnimacao 1.2s ease-in-out ${i * 0.2}s infinite`,
      }} />
    ))}
    <style>{`
      @keyframes puloAnimacao {
        0%, 100% { transform: translateY(0); opacity: 0.4; }
        50% { transform: translateY(-4px); opacity: 1; }
      }
      @keyframes piscar {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
      }
    `}</style>
  </div>
);
