import React from 'react';

export const Sidebar = ({ activeSection, onNavigate, currentUser, onLogout }) => {
  return (
    <>
      {/* 1. Sidebar Desktop & Tablet */}
      <aside className="desktop-sidebar">
        <a 
          className="brand" 
          href="#" 
          onClick={(e) => { e.preventDefault(); onNavigate('menu'); }}
        >
          <span className="brand-mark">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
              <path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z"></path>
            </svg>
          </span>
          LumenLab<span className="brand-dot">.</span>
        </a>

        <div className="workspace">SEU UNIVERSO DIGITAL</div>

        <nav>
          <button
            className={activeSection === 'menu' ? 'active' : ''}
            onClick={() => onNavigate('menu')}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
              <path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z"></path>
            </svg>
            Menu
          </button>

          <button
            className={activeSection === 'modulos' || activeSection === 'fase-detalhe' ? 'active' : ''}
            onClick={() => onNavigate('modulos')}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 4h6l2 2 2-2h6v15h-6l-2 2-2-2H4Z M12 6v15"></path>
            </svg>
            Módulos
          </button>

          <button
            className={activeSection === 'agente-ia' ? 'active' : ''}
            onClick={() => onNavigate('agente-ia')}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
              <path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z"></path>
            </svg>
            Agente de IA
            <small>NOVO</small>
          </button>

          <button
            className={activeSection === 'higiene-digital' ? 'active' : ''}
            onClick={() => onNavigate('higiene-digital')}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 3C7 2 2 8 5 15s16 5 15-12ZM5 21 16 10"></path>
            </svg>
            Higiene digital
          </button>
        </nav>

        {currentUser && (
          <div className="sidebar-bottom" style={{ marginTop: 'auto', paddingTop: '20px' }}>
            <div
              className="profile"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                borderTop: '1px solid #efedf5',
                padding: '16px 0',
              }}
            >
              <div
                className="avatar"
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: '#7042f4',
                  color: '#ffffff',
                  display: 'grid',
                  placeItems: 'center',
                  fontWeight: 750,
                  fontSize: '12px',
                  overflow: 'hidden',
                  flexShrink: 0,
                  boxShadow: '0 2px 8px rgba(112, 66, 244, 0.3)',
                }}
              >
                {currentUser.avatar_url ? (
                  <img src={currentUser.avatar_url} alt="Avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  `${currentUser.first_name?.[0] || ''}${currentUser.last_name?.[0] || ''}`.toUpperCase()
                )}
              </div>
              <div style={{ flex: 1, minWidth: 0, overflow: 'hidden' }}>
                <b style={{ display: 'block', fontSize: '12px', color: '#1e1435', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {currentUser.first_name} {currentUser.last_name}
                </b>
                <p style={{ margin: '2px 0 0', fontSize: '10px', color: '#81758f', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {currentUser.gmail}
                </p>
              </div>
              <button
                type="button"
                onClick={onLogout}
                title="Sair da conta"
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#9993a8',
                  cursor: 'pointer',
                  padding: '6px',
                  borderRadius: '8px',
                  display: 'grid',
                  placeItems: 'center',
                  transition: 'color 0.2s, background 0.2s',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.color = '#d6334a'; e.currentTarget.style.background = '#fff0f2'; }}
                onMouseLeave={(e) => { e.currentTarget.style.color = '#9993a8'; e.currentTarget.style.background = 'none'; }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                  <polyline points="16 17 21 12 16 7"></polyline>
                  <line x1="21" y1="12" x2="9" y2="12"></line>
                </svg>
              </button>
            </div>
          </div>
        )}
      </aside>

      {/* 2. Barra de Navegação Inferior Nativa para Mobile (Celulares) */}
      <nav className="mobile-bottom-nav">
        <button
          className={activeSection === 'menu' ? 'active' : ''}
          onClick={() => onNavigate('menu')}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z"></path>
          </svg>
          <span>Menu</span>
        </button>

        <button
          className={activeSection === 'modulos' || activeSection === 'fase-detalhe' ? 'active' : ''}
          onClick={() => onNavigate('modulos')}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M4 4h6l2 2 2-2h6v15h-6l-2 2-2-2H4Z M12 6v15"></path>
          </svg>
          <span>Módulos</span>
        </button>

        <button
          className={activeSection === 'agente-ia' ? 'active' : ''}
          onClick={() => onNavigate('agente-ia')}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z"></path>
          </svg>
          <span>Agente IA</span>
          <small>NOVO</small>
        </button>

        <button
          className={activeSection === 'higiene-digital' ? 'active' : ''}
          onClick={() => onNavigate('higiene-digital')}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M20 3C7 2 2 8 5 15s16 5 15-12ZM5 21 16 10"></path>
          </svg>
          <span>Higiene</span>
        </button>

        {currentUser && (
          <button onClick={onLogout} title="Sair da conta" style={{ color: '#d6334a' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
            <span>Sair</span>
          </button>
        )}
      </nav>
    </>
  );
};
