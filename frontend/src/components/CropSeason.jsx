import React, { useState, useEffect } from 'react';
import api from '../api';
import { useLanguage } from '../i18n';

export default function CropSeason() {
  const { t, cropLabel } = useLanguage();
  const [crop, setCrop] = useState('Rice');
  const [region, setRegion] = useState('');
  const [availableCrops, setAvailableCrops] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCrops();
    handleSearch('Rice', '');
  }, []);

  const fetchCrops = async () => {
    try {
      const res = await api.get('/api/crops');
      if (res.data.crops) {
        setAvailableCrops(res.data.crops);
      }
    } catch (err) {
      console.error('Failed to load crop list:', err);
    }
  };

  const handleSearch = async (targetCrop = crop, targetRegion = region) => {
    if (!targetCrop) {
      setError(t('Please select or enter a crop name.'));
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await api.get('/api/crop/season', {
        params: { crop: targetCrop, region: targetRegion }
      });

      if (res.data.found === false) {
        setError(t('Crop not found in season dataset.'));
        setResult(null);
      } else {
        setResult(res.data);
      }
    } catch (err) {
      setError(t(err.response?.data?.error || 'Failed to retrieve crop season dataset recommendations.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="module-card">
      <div className="module-header">
        <div className="badge-pill">{t('Module 3')}</div>
        <h2>{t('Crop Name → Season, Sowing & Harvesting Recommendation')}</h2>
        <p>{t('Query our comprehensive dataset of agricultural crops and regional growing periods across seasons (Kharif, Rabi, Zaid).')}</p>
      </div>

      <div className="search-filter-bar">
        <div className="form-group inline">
          <label>{t('Select or Enter Crop Name:')}</label>
          <input
            type="text"
            list="crop-options"
            value={crop}
            onChange={(e) => setCrop(e.target.value)}
            placeholder={t('Type or select crop (e.g. Rice, Wheat, Cotton...)')}
          />
          <datalist id="crop-options">
            {availableCrops.map((c) => (
              <option key={c} value={c}>{cropLabel(c)}</option>
            ))}
          </datalist>
        </div>

        <div className="form-group inline">
          <label>{t('State / Region (Optional):')}</label>
          <input
            type="text"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            placeholder={t('e.g. Punjab, West Bengal, Maharashtra')}
          />
        </div>

        <button className="primary-btn search-btn" onClick={() => handleSearch()} disabled={loading}>
          {loading ? `🔍 ${t('Searching Dataset...')}` : `🌾 ${t('Find Seasonal Period')}`}
        </button>
      </div>

      {error && <div className="error-box mt-16">⚠️ {t(error)}</div>}

      {/* Dataset Results */}
      {result && (
        <div className="season-results-container">
          <div className="season-hero-card">
            <div className="hero-season-title">
              <span className="crop-tag">{cropLabel(result.crop)}</span>
              <h3>{t('Suitable Growing Season:')} <span className="season-highlight">{t(result.primary_season)}</span></h3>
            </div>

            <div className="season-periods-grid">
              <div className="period-box sowing">
                <span className="period-icon">🌱</span>
                <div>
                  <span className="period-label">{t('Sowing Period')}</span>
                  <span className="period-val">{result.sowing_period}</span>
                </div>
              </div>

              <div className="period-box harvest">
                <span className="period-icon">🌾</span>
                <div>
                  <span className="period-label">{t('Harvesting Period')}</span>
                  <span className="period-val">{result.harvesting_period}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Environmental Requirements */}
          <div className="requirements-card">
            <h4>🌡️ {t('Agro-Climatic Requirements & Soil Suitability')}</h4>
            <div className="req-grid">
              <div className="req-item">
                <span className="req-label">{t('Optimal Temperature')}</span>
                <span className="req-val">{result.temperature_requirement}</span>
              </div>
              <div className="req-item">
                <span className="req-label">{t('Rainfall Requirement')}</span>
                <span className="req-val">{result.rainfall_requirement}</span>
              </div>
              <div className="req-item">
                <span className="req-label">{t('Water Requirement')}</span>
                <span className="req-val">{result.water_requirement}</span>
              </div>
              <div className="req-item full">
                <span className="req-label">{t('Compatible Soil Types')}</span>
                <span className="req-val">{t(result.suitable_soil_types)}</span>
              </div>
            </div>
          </div>

          {/* Regional Records Table */}
          {result.regional_breakdown && result.regional_breakdown.length > 1 && (
            <div className="regional-table-card">
              <h4>🗺️ {t('Regional Variations')} ({result.regional_records_count} {t('Records Found')})</h4>
              <div className="table-responsive">
                <table className="dataset-table">
                  <thead>
                    <tr>
                      <th>{t('State / Zone')}</th>
                      <th>{t('Season')}</th>
                      <th>{t('Sowing Window')}</th>
                      <th>{t('Harvesting Window')}</th>
                      <th>{t('Temp Range')}</th>
                      <th>{t('Soil Types')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.regional_breakdown.map((row, idx) => (
                      <tr key={idx}>
                        <td><strong>{row.state}</strong> ({row.region})</td>
                        <td><span className="badge-season">{t(row.season)}</span></td>
                        <td>{row.sowing_month}</td>
                        <td>{row.harvesting_month}</td>
                        <td>{row.temperature_range}</td>
                        <td>{t(row.suitable_soil_types)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
}
