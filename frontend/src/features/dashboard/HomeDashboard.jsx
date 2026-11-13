import React from 'react';

export const HomeDashboard = ({
  onNavigate,
  privacyProgress = 45,
  aiProgress = 25,
}) => {
  return (
    <>
      <div className="page-title">
        <div>
          <h1>Seu próximo nível começa aqui.</h1>
          <p>Que tal descobrir algo novo sobre o mundo digital hoje?</p>
        </div>
      </div>

      <section className="home-dashboard">
        <div className="home-section-heading">
          <div>
            <h2>Continue de onde parou.</h2>
            <p>Suas descobertas de hoje começam por aqui.</p>
          </div>
          <button 
            className="home-text-link"
            onClick={() => onNavigate('modulos')}
          >
            Ver toda a trilha{' '}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
              <path d="M5 12h14m-5-5 5 5-5 5"></path>
            </svg>
          </button>
        </div>

        <div className="home-phase-grid">
          {/* Card 1: Cybersec - Privacidade */}
          <article className="home-phase-card">
            <div className="home-phase-art">
              <img 
                alt="Escudo com uma impressão digital, em tons de azul" 
                src="/images/fase-privacidade.svg" 
              />
              <span className="home-status" style={{ background: '#ede8ff', color: '#7042f4', border: '1.5px solid #ddd6fe', fontWeight: 800 }}>
                Em desenvolvimento
              </span>
            </div>
            <div className="home-phase-body">
              <span className="eyebrow">CYBERSEC · FASE 02</span>
              <h3>Métodos de privacidade de dados</h3>
              <p>Seus dados contam uma história. Aprenda a escolher o que compartilhar.</p>
              <div className="home-progress-label">
                <span>Status da fase</span>
                <b>Em desenvolvimento</b>
              </div>
              <progress 
                value={privacyProgress} 
                max="100" 
                aria-label="Progresso ilustrativo em Métodos de privacidade de dados"
              />
              <button 
                className="home-continue"
                onClick={() => onNavigate('fase-detalhe', 'privacidade')}
              >
                Ver detalhes da fase{' '}
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
                  <path d="M5 12h14m-5-5 5 5-5 5"></path>
                </svg>
              </button>
            </div>
          </article>

          {/* Card 2: IA - Fundamentos */}
          <article className="home-phase-card">
            <div className="home-phase-art">
              <img 
                alt="Chip conectado a uma rede de aprendizado, em tons de roxo" 
                src="/images/fase-fundamentos-ia.svg" 
              />
              <span className="home-status" style={{ background: '#ede8ff', color: '#7042f4', border: '1.5px solid #ddd6fe', fontWeight: 800 }}>
                Em desenvolvimento
              </span>
            </div>
            <div className="home-phase-body">
              <span className="eyebrow">INTELIGÊNCIA ARTIFICIAL · FASE 01</span>
              <h3>Fundamentos de IA</h3>
              <p>Descubra como as máquinas aprendem e por que vale questionar suas respostas.</p>
              <div className="home-progress-label">
                <span>Status da fase</span>
                <b>Em desenvolvimento</b>
              </div>
              <progress 
                value={aiProgress} 
                max="100" 
                aria-label="Progresso ilustrativo em Fundamentos de IA"
              />
              <button 
                className="home-continue"
                onClick={() => onNavigate('fase-detalhe', 'ia')}
              >
                Ver detalhes da fase{' '}
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
                  <path d="M5 12h14m-5-5 5 5-5 5"></path>
                </svg>
              </button>
            </div>
          </article>
        </div>

        <div className="home-bottom-grid">
          {/* Card 3: Recomendação Redes Sociais */}
          <article className="home-recommendation">
            <div className="home-recommendation-copy">
              <span className="eyebrow">QUE TAL EXPLORAR ALGO NOVO?</span>
              <h2>O que está por trás do seu feed?</h2>
              <p>
                Você ainda não começou <strong>Redes Sociais</strong>. Descubra como os algoritmos influenciam o que você vê e recupere sua atenção.
              </p>
              <span className="home-module-meta">Módulo 03 · 2 fases · Não iniciado</span>
              <button 
                className="home-continue"
                onClick={() => onNavigate('modulos')}
              >
                Conhecer módulo{' '}
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
                  <path d="M5 12h14m-5-5 5 5-5 5"></path>
                </svg>
              </button>
            </div>
            <img 
              alt="Balões de conversa representando o módulo de Redes Sociais" 
              src="/images/modulo-03-redes-sociais.jpeg" 
            />
          </article>

          {/* Card 4: Apresentação da NIA */}
          <article className="home-nia">
            <div className="home-nia-top">
              <div className="nia-avatar">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
                  <path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z"></path>
                </svg>
              </div>
              <span>SUA COMPANHEIRA DIGITAL</span>
            </div>
            <h2>Prazer, eu sou a NIA.</h2>
            <p>Uma parceira para explorar ideias, entender conceitos e transformar dúvidas em novas descobertas.</p>
            <div className="home-nia-bubble">“Vamos desvendar o universo digital juntas?”</div>
            <button 
              className="home-continue"
              onClick={() => onNavigate('agente-ia')}
            >
              Conhecer a NIA{' '}
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
                <path d="M5 12h14m-5-5 5 5-5 5"></path>
              </svg>
            </button>
          </article>
        </div>
      </section>
    </>
  );
};

