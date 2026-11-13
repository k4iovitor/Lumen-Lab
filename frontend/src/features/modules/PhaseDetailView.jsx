import React from 'react';

export const PhaseDetailView = ({
  phaseId = 'privacidade',
  onNavigate,
}) => {
  // Informações detalhadas de cada fase mapeada no sistema
  const getPhaseData = () => {
    switch (phaseId) {
      case 'phishing':
        return {
          moduleTag: 'CYBERSEC · FASE 01',
          title: 'Caça ao Phishing',
          desc: 'Identifique sites clonados, e-mails com links encurtados e armadilhas de engenharia social antes de clicar.',
          img: '/images/modulo-01-cyberseguranca.jpeg',
          tags: ['Phishing', 'URL Spoofing', 'Engenharia Social'],
        };
      case 'privacidade':
        return {
          moduleTag: 'CYBERSEC · FASE 02',
          title: 'Métodos de privacidade de dados',
          desc: 'Seus dados contam uma história. Aprenda a escolher o que compartilhar e como os rastreadores operam.',
          img: '/images/fase-privacidade.svg',
          tags: ['Cookies de Terceiros', 'Metadados', 'LGPD Estudantil', 'Modo Anônimo'],
        };
      case 'senhas':
        return {
          moduleTag: 'CYBERSEC · FASE 03',
          title: 'Blindagem de senhas & DNS',
          desc: 'Fortaleça suas senhas com entropia real e entenda o papel dos servidores DNS na navegação segura.',
          img: '/images/modulo-01-cyberseguranca.jpeg',
          tags: ['Entropia de Senhas', 'Servidores DNS', 'Autenticação 2FA', 'Criptografia'],
        };
      case 'ia':
        return {
          moduleTag: 'INTELIGÊNCIA ARTIFICIAL · FASE 01',
          title: 'Fundamentos de IA',
          desc: 'Descubra como as máquinas aprendem, o que são redes neurais e por que vale questionar suas respostas.',
          img: '/images/fase-fundamentos-ia.svg',
          tags: ['Machine Learning', 'Pesos & Viéses', 'Previsão Estatística'],
        };
      case 'alucinacao':
        return {
          moduleTag: 'INTELIGÊNCIA ARTIFICIAL · FASE 02',
          title: 'Caçador de Alucinações',
          desc: 'Investigue fatos e explore como modelos de linguagem podem inventar dados convincentes e falsos.',
          img: '/images/modulo-02-ia.jpeg',
          tags: ['RAG', 'Alucinações de LLM', 'Checagem de Fatos', 'ChromaDB'],
        };
      case '5erros':
        return {
          moduleTag: 'INTELIGÊNCIA ARTIFICIAL · FASE 03',
          title: 'Jogo dos 5 Erros de IA',
          desc: 'Detecte manipulações visuais e rastreie anomalias em matrizes de imagens geradas por modelos generativos.',
          img: '/images/modulo-02-ia.jpeg',
          tags: ['Visão Computacional', 'Deepfakes', 'Artefatos de Imagem', 'OpenCV'],
        };
      case 'algoritmos':
        return {
          moduleTag: 'REDES SOCIAIS · FASE 01',
          title: 'Dinâmica dos Algoritmos',
          desc: 'Evidencie a dinâmica com que os feeds infinitos são arquitetados para capturar tempo, atenção e emoções.',
          img: '/images/modulo-03-redes-sociais.jpeg',
          tags: ['Feed Infinito', 'Dark Patterns', 'Economia da Atenção', 'Dopamina'],
        };
      default:
        return {
          moduleTag: 'TRILHA DE APRENDIZAGEM',
          title: 'Fase de Aprendizado',
          desc: 'Conteúdo formativo para desenvolver autonomia e letramento digital.',
          img: '/images/fase-privacidade.svg',
          tags: ['Letramento Digital', 'Segurança', 'Tecnologia'],
        };
    }
  };

  const data = getPhaseData();

  return (
    <div className="phase-screen" style={{ paddingTop: '8px' }}>
      {/* Barra de Navegação */}
      <div className="phase-screen-nav">
        <button
          className="back-modules"
          onClick={() => onNavigate('modulos')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: '#ede8ff',
            color: '#7042f4',
            border: '1.5px solid #ddd6fe',
            borderRadius: '10px',
            padding: '10px 18px',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          ← Voltar para todos os módulos
        </button>
        <span className="eyebrow" style={{ color: '#7042f4', fontWeight: 800 }}>
          {data.moduleTag}
        </span>
      </div>

      {/* Hero da Fase */}
      <div className="phase-screen-hero" style={{ minHeight: '240px', marginTop: '16px' }}>
        <div>
          <h1>{data.title}</h1>
          <p>{data.desc}</p>
          <div className="phase-screen-tags">
            {data.tags.map((tag, idx) => (
              <span key={idx}>{tag}</span>
            ))}
          </div>
        </div>
        <img src={data.img} alt={data.title} style={{ maxWidth: '45%' }} />
      </div>

      {/* Cartão Gigante: Em Desenvolvimento */}
      <div
        className="phase-under-development-card"
        style={{
          background: 'linear-gradient(135deg, #ffffff 0%, #faf8ff 100%)',
          border: '2.5px dashed #c4b5fd',
          borderRadius: '24px',
          padding: '56px 36px',
          margin: '28px auto',
          maxWidth: '900px',
          textAlign: 'center',
          boxShadow: '0 12px 36px rgba(112, 66, 244, 0.08)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Efeitos de iluminação sutil de fundo */}
        <div
          style={{
            position: 'absolute',
            width: '320px',
            height: '320px',
            background: 'radial-gradient(circle, rgba(112, 66, 244, 0.12) 0%, transparent 70%)',
            top: '-80px',
            right: '-80px',
            borderRadius: '50%',
            pointerEvents: 'none',
          }}
        />
        <div
          style={{
            position: 'absolute',
            width: '280px',
            height: '280px',
            background: 'radial-gradient(circle, rgba(236, 72, 153, 0.1) 0%, transparent 70%)',
            bottom: '-60px',
            left: '-60px',
            borderRadius: '50%',
            pointerEvents: 'none',
          }}
        />

        {/* Ícone de Construção sem emoji */}
        <div
          style={{
            width: '80px',
            height: '80px',
            borderRadius: '24px',
            background: 'linear-gradient(135deg, #ede8ff 0%, #fae8ff 100%)',
            border: '2px solid #ddd6fe',
            display: 'grid',
            placeItems: 'center',
            margin: '0 auto 22px',
            boxShadow: '0 8px 24px rgba(112, 66, 244, 0.2)',
            color: '#7042f4',
          }}
        >
          <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>
          </svg>
        </div>

        {/* Badge Eyebrow */}
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: '#ede8ff', border: '1.5px solid #ddd6fe', padding: '6px 18px', borderRadius: '24px', marginBottom: '18px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#7042f4', display: 'inline-block' }}></span>
          <span style={{ fontSize: '11px', fontWeight: 800, color: '#7042f4', letterSpacing: '1.2px' }}>
            EM DESENVOLVIMENTO
          </span>
        </div>

        {/* Título Gigante */}
        <h2
          style={{
            fontSize: '28px',
            fontWeight: 850,
            color: '#1e1435',
            letterSpacing: '-0.8px',
            marginBottom: '14px',
          }}
        >
          Esta Fase está em Desenvolvimento
        </h2>

        {/* Mensagem direta sem recomendação da Lumia */}
        <p
          style={{
            fontSize: '15px',
            lineHeight: 1.8,
            color: '#554470',
            maxWidth: '620px',
            margin: '0 auto 32px',
          }}
        >
          Os simuladores práticos, lições interativas e atividades desta fase estão sendo construídos e estarão disponíveis em breve.
        </p>

        {/* Botão de Retorno */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <button
            onClick={() => onNavigate('modulos')}
            style={{
              background: 'linear-gradient(135deg, #7042f4, #6366f1)',
              color: '#ffffff',
              border: 'none',
              borderRadius: '12px',
              padding: '14px 32px',
              fontSize: '14px',
              fontWeight: 750,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 16px rgba(112, 66, 244, 0.3)',
              transition: 'all 0.2s',
            }}
            onMouseEnter={e => (e.currentTarget.style.transform = 'translateY(-2px)')}
            onMouseLeave={e => (e.currentTarget.style.transform = 'none')}
          >
            <span>Voltar para todos os módulos</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

