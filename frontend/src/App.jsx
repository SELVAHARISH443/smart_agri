import React, { useState, useEffect } from 'react';
import api from './api';
import SoilAnalyzer from './components/SoilAnalyzer';
import CropAnalyzer from './components/CropAnalyzer';
import CropSeason from './components/CropSeason';
import AuthPage from './components/AuthPage';
import { LanguageProvider, useLanguage } from './i18n';
import './styles.css';

function AppContent() {
  const [activeTab, setActiveTab] = useState('soil');
  const [healthStatus, setHealthStatus] = useState(null);
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const { language, setLanguage, t } = useLanguage();

  useEffect(() => {
    checkSession();
    checkHealth();
  }, []);

  const checkSession = async () => {
    try {
      const res = await api.get('/api/auth/me');
      setUser(res.data.user);
    } catch (err) {
      if (err.response?.status !== 401) {
        console.error('Unable to verify login session:', err);
      }
      setUser(null);
    } finally {
      setAuthLoading(false);
    }
  };

  const checkHealth = async () => {
    try {
      const res = await api.get('/api/health');
      setHealthStatus(res.data);
    } catch (err) {
      console.error('Backend API offline or unreachable:', err);
      setHealthStatus({ status: 'offline' });
    }
  };

  const handleLogout = async () => {
    try {
      await api.post('/api/auth/logout');
      setUser(null);
    } catch (err) {
      console.error('Unable to log out:', err);
    }
  };

  if (authLoading) {
    return (
      <div className="auth-loading" role="status">
        <span className="loader" />
        <span>{t('Checking your account...')}</span>
      </div>
    );
  }

  if (!user) {
    return (
      <>
        <LanguageToggle language={language} setLanguage={setLanguage} />
        <AuthPage onAuthenticated={setUser} />
      </>
    );
  }

  return (
    <div className="app-shell">
      {/* Top Navigation Bar */}
      <header className="top-nav">
        <div className="nav-container">
          <div className="brand-logo">
            <span className="logo-icon">🌿</span>
            <div className="brand-titles">
              <h1>AgriSmart AI</h1>
              <span className="sub-title">{t('Dataset & Machine Learning Driven System')}</span>
            </div>
          </div>

          <div className="health-badge">
            <span className={`status-dot ${healthStatus?.status === 'online' ? 'online' : 'offline'}`}></span>
            <span className="status-text">
              {healthStatus?.status === 'online' ? t('ML Models Online') : t('Connecting ML Backend...')}
            </span>
          </div>
          <div className="account-controls">
            <LanguageToggle language={language} setLanguage={setLanguage} />
            <span className="account-email">{user.email}</span>
            <button type="button" className="logout-btn" onClick={handleLogout}>{t('Log out')}</button>
          </div>
        </div>
      </header>

      {/* Main Container & Module Tabs */}
      <main className="main-content">
        <div className="module-tabs-bar">
          <button
            className={`tab-btn ${activeTab === 'soil' ? 'active' : ''}`}
            onClick={() => setActiveTab('soil')}
          >
            <span className="tab-icon">🧪</span>
            <div className="tab-labels">
              <span className="tab-title">{t('Page 1: Soil Analysis')}</span>
              <span className="tab-sub">{t('Soil Image → Soil Type → ML Fertilizer')}</span>
            </div>
          </button>

          <button
            className={`tab-btn ${activeTab === 'crop' ? 'active' : ''}`}
            onClick={() => setActiveTab('crop')}
          >
            <span className="tab-icon">🩺</span>
            <div className="tab-labels">
              <span className="tab-title">{t('Page 2: Crop Analyzer')}</span>
              <span className="tab-sub">{t('Crop Image → Pathogen/Disease → ML Action')}</span>
            </div>
          </button>

          <button
            className={`tab-btn ${activeTab === 'season' ? 'active' : ''}`}
            onClick={() => setActiveTab('season')}
          >
            <span className="tab-icon">🌾</span>
            <div className="tab-labels">
              <span className="tab-title">{t('Page 3: Crop Season')}</span>
              <span className="tab-sub">{t('Crop Name → Sowing/Harvest Dataset')}</span>
            </div>
          </button>
        </div>

        {/* Render Active Module */}
        <div className="tab-viewport">
          {activeTab === 'soil' && <SoilAnalyzer />}
          {activeTab === 'crop' && <CropAnalyzer />}
          {activeTab === 'season' && <CropSeason />}
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-container">
          <p>{t('© 2026 AgriSmart AI System — Powered by PyTorch, Scikit-Learn & Agricultural Datasets')}</p>
          <span className="footer-tag">{t('100% Machine Learning & Dataset Driven Architecture')}</span>
        </div>
      </footer>
    </div>
  );
}

function LanguageToggle({ language, setLanguage }) {
  return (
    <div className="language-toggle" role="group" aria-label={language === 'ta' ? 'மொழி' : 'Language'}>
      <button
        type="button"
        className={language === 'en' ? 'active' : ''}
        aria-pressed={language === 'en'}
        onClick={() => setLanguage('en')}
      >
        English
      </button>
      <button
        type="button"
        className={language === 'ta' ? 'active' : ''}
        aria-pressed={language === 'ta'}
        onClick={() => setLanguage('ta')}
      >
        தமிழ்
      </button>
    </div>
  );
}

export default function App() {
  return (
    <LanguageProvider>
      <AppContent />
    </LanguageProvider>
  );
}
