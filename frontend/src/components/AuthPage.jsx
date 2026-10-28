import React, { useState } from 'react';
import axios from 'axios';
import { useLanguage } from '../i18n';

export default function AuthPage({ onAuthenticated }) {
  const { t } = useLanguage();
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const isRegistering = mode === 'register';

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      const endpoint = isRegistering ? '/api/auth/register' : '/api/auth/login';
      const response = await axios.post(endpoint, { email, password });
      onAuthenticated(response.data.user);
    } catch (requestError) {
      setError(
        requestError.response?.data?.error ||
        t('Unable to connect to the account service. Please try again.')
      );
    } finally {
      setLoading(false);
    }
  };

  const changeMode = (nextMode) => {
    setMode(nextMode);
    setError('');
    setPassword('');
  };

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="auth-title">
        <div className="auth-brand">
          <span className="auth-logo" aria-hidden="true">🌿</span>
          <span>AgriSmart AI</span>
        </div>
        <p className="auth-eyebrow">{t('SMART AGRICULTURE PLATFORM')}</p>
        <h1 id="auth-title">{isRegistering ? t('Create your account') : t('Welcome back')}</h1>
        <p className="auth-description">
          {isRegistering
            ? t('Register with your email and password to access the agriculture dashboard.')
            : t('Log in to continue to your agriculture dashboard.')}
        </p>

        <div className="auth-tabs" role="tablist" aria-label={t('Account options')}>
          <button
            type="button"
            role="tab"
            aria-selected={!isRegistering}
            className={!isRegistering ? 'active' : ''}
            onClick={() => changeMode('login')}
          >
            {t('Log in')}
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={isRegistering}
            className={isRegistering ? 'active' : ''}
            onClick={() => changeMode('register')}
          >
            {t('Register')}
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="auth-email">{t('Email address')}</label>
          <input
            id="auth-email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder={t('you@example.com')}
            maxLength={254}
            required
          />

          <label htmlFor="auth-password">{t('Password')}</label>
          <input
            id="auth-password"
            type="password"
            autoComplete={isRegistering ? 'new-password' : 'current-password'}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder={isRegistering ? t('At least 8 characters') : t('Enter your password')}
            minLength={isRegistering ? 8 : undefined}
            maxLength={128}
            required
          />

          {error && <div className="error-box auth-error" role="alert">{error}</div>}

          <button className="primary-btn auth-submit" type="submit" disabled={loading}>
            {loading
              ? t('Please wait...')
              : isRegistering ? t('Create account') : t('Log in')}
          </button>
        </form>

        {isRegistering && (
          <p className="auth-note">{t('Use a password with at least 8 characters.')}</p>
        )}
      </section>
    </main>
  );
}
