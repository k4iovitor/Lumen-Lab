import React, { useState } from 'react';

export const ModulesView = ({ onNavigate }) => {
  const [selectedModule, setSelectedModule] = useState('cyber');

  return (
    <div style={{ paddingTop: '8px' }}>
      <div className="page-title">
        <div>
          <span className="eyebrow" style={{ color: '#7042f4', fontWeight: 800, fontSize: '11px', letterSpacing: '1px' }}>
            TRILHA COMPLETA DE APRENDIZAGEM
          </span>
          <h1 style={{ marginTop: '8px' }}>Módulos & Fases do LumenLab</h1>
          <p>Explore conceitos práticos sobre segurança digital, IA e controle de atenção.</p>
        </div>
      </div>

      {/* Tabs dos Módulos */}
      <div 
        style={{ 
          display: 'flex', 
          gap: '12px', 
          marginTop: '24px', 
          overflowX: 'auto', 
          paddingBottom: '6px',
          WebkitOverflowScrolling: 'touch'
        }}
      >
        <button
          onClick={() => setSelectedModule('cyber')}
          style={{
            padding: '12px 22px',
            borderRadius: '12px',
            border: '1.5px solid',
            borderColor: selectedModule === 'cyber' ? '#7042f4' : '#e9d5ff',
            background: selectedModule === 'cyber' ? 'linear-gradient(135deg, #7042f4, #6366f1)' : '#ffffff',
            color: selectedModule === 'cyber' ? '#ffffff' : '#31214e',
            fontWeight: 750,
            cursor: 'pointer',
            transition: 'all 0.2s',
            whiteSpace: 'nowrap',
            flexShrink: 0,
            boxShadow: selectedModule === 'cyber' ? '0 4px 16px rgba(112, 66, 244, 0.25)' : 'none',
          }}
        >
          01 · Cybersegurança
        </button>

        <button
          onClick={() => setSelectedModule('ia')}
          style={{
            padding: '12px 22px',
            borderRadius: '12px',
            border: '1.5px solid',
            borderColor: selectedModule === 'ia' ? '#7042f4' : '#e9d5ff',
            background: selectedModule === 'ia' ? 'linear-gradient(135deg, #7042f4, #6366f1)' : '#ffffff',
            color: selectedModule === 'ia' ? '#ffffff' : '#31214e',
            fontWeight: 750,
            cursor: 'pointer',
            transition: 'all 0.2s',
            whiteSpace: 'nowrap',
            flexShrink: 0,
            boxShadow: selectedModule === 'ia' ? '0 4px 16px rgba(112, 66, 244, 0.25)' : 'none',
          }}
        >
          02 · Desmistificando IA
        </button>

        <button
          onClick={() => setSelectedModule('social')}
          style={{
            padding: '12px 22px',
            borderRadius: '12px',
            border: '1.5px solid',
            borderColor: selectedModule === 'social' ? '#7042f4' : '#e9d5ff',
            background: selectedModule === 'social' ? 'linear-gradient(135deg, #7042f4, #6366f1)' : '#ffffff',
            color: selectedModule === 'social' ? '#ffffff' : '#31214e',
            fontWeight: 750,
            cursor: 'pointer',
            transition: 'all 0.2s',
            whiteSpace: 'nowrap',
            flexShrink: 0,
            boxShadow: selectedModule === 'social' ? '0 4px 16px rgba(112, 66, 244, 0.25)' : 'none',
          }}
        >
          03 · Redes Sociais & Higiene
        </button>
      </div>

      {/* MÓDULO 01: Cybersegurança */}
      {selectedModule === 'cyber' && (
        <div style={{ marginTop: '24px' }}>
          <div className="phase-screen cyber">
            <div className="phase-screen-hero">
              <div>
                <span className="eyebrow" style={{ color: '#0284c7', fontWeight: 800 }}>MÓDULO 01 · CYBERSEGURANÇA</span>
                <h1>Aprenda a se proteger no mundo digital</h1>
                <p>Desmascare sites falsos, compreenda a estrutura da internet e blinde suas senhas e dados contra vazamentos.</p>
                <div className="phase-screen-tags">
                  <span>Phishing</span>
                  <span>DNS & Rotas IP</span>
                  <span>Criptografia</span>
                  <span>Privacidade</span>
                </div>
              </div>
              <img src="/images/modulo-01-cyberseguranca.jpeg" alt="Ilustração Cybersegurança" />
            </div>
          </div>

          <div className="phase-map">
            {/* Card 01 */}
            <div 
              className="phase-map-card" 
              style={{ cursor: 'pointer' }}
              onClick={() => onNavigate('fase-detalhe', 'phishing')}
            >
              <div className="phase-map-number">01</div>
              <div>
                <div className="phase-map-card-header">
                  <h3>Caça ao Phishing</h3>
                  <div>
                    <span style={{ fontSize: '11px', background: '#ede8ff', color: '#7042f4', padding: '3px 10px', borderRadius: '12px', fontWeight: 700, border: '1px solid #ddd6fe' }}>
                      Em desenvolvimento
                    </span>
                  </div>
                </div>
                <p>Identifique e-mails maliciosos, endereços clonados e engenharia social antes do primeiro clique.</p>
                <span className="phase-map-format">Fase em desenvolvimento →</span>
              </div>
            </div>

            {/* Card 02: Métodos de privacidade de dados (Referência de Altura) */}
            <div 
              className="phase-map-card" 
              style={{ cursor: 'pointer', borderColor: '#7042f4', boxShadow: '0 6px 20px rgba(112, 66, 244, 0.12)' }}
              onClick={() => onNavigate('fase-detalhe', 'privacidade')}
            >
              <div className="phase-map-number" style={{ background: 'linear-gradient(135deg, #7042f4, #6366f1)', color: '#fff', border: 'none' }}>02</div>
              <div>
                <div className="phase-map-card-header">
                  <h3>Métodos de privacidade de dados</h3>
                  <div>
                    <span style={{ fontSize: '11px', background: '#ede8ff', color: '#7042f4', padding: '3px 10px', borderRadius: '12px', fontWeight: 700, border: '1px solid #ddd6fe' }}>
                      Em desenvolvimento
                    </span>
                  </div>
                </div>
                <p>Seus dados contam uma história. Aprenda a escolher o que compartilhar e como funcionam rastreadores.</p>
                <span className="phase-map-format">Fase em desenvolvimento →</span>
              </div>
            </div>

            {/* Card 03 */}
            <div 
              className="phase-map-card" 
              style={{ cursor: 'pointer' }}
              onClick={() => onNavigate('fase-detalhe', 'senhas')}
            >
              <div className="phase-map-number">03</div>
              <div>
                <div className="phase-map-card-header">
                  <h3>Blindagem de senhas & DNS</h3>
                  <div>
                    <span style={{ fontSize: '11px', background: '#ede8ff', color: '#7042f4', padding: '3px 10px', borderRadius: '12px', fontWeight: 700, border: '1px solid #ddd6fe' }}>
                      Em desenvolvimento
                    </span>
                  </div>
                </div>
                <p>Fortaleça suas senhas com entropia real e entenda o papel dos servidores DNS na navegação segura.</p>
                <span className="phase-map-format">Fase em desenvolvimento →</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MÓDULO 02: Inteligência Artificial */}
      {selectedModule === 'ia' && (
        <div style={{ marginTop: '24px' }}>
          <div className="phase-screen">
            <div className="phase-screen-hero">
              <div>
                <span className="eyebrow" style={{ color: '#7042f4', fontWeight: 800 }}>MÓDULO 02 · INTELIGÊNCIA ARTIFICIAL</span>
                <h1>Desmistificando a Inteligência Artificial</h1>
                <p>Descubra como os modelos de linguagem e visão funcionam, desmascare alucinações e rastreie manipulações visuais.</p>
                <div className="phase-screen-tags">
                  <span>Redes Neurais</span>
                  <span>RAG & LangGraph</span>
                  <span>Caçador de Alucinações</span>
                  <span>OpenCV</span>
                </div>
              </div>
              <img src="/images/modulo-02-ia.jpeg" alt="Ilustração Inteligência Artificial" />
            </div>
          </div>

          <div className="phase-map">
            {/* Card 01: Fundamentos de IA */}
            <div 
              className="phase-map-card" 
              style={{ cursor: 'pointer', borderColor: '#7042f4', boxShadow: '0 6px 20px rgba(112, 66, 244, 0.12)' }}
              onClick={() => onNavigate('fase-detalhe', 'ia')}
            >
              <div className="phase-map-number" style={{ background: 'linear-gradient(135deg, #7042f4, #6366f1)', color: '#fff', border: 'none' }}>01</div>
              <div>
                <div className="phase-map-card-header">
                  <h3>Fundamentos de IA</h3>
                  <div>
                    <span style={{ fontSize: '11px', background: '#ede8ff', color: '#7042f4', padding: '3px 10px', borderRadius: '12px', fontWeight: 700, border: '1px solid #ddd6fe' }}>
                      Em desenvolvimento
                    </span>
                  </div>
                </div>
                <p>Descubra como as máquinas aprendem e por que vale questionar suas respostas antes de confiar nelas.</p>
                <span className="phase-map-format">Fase em desenvolvimento →</span>
              </div>
            </div>

            {/* Card 02 */}
            <div 
              className="phase-map-card" 
              style={{ cursor: 'pointer' }}
              onClick={() => onNavigate('fase-detalhe', 'alucinacao')}
            >
              <div className="phase-map-number">02</div>
              <div>
                <div className="phase-map-card-header">
                  <h3>Caçador de Alucinações</h3>
                  <div>
                    <span style={{ fontSize: '11px', background: '#ede8ff', color: '#7042f4', padding: '3px 10px', borderRadius: '12px', fontWeight: 700, border: '1px solid #ddd6fe' }}>
                      Em desenvolvimento
                    </span>
                  </div>
                </div>
                <p>Investigue fatos com Tavily e ChromaDB para expor erros e alucinações geradas propositalmente por modelos de IA.</p>
                <span className="phase-map-format">Fase em desenvolvimento →</span>
              </div>
            </div>

            {/* Card 03 */}
            <div 
              className="phase-map-card" 
              style={{ cursor: 'pointer' }}
              onClick={() => onNavigate('fase-detalhe', '5erros')}
            >
              <div className="phase-map-number">03</div>
              <div>
                <div className="phase-map-card-header">
                  <h3>Jogo dos 5 Erros de IA</h3>
                  <div>
                    <span style={{ fontSize: '11px', background: '#ede8ff', color: '#7042f4', padding: '3px 10px', borderRadius: '12px', fontWeight: 700, border: '1px solid #ddd6fe' }}>
                      Em desenvolvimento
                    </span>
                  </div>
                </div>
                <p>Detecte manipulações visuais e rastreie anomalias em matrizes de imagens geradas por modelos generativos com OpenCV.</p>
                <span className="phase-map-format">Fase em desenvolvimento →</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MÓDULO 03: Redes Sociais */}
      {selectedModule === 'social' && (
        <div style={{ marginTop: '24px' }}>
          <div className="phase-screen social">
            <div className="phase-screen-hero">
              <div>
                <span className="eyebrow" style={{ color: '#ec4899', fontWeight: 800 }}>MÓDULO 03 · REDES SOCIAIS E ATENÇÃO</span>
                <h1>O que está por trás do seu feed?</h1>
                <p>Evidencie a dinâmica com que os algoritmos retêm sua atenção e desenvolva autonomia com higiene digital e pausas conscientes.</p>
                <div className="phase-screen-tags">
                  <span>Algoritmos de Recomendação</span>
                  <span>Dark Patterns</span>
                  <span>Higiene Digital</span>
                  <span>Foco & Sono</span>
                </div>
              </div>
              <img src="/images/modulo-03-redes-sociais.jpeg" alt="Ilustração Redes Sociais" />
            </div>
          </div>

          <div className="phase-map">
            {/* Card 01 */}
            <div 
              className="phase-map-card" 
              style={{ cursor: 'pointer' }}
              onClick={() => onNavigate('fase-detalhe', 'algoritmos')}
            >
              <div className="phase-map-number">01</div>
              <div>
                <div className="phase-map-card-header">
                  <h3>Dinâmica dos Algoritmos</h3>
                  <div>
                    <span style={{ fontSize: '11px', background: '#ede8ff', color: '#7042f4', padding: '3px 10px', borderRadius: '12px', fontWeight: 700, border: '1px solid #ddd6fe' }}>
                      Em desenvolvimento
                    </span>
                  </div>
                </div>
                <p>Artigo explicativo evidenciando como feeds infinitos são arquitetados para capturar tempo e emoções.</p>
                <span className="phase-map-format">Fase em desenvolvimento →</span>
              </div>
            </div>

            {/* Card 02 */}
            <div 
              className="phase-map-card" 
              style={{ cursor: 'pointer', borderColor: '#ec4899', boxShadow: '0 6px 20px rgba(236, 72, 153, 0.12)' }}
              onClick={() => onNavigate('higiene-digital')}
            >
              <div className="phase-map-number" style={{ background: 'linear-gradient(135deg, #ec4899, #f43f5e)', color: '#fff', border: 'none' }}>02</div>
              <div>
                <div className="phase-map-card-header">
                  <h3>Higiene Digital & Rotina Saudável</h3>
                </div>
                <p>Metas diárias de desconexão, streaks de hábitos offline e pausas conscientes para recuperar o foco.</p>
                <span className="phase-map-format">Dashboard de hábitos · Prática diária →</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
