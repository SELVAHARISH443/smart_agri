import React, { useState } from 'react';
import api from '../api';
import { useLanguage } from '../i18n';

export default function SoilAnalyzer() {
  const { t, cropLabel } = useLanguage();
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [crop, setCrop] = useState('Rice');
  const [N, setN] = useState('');
  const [P, setP] = useState('');
  const [K, setK] = useState('');
  const [pH, setPH] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setPreview(URL.createObjectURL(selected));
      setResult(null);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) {
      setError(t('Please select or upload a soil image first.'));
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('image', file);
    if (crop) formData.append('crop', crop);
    if (N) formData.append('N', N);
    if (P) formData.append('P', P);
    if (K) formData.append('K', K);
    if (pH) formData.append('pH', pH);

    try {
      const res = await api.post('/api/soil/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(res.data);
    } catch (err) {
      setError(t(err.response?.data?.error || err.response?.data?.message || 'Failed to analyze soil image.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="module-card">
      <div className="module-header">
        <div className="badge-pill">{t('Module 1')}</div>
        <h2>{t('Soil Image → Soil Type Prediction → ML Fertilizer Recommendation')}</h2>
        <p>{t('Upload a soil image for PyTorch Deep Learning soil classification and ML-driven fertilizer recommendation.')}</p>
      </div>

      <div className="grid-2col">
        {/* Upload & Inputs Box */}
        <div className="card-box">
          <h3>{t('1. Upload Soil Image')}</h3>
          <div className="dropzone">
            <input type="file" accept="image/*" onChange={handleFileChange} id="soil-upload" />
            <label htmlFor="soil-upload" className="dropzone-label">
              <span className="drop-icon">📷</span>
              <span>{file ? file.name : t('Click or Drag Soil Image Here')}</span>
              <span className="subtext">{t('Supports JPG, PNG, WEBP')}</span>
            </label>
          </div>

          {preview && (
            <div className="image-preview-container">
              <img src={preview} alt="Soil Preview" className="img-preview" />
            </div>
          )}

          <div className="optional-inputs-section">
            <h4>{t('Optional Soil Nutrient Measurements (Measured Lab Data)')}</h4>
            <p className="input-tip">{t('If left blank, the ML recommendation model uses agronomic learned advisory defaults for the identified soil type.')}</p>

            <div className="form-grid">
              <div className="form-group">
                <label>{t('Target Crop')}</label>
                <select value={crop} onChange={(e) => setCrop(e.target.value)}>
                  {['Rice', 'Wheat', 'Corn', 'Cotton', 'Groundnut', 'Sugarcane', 'Tomato', 'Potato', 'Banana', 'Onion'].map((cropOption) => (
                    <option key={cropOption} value={cropOption}>
                      {cropOption === 'Corn' ? t('Corn / Maize') : cropLabel(cropOption)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>{t('Nitrogen (N mg/kg)')}</label>
                <input type="number" placeholder={t('e.g. 50')} value={N} onChange={(e) => setN(e.target.value)} />
              </div>

              <div className="form-group">
                <label>{t('Phosphorus (P mg/kg)')}</label>
                <input type="number" placeholder={t('e.g. 35')} value={P} onChange={(e) => setP(e.target.value)} />
              </div>

              <div className="form-group">
                <label>{t('Potassium (K mg/kg)')}</label>
                <input type="number" placeholder={t('e.g. 40')} value={K} onChange={(e) => setK(e.target.value)} />
              </div>

              <div className="form-group">
                <label>{t('Soil pH (4.0 - 9.0)')}</label>
                <input type="number" step="0.1" placeholder={t('e.g. 6.5')} value={pH} onChange={(e) => setPH(e.target.value)} />
              </div>
            </div>
          </div>

          <button className="primary-btn" onClick={handleAnalyze} disabled={loading}>
            {loading ? <span className="spinner">⏳ {t('Processing PyTorch & ML Models...')}</span> : `⚡ ${t('Predict Soil Type & Recommend Fertilizer')}`}
          </button>

          {error && <div className="error-box">⚠️ {t(error)}</div>}
        </div>

        {/* Results Panel */}
        <div className="card-box">
          <h3>{t('2. Deep Learning & ML Prediction Results')}</h3>

          {!result && !loading && (
            <div className="placeholder-box">
              <span className="placeholder-icon">🌱</span>
              <p>{t('Upload a soil image and click analyze to see PyTorch soil classification and Random Forest fertilizer predictions.')}</p>
            </div>
          )}

          {loading && (
            <div className="loading-box">
              <div className="loader"></div>
              <p>{t('Running MobileNetV2 Neural Network & Fertilizer Model...')}</p>
            </div>
          )}

          {result && (
            <div className="results-container">
              {result.low_confidence && (
                <div className="warning-box">
                  <h4>{t('Low Soil Image Classification Confidence')}</h4>
                  <p>{t(result.message)}</p>
                </div>
              )}

              <div className="res-card highlighted">
                <div className="res-header">
                  <div>
                    <span className="label-title">{t('Predicted Soil Type')}</span>
                    <h3 className="res-value">{t(result.predicted_soil_type)}</h3>
                  </div>
                </div>

                <div className="meta-pills">
                  <span className="pill">{t('Health:')} {t(result.soil_health_status)}</span>
                  <span className="pill">{t('Moisture Retention:')} {t(result.moisture_retention)}</span>
                  <span className="pill">{t('Organic Carbon:')} {result.organic_matter_pct}%</span>
                </div>

                {result.top_predictions && result.top_predictions.length > 0 && (
                  <div style={{ marginTop: '1rem' }}>
                    <strong>{t('Top Soil Predictions')}</strong>
                    <div className="meta-pills" style={{ marginTop: '0.5rem' }}>
                      {result.top_predictions.map((item, idx) => (
                        <span key={`${item.soil_type}-${idx}`} className="pill">
                          {t(item.soil_type)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {result.suitable_plants && result.suitable_plants.length > 0 && (
                  <div style={{ marginTop: '1rem' }}>
                    <strong>{t('Suitable Plants / Crops')}</strong>
                    <div className="meta-pills" style={{ marginTop: '0.5rem' }}>
                      {result.suitable_plants.map((plant, idx) => (
                        <span key={`${plant}-${idx}`} className="pill">{cropLabel(plant)}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="res-card ml-card">
                <div className="res-header">
                  <div>
                    <span className="label-title">{t('ML Recommended Fertilizer')}</span>
                    <h3 className="res-value fert-name">{t(result.fertilizer_recommendation.recommended_fertilizer)}</h3>
                  </div>
                </div>

                {result.is_advisory_result && (
                  <div className="advisory-badge">
                    ℹ️ {t('Advisory Recommendation (Learned from Soil Type Dataset profile)')}
                  </div>
                )}

                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">{t('Dosage')}</span>
                    <span className="info-val">{t(result.fertilizer_recommendation.dosage)}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">{t('Application Method')}</span>
                    <span className="info-val">{t(result.fertilizer_recommendation.application_method)}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">{t('Optimal Timing')}</span>
                    <span className="info-val">{t(result.fertilizer_recommendation.best_time)}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">{t('Organic Alternative')}</span>
                    <span className="info-val">{t(result.fertilizer_recommendation.organic_alternative)}</span>
                  </div>
                </div>

                <div className="reason-box">
                  <strong>{t('ML Model Rationale:')}</strong>
                  <p>{t(result.fertilizer_recommendation.recommendation_reason)}</p>
                </div>
              </div>

            </div>
          )}
        </div>
      </div>

    </div>
  );
}
