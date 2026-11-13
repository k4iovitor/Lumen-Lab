import React from 'react';

export const Header = ({ activeSection, breadcrumbText, onNavigateHome, currentUser }) => {
  const getBreadcrumb = () => {
    if (breadcrumbText) return breadcrumbText;
    switch (activeSection) {
      case 'modulos':
        return 'Trilhas / Módulos';
      case 'agente-ia':
        return 'Companheira / Lumia';
      case 'higiene-digital':
        return 'Rotina & Foco';
      case 'fase-detalhe':
        return 'Leitor de Fase';
      default:
        return '';
    }
  };

  // Data dinâmica adaptada ao dia real atual
  const getCurrentFormattedDate = () => {
    const now = new Date();
    const weekday = now.toLocaleDateString('pt-BR', { weekday: 'long' });
    const day = now.toLocaleDateString('pt-BR', { day: 'numeric' });
    const month = now.toLocaleDateString('pt-BR', { month: 'long' });
    
    // Capitaliza o dia da semana: "Quarta-feira, 5 de novembro"
    const capitalizedWeekday = weekday.charAt(0).toUpperCase() + weekday.slice(1);
    return `${capitalizedWeekday}, ${day} de ${month}`;
  };

  const crumb = getBreadcrumb();

  return (
    <header>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {/* Logo visível no Mobile */}
        <div 
          className="mobile-header-brand"
          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
          onClick={onNavigateHome}
        >
          <span style={{ color: '#7042f4', display: 'grid', placeItems: 'center' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z"></path>
            </svg>
          </span>
          <b style={{ color: '#1e1435', fontSize: '18px', letterSpacing: '-0.5px' }}>LumenLab</b>
        </div>

        {/* Breadcrumb em Desktop / Tablet */}
        {crumb && (
          <span 
            className="breadcrumb desktop-breadcrumb" 
            style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', marginLeft: '12px' }}
            onClick={onNavigateHome}
          >
            <span style={{ opacity: 0.6 }}>Início</span>
            <span style={{ opacity: 0.4 }}>/</span>
            <b style={{ color: '#7042f4' }}>{crumb}</b>
          </span>
        )}
      </div>

      <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span className="date desktop-date">{getCurrentFormattedDate()}</span>
        {currentUser && (
          <div
            className="avatar small"
            title={`${currentUser.first_name} ${currentUser.last_name} (${currentUser.gmail})`}
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              background: '#7042f4',
              color: '#ffffff',
              display: 'grid',
              placeItems: 'center',
              fontWeight: 750,
              fontSize: '12px',
              overflow: 'hidden',
              cursor: 'default',
              boxShadow: '0 2px 8px rgba(112, 66, 244, 0.25)',
            }}
          >
            {currentUser.avatar_url ? (
              <img src={currentUser.avatar_url} alt="Avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              `${currentUser.first_name?.[0] || ''}${currentUser.last_name?.[0] || ''}`.toUpperCase()
            )}
          </div>
        )}
      </div>
    </header>
  );
};
