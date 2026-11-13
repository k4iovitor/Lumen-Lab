import React, { useState, useEffect, useRef } from 'react';
import { apiService } from '../../services/api';

export const AuthScreen = ({ onAuthSuccess }) => {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Gmail digitado na aba de Login
  const [loginGmail, setLoginGmail] = useState('');

  // Dados do formulário de Cadastro
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    dateOfBirth: '',
    gmail: '',
    googleId: '',
    avatarUrl: '',
  });

  const googleBtnRef = useRef(null);
  const [googleClientId, setGoogleClientId] = useState(
    import.meta.env.VITE_GOOGLE_CLIENT_ID || window.__GOOGLE_CLIENT_ID__ || ''
  );

  // Carrega o Google Client ID dinamicamente do backend (.env)
  useEffect(() => {
    const loadConfig = async () => {
      const config = await apiService.getAuthConfig();
      if (config.google_client_id) {
        setGoogleClientId(config.google_client_id);
      }
    };
    loadConfig();
  }, []);

  // Configura a API do Google Identity Services
  useEffect(() => {
    /* global google */
    if (typeof window !== 'undefined' && window.google && googleClientId) {
      try {
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: handleGoogleCredentialResponse,
          auto_select: false,
        });

        if (googleBtnRef.current) {
          window.google.accounts.id.renderButton(googleBtnRef.current, {
            theme: 'outline',
            size: 'large',
            width: 320,
            text: mode === 'login' ? 'signin_with' : 'signup_with',
            shape: 'pill',
            locale: 'pt-BR',
          });
        }
      } catch (err) {
        console.warn('Google Identity Services aguardando configuração:', err);
      }
    }
  }, [mode, googleClientId]);

  // Resposta da API oficial do Google após autorização
  const handleGoogleCredentialResponse = async (response) => {
    if (!response || !response.credential) {
      setError('Não foi possível obter a credencial do Google.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const result = await apiService.googleAuth(response.credential);
      
      if (result.error) {
        setError(result.error);
        setLoading(false);
        return;
      }

      // 1. Se o usuário já existe na base de dados (por Google ID ou Gmail): LOGIN IMEDIATO
      if (result.token && result.profile) {
        localStorage.setItem('lumenlab_token', result.token);
        onAuthSuccess(result.profile);
        return;
      }

      // 2. Se for um estudante 100% novo: preenche os dados e solicita a data de nascimento
      if (result.needs_registration) {
        const googleData = result.google_data || {};
        const nameParts = (googleData.name || '').trim().split(' ');
        const first = nameParts[0] || '';
        const last = nameParts.slice(1).join(' ') || '';

        setFormData(prev => ({
          ...prev,
          gmail: googleData.email || '',
          firstName: first,
          lastName: last,
          googleId: googleData.google_id || '',
          avatarUrl: googleData.picture || '',
        }));

        setMode('register');
        setError('');
      }
    } catch {
      setError('Erro ao processar autenticação com o Google.');
    } finally {
      setLoading(false);
    }
  };

  // Login direto com Gmail digitado ou via popup
  const handleDirectLogin = async (e) => {
    if (e) e.preventDefault();
    const emailToUse = loginGmail.trim().toLowerCase();

    if (!emailToUse || !emailToUse.includes('@')) {
      // Se não digitou e-mail, tenta disparar o popup do Google
      if (typeof window !== 'undefined' && window.google?.accounts?.id?.prompt) {
        window.google.accounts.id.prompt();
        return;
      }
      setError('Por favor, informe seu endereço de Gmail para entrar.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const credential = `email_${emailToUse}`;
      const result = await apiService.googleAuth(credential);

      // 1. Usuário existente encontrado -> LOGIN IMEDIATO
      if (result.token && result.profile) {
        localStorage.setItem('lumenlab_token', result.token);
        onAuthSuccess(result.profile);
        return;
      }

      // 2. Usuário não encontrado no banco -> direciona para criar conta com o e-mail pré-preenchido
      if (result.needs_registration) {
        const parts = emailToUse.split('@')[0].replace(/[._-]/g, ' ').split(' ');
        const first = parts[0]?.charAt(0).toUpperCase() + parts[0]?.slice(1) || '';
        const last = parts.slice(1).map(p => p.charAt(0).toUpperCase() + p.slice(1)).join(' ') || '';

        setFormData(prev => ({
          ...prev,
          gmail: emailToUse,
          firstName: first,
          lastName: last,
          googleId: `manual_google_${emailToUse.replace(/[^a-zA-Z0-9]/g, '_')}`,
        }));

        setMode('register');
      } else if (result.error) {
        setError(result.error);
      }
    } catch {
      setError('Erro ao autenticar com o servidor.');
    } finally {
      setLoading(false);
    }
  };

  // Envio do formulário de criação de conta
  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!formData.firstName.trim()) {
      setError('Por favor, informe seu nome.');
      return;
    }
    if (!formData.lastName.trim()) {
      setError('Por favor, informe seu sobrenome.');
      return;
    }
    if (!formData.dateOfBirth) {
      setError('Por favor, informe sua data de nascimento.');
      return;
    }
    if (!formData.gmail.trim() || !formData.gmail.includes('@')) {
      setError('Por favor, informe um endereço de Gmail válido.');
      return;
    }

    setLoading(true);
    const googleIdToUse = formData.googleId || `manual_google_${formData.gmail.replace(/[^a-zA-Z0-9]/g, '_')}`;

    const payload = {
      first_name: formData.firstName.trim(),
      last_name: formData.lastName.trim(),
      date_of_birth: formData.dateOfBirth,
      gmail: formData.gmail.trim().toLowerCase(),
      google_id: googleIdToUse,
      avatar_url: formData.avatarUrl || '',
    };

    const res = await apiService.register(payload);
    setLoading(false);

    if (res.error) {
      setError(res.error);
      return;
    }

    // Se criou ou atualizou com sucesso, autentica e entra no sistema imediatamente
    if (res.token && res.profile) {
      localStorage.setItem('lumenlab_token', res.token);
      onAuthSuccess(res.profile);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(circle at 10% 20%, #ede8ff 0%, #fae8ff 50%, #f0fdf4 100%)',
      fontFamily: "'DM Sans', 'Manrope', sans-serif",
      padding: '24px',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '460px',
        background: '#ffffff',
        borderRadius: '24px',
        padding: '36px 32px',
        boxShadow: '0 20px 45px rgba(112, 66, 244, 0.14), 0 2px 6px rgba(0,0,0,0.04)',
        border: '1.5px solid #ddd6fe',
      }}>
        {/* Logo LumenLab */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            background: '#ede8ff',
            border: '1px solid #ddd6fe',
            padding: '8px 18px',
            borderRadius: '16px',
            marginBottom: '16px',
          }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#7042f4" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z"></path>
            </svg>
            <span style={{ fontWeight: 800, fontSize: '18px', color: '#1e1435', letterSpacing: '-0.5px' }}>
              LumenLab<span style={{ color: '#ec4899' }}>.</span>
            </span>
          </div>

          <h1 style={{
            fontSize: '24px',
            fontWeight: 850,
            color: '#1e1435',
            margin: '0 0 6px 0',
            letterSpacing: '-0.5px',
          }}>
            {mode === 'login' ? 'Entrar no LumenLab' : 'Criar Conta de Estudante'}
          </h1>
          <p style={{
            fontSize: '13px',
            color: '#635b77',
            margin: 0,
            lineHeight: 1.5,
          }}>
            {mode === 'login'
              ? 'Conecte-se com sua conta Google ou Gmail para acessar a plataforma.'
              : 'Preencha seus dados para começar seu letramento em IA e cybersegurança.'}
          </p>
        </div>

        {/* Mensagem de Erro */}
        {error && (
          <div style={{
            background: '#fff0f2',
            border: '1px solid #ffd6dc',
            color: '#d6334a',
            padding: '12px 14px',
            borderRadius: '12px',
            fontSize: '13px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <span>{error}</span>
          </div>
        )}

        {/* MODO 1: LOGIN */}
        {mode === 'login' ? (
          <div>
            {/* Botão oficial do Google (renderizado pela API Google gsi) */}
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '16px' }}>
              <div ref={googleBtnRef}></div>
            </div>

            {/* Divisor */}
            <div style={{
              margin: '20px 0',
              textAlign: 'center',
              position: 'relative',
            }}>
              <div style={{ height: '1px', background: '#f0ecf6' }}></div>
              <span style={{
                position: 'absolute',
                top: '-9px',
                left: '50%',
                transform: 'translateX(-50%)',
                background: '#ffffff',
                padding: '0 12px',
                fontSize: '11px',
                color: '#a498b5',
                textTransform: 'uppercase',
                fontWeight: 650,
                letterSpacing: '0.8px',
              }}>
                Ou entre com seu Gmail
              </span>
            </div>

            {/* Formulário de Login Direto com Gmail */}
            <form onSubmit={handleDirectLogin}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 750, color: '#1e1435', marginBottom: '6px' }}>
                  Seu Gmail Cadastrado
                </label>
                <input
                  type="email"
                  placeholder="exemplo@gmail.com"
                  value={loginGmail}
                  onChange={(e) => setLoginGmail(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    borderRadius: '12px',
                    border: '1.5px solid #e9d5ff',
                    fontSize: '13px',
                    color: '#1e1435',
                    outline: 'none',
                    boxSizing: 'border-box',
                    background: '#faf8fd',
                    transition: 'border-color 0.2s',
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#7042f4'}
                  onBlur={(e) => e.target.style.borderColor = '#e9d5ff'}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '10px',
                  padding: '14px 18px',
                  background: 'linear-gradient(135deg, #7042f4, #6366f1)',
                  border: 'none',
                  borderRadius: '14px',
                  color: '#ffffff',
                  fontSize: '14px',
                  fontWeight: 750,
                  cursor: loading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: '0 4px 16px rgba(112, 66, 244, 0.3)',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.filter = 'brightness(1.08)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.filter = 'none'; }}
              >
                <span>{loading ? 'Entrando...' : 'Entrar no Sistema'}</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14"></path>
                  <path d="m12 5 7 7-7 7"></path>
                </svg>
              </button>
            </form>

            <div style={{ textAlign: 'center', marginTop: '22px' }}>
              <p style={{ fontSize: '13px', color: '#635b77', margin: '0 0 8px 0' }}>
                Ainda não possui conta de estudante?
              </p>
              <button
                type="button"
                onClick={() => {
                  setError('');
                  setMode('register');
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#7042f4',
                  fontSize: '13px',
                  fontWeight: 750,
                  cursor: 'pointer',
                  textDecoration: 'underline',
                }}
              >
                Criar uma conta agora
              </button>
            </div>
          </div>
        ) : (
          /* MODO 2: CRIAÇÃO DE CONTA (NOME, SOBRENOME, DATA DE NASCIMENTO, GMAIL) */
          <form onSubmit={handleRegisterSubmit}>
            {/* Foto de perfil se capturada via Google */}
            {formData.avatarUrl && (
              <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                <img
                  src={formData.avatarUrl}
                  alt="Foto Google"
                  style={{
                    width: '56px',
                    height: '56px',
                    borderRadius: '50%',
                    border: '2.5px solid #7042f4',
                    boxShadow: '0 4px 14px rgba(112, 66, 244, 0.25)',
                  }}
                />
                <p style={{ fontSize: '11px', color: '#7042f4', margin: '4px 0 0 0', fontWeight: 700 }}>
                  Conta Google Conectada
                </p>
              </div>
            )}

            {/* Campo Nome */}
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 750, color: '#1e1435', marginBottom: '6px' }}>
                Nome
              </label>
              <input
                type="text"
                placeholder="Ex: Júlia"
                value={formData.firstName}
                onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                required
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  borderRadius: '12px',
                  border: '1.5px solid #e9d5ff',
                  fontSize: '13px',
                  color: '#1e1435',
                  outline: 'none',
                  boxSizing: 'border-box',
                  background: '#faf8fd',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => e.target.style.borderColor = '#7042f4'}
                onBlur={(e) => e.target.style.borderColor = '#e9d5ff'}
              />
            </div>

            {/* Campo Sobrenome */}
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 750, color: '#1e1435', marginBottom: '6px' }}>
                Sobrenome
              </label>
              <input
                type="text"
                placeholder="Ex: Lima"
                value={formData.lastName}
                onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                required
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  borderRadius: '12px',
                  border: '1.5px solid #e9d5ff',
                  fontSize: '13px',
                  color: '#1e1435',
                  outline: 'none',
                  boxSizing: 'border-box',
                  background: '#faf8fd',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => e.target.style.borderColor = '#7042f4'}
                onBlur={(e) => e.target.style.borderColor = '#e9d5ff'}
              />
            </div>

            {/* Campo Data de Nascimento */}
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 750, color: '#1e1435', marginBottom: '6px' }}>
                Data de Nascimento
              </label>
              <input
                type="date"
                value={formData.dateOfBirth}
                onChange={(e) => setFormData({ ...formData, dateOfBirth: e.target.value })}
                required
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  borderRadius: '12px',
                  border: '1.5px solid #e9d5ff',
                  fontSize: '13px',
                  color: '#1e1435',
                  outline: 'none',
                  boxSizing: 'border-box',
                  background: '#faf8fd',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => e.target.style.borderColor = '#7042f4'}
                onBlur={(e) => e.target.style.borderColor = '#e9d5ff'}
              />
            </div>

            {/* Campo Gmail */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 750, color: '#1e1435', marginBottom: '6px' }}>
                Gmail do Estudante
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type="email"
                  placeholder="exemplo@gmail.com"
                  value={formData.gmail}
                  onChange={(e) => setFormData({ ...formData, gmail: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    borderRadius: '12px',
                    border: '1.5px solid #e9d5ff',
                    fontSize: '13px',
                    color: '#1e1435',
                    outline: 'none',
                    boxSizing: 'border-box',
                    background: '#faf8fd',
                    transition: 'border-color 0.2s',
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#7042f4'}
                  onBlur={(e) => e.target.style.borderColor = '#e9d5ff'}
                />
              </div>
            </div>

            {/* Botão de Finalizar Cadastro */}
            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                padding: '14px',
                borderRadius: '14px',
                background: 'linear-gradient(135deg, #7042f4, #6366f1)',
                color: '#ffffff',
                border: 'none',
                fontSize: '14px',
                fontWeight: 750,
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1,
                boxShadow: '0 4px 16px rgba(112, 66, 244, 0.3)',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => { if (!loading) e.currentTarget.style.filter = 'brightness(1.08)'; }}
              onMouseLeave={(e) => { if (!loading) e.currentTarget.style.filter = 'none'; }}
            >
              {loading ? 'Conectando...' : 'Finalizar Cadastro e Entrar'}
            </button>

            {/* Voltar para o Login */}
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <button
                type="button"
                onClick={() => {
                  setError('');
                  setMode('login');
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#7042f4',
                  fontSize: '13px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  textDecoration: 'underline',
                }}
              >
                ← Já possui conta? Fazer login
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
