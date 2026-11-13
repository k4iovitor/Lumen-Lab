import React, { useState, useEffect } from 'react';
import { apiService } from './services/api';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { HomeDashboard } from './features/dashboard/HomeDashboard';
import { ModulesView } from './features/modules/ModulesView';
import { PhaseDetailView } from './features/modules/PhaseDetailView';
import { RoutineDashboard } from './features/social-hygiene/RoutineDashboard';
import { AIAssistantView } from './features/lumia-assistant/AIAssistantView';
import { AuthScreen } from './features/auth/AuthScreen';

export const App = () => {
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  const [activeSection, setActiveSection] = useState('menu');
  const [selectedPhaseId, setSelectedPhaseId] = useState('privacidade');
  const [privacyProgress, setPrivacyProgress] = useState(45);
  const [aiProgress, setAiProgress] = useState(25);

  // Verifica se o estudante já possui sessão autenticada com JWT válido
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('lumenlab_token');
      if (token) {
        const profile = await apiService.getProfile();
        if (profile) {
          setCurrentUser(profile);
        } else {
          localStorage.removeItem('lumenlab_token');
        }
      }
      setAuthLoading(false);
    };

    checkAuth();
  }, []);

  // Carrega o estado de navegação do backend
  useEffect(() => {
    if (!currentUser) return;
    const fetchState = async () => {
      const data = await apiService.getInitialState();
      if (data.activeSection) setActiveSection(data.activeSection);
      if (data.privacyProgress) setPrivacyProgress(data.privacyProgress);
      if (data.aiProgress) setAiProgress(data.aiProgress);
    };
    fetchState();
  }, [currentUser]);

  // Logout
  const handleLogout = () => {
    localStorage.removeItem('lumenlab_token');
    setCurrentUser(null);
    setActiveSection('menu');
  };

  // Transição de seções
  const handleNavigate = (section, phaseId) => {
    setActiveSection(section);
    if (phaseId) {
      setSelectedPhaseId(phaseId);
    }
    apiService.switchSection(section);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleUpdateProgress = (phaseId, progress) => {
    if (phaseId === 'privacidade') {
      setPrivacyProgress(progress);
    } else if (phaseId === 'ia') {
      setAiProgress(progress);
    }
  };

  // Carregamento inicial de verificação de autenticação
  if (authLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        background: '#f8f6fc',
        fontFamily: "'DM Sans', sans-serif",
        color: '#7959bc',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '3px solid #e6dff1',
            borderTopColor: '#7959bc',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
            margin: '0 auto 12px',
          }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          <span style={{ fontSize: '13px', fontWeight: 600 }}>Carregando LumenLab...</span>
        </div>
      </div>
    );
  }

  // Se não estiver autenticado, exibe a tela de login / criação de conta com Gmail
  if (!currentUser) {
    return <AuthScreen onAuthSuccess={(profile) => setCurrentUser(profile)} />;
  }

  return (
    <div className="app">
      {/* Sidebar Lateral */}
      <Sidebar 
        activeSection={activeSection} 
        onNavigate={handleNavigate}
        currentUser={currentUser}
        onLogout={handleLogout}
      />

      {/* Conteúdo Principal */}
      <main>
        <Header 
          activeSection={activeSection} 
          onNavigateHome={() => handleNavigate('menu')} 
          currentUser={currentUser}
        />

        <div className="content">
          {activeSection === 'menu' && (
            <HomeDashboard 
              onNavigate={handleNavigate} 
              privacyProgress={privacyProgress} 
              aiProgress={aiProgress} 
            />
          )}

          {activeSection === 'modulos' && (
            <ModulesView onNavigate={handleNavigate} />
          )}

          {activeSection === 'fase-detalhe' && (
            <PhaseDetailView 
              phaseId={selectedPhaseId} 
              onNavigate={handleNavigate}
              onUpdateProgress={handleUpdateProgress} 
            />
          )}

          {activeSection === 'higiene-digital' && (
            <RoutineDashboard />
          )}

          {activeSection === 'agente-ia' && (
            <AIAssistantView />
          )}

          <footer>
            <span>
              <span className="footer-logo">LumenLab.</span> Conhecimento que conecta. Escolhas que transformam.
            </span>
          </footer>
        </div>
      </main>
    </div>
  );
};

export default App;
