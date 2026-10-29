import React, { useState } from 'react';
import api from '../api';
import { useLanguage } from '../i18n';

export default function CropAnalyzer() {
  const { t } = useLanguage();
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
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
      setError(t('Please select or upload a crop leaf image first.'));
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('image', file);

    try {
      const res = await api.post('/api/crop/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(res.data);
    } catch (err) {
      setError(t(err.response?.data?.error || err.response?.data?.message || 'Failed to analyze crop image.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="module-card">
      <div className="module-header">
        <div className="badge-pill">{t('Module 2')}</div>
        <h2>{t('Crop Image → Crop/Disease Prediction → ML Corrective Recommendation')}</h2>
        <p>{t('Upload a crop or plant leaf image for PyTorch Deep Learning disease classification and targeted corrective recommendations.')}</p>
      </div>

      <div className="grid-2col">
        {/* Upload Box */}
        <div className="card-box">
          <h3>{t('1. Upload Crop / Leaf Image')}</h3>
          <div className="dropzone">
            <input type="file" accept="image/*" onChange={handleFileChange} id="crop-upload" />
            <label htmlFor="crop-upload" className="dropzone-label">
              <span className="drop-icon">🍃</span>
              <span>{file ? file.name : t('Click or Drag Crop Leaf Image Here')}</span>
              <span className="subtext">{t('Supports JPG, PNG, WEBP')}</span>
            </label>
          </div>

          {preview && (
            <div className="image-preview-container">
              <img src={preview} alt="Crop Preview" className="img-preview" />
            </div>
          )}

          <button className="primary-btn" onClick={handleAnalyze} disabled={loading}>
            {loading ? <span className="spinner">⏳ {t('Analyzing Plant Pathogens...')}</span> : `⚡ ${t('Detect Crop Disease & Recommend Treatment')}`}
          </button>

          {error && <div className="error-box">⚠️ {t(error)}</div>}
        </div>

        {/* Results Box */}
        <div className="card-box">
          <h3>{t('2. Disease Classification & Treatment Recommendations')}</h3>

          {!result && !loading && (
            <div className="placeholder-box">
              <span className="placeholder-icon">🩺</span>
              <p>{t('Upload a crop image to identify plant species, detect pathogens/diseases, and receive dataset-driven corrective guidance.')}</p>
            </div>
          )}

          {loading && (
            <div className="loading-box">
              <div className="loader"></div>
              <p>{t('Running Crop Disease Neural Network Model...')}</p>
            </div>
          )}

          {result && result.low_confidence && (
            <div className="warning-box">
              <h4>{t('Low Disease Identification Confidence')}</h4>
              <p>{t(result.message)}</p>
            </div>
          )}

          {result && !result.low_confidence && (
            <div className="results-container">
              {/* Crop & Disease Prediction Card */}
              <div className="res-card highlighted">
                <div className="res-header">
                  <div>
                    <span className="label-title">{t('Identified Crop & Health Condition')}</span>
                    <h3 className="res-value">{t(result.crop_name)} — <span className="condition-highlight">{t(result.condition)}</span></h3>
                  </div>
                </div>

                <div className="meta-pills">
                  <span className={`pill ${result.severity_level.toLowerCase()}`}>{t('Severity:')} {t(result.severity_level)}</span>
                  <span className="pill">{t('Health Status:')} {t(result.health_status)}</span>
                </div>
              </div>

              {/* Treatment Recommendation Card */}
              <div className="res-card ml-card">
                <h4 className="card-sub-header">🛠️ {t('Recommended Corrective Action Plan')}</h4>
                
                <div className="action-step-box">
                  <strong>{t('Recommended Action:')}</strong>
                  <p>{t(result.recommended_action)}</p>
                </div>

                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">{t('Fertilizer Focus')}</span>
                    <span className="info-val">{t(result.recommended_fertilizer)}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">{t('Targeted Pesticide / Fungicide')}</span>
                    <span className="info-val">{t(result.recommended_pesticide)}</span>
                  </div>
                  <div className="info-item full-width">
                    <span className="info-label">{t('Organic / Bio Alternative')}</span>
                    <span className="info-val">{t(result.organic_alternative)}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
