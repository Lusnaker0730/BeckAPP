import React, { useState, useEffect } from 'react';
import axios from '../../utils/axiosConfig';
import './SurvivalAnalysis.css';

function SurvivalAnalysis() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    // 分析參數
    const [diagnosisCode, setDiagnosisCode] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [maxFollowUpDays, setMaxFollowUpDays] = useState(1825); // 5年
    const [stratifyBy, setStratifyBy] = useState('');
    
    // 分析結果
    const [analysisType, setAnalysisType] = useState('kaplan-meier'); // kaplan-meier, cox, summary
    const [kmData, setKmData] = useState(null);
    const [kmPlot, setKmPlot] = useState(null);
    const [coxData, setCoxData] = useState(null);
    const [summaryData, setSummaryData] = useState(null);
    
    // 可用診斷列表
    const [diagnosesList, setDiagnosesList] = useState([]);

    useEffect(() => {
        fetchDiagnosesList();
    }, []);

    const fetchDiagnosesList = async () => {
        try {
            const response = await axios.get('/api/analytics/available-diagnoses');
            setDiagnosesList(response.data);
        } catch (err) {
            console.error('Error fetching diagnoses list:', err);
        }
    };

    const handleAnalyze = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const params = {
                diagnosis_code: diagnosisCode,
                start_date: startDate,
                end_date: endDate,
                max_follow_up_days: maxFollowUpDays,
                stratify_by: stratifyBy || undefined
            };
            
            if (analysisType === 'kaplan-meier') {
                // 獲取 KM 數據
                const kmResponse = await axios.get('/api/survival/kaplan-meier', { params });
                
                // 檢查是否返回錯誤
                if (kmResponse.data.error) {
                    let errorMsg = kmResponse.data.message;
                    if (kmResponse.data.actual_date_range) {
                        const { start, end, total_records } = kmResponse.data.actual_date_range;
                        errorMsg += `\n\n📊 實際數據範圍：\n`;
                        errorMsg += `• 開始日期：${new Date(start).toLocaleDateString('zh-TW')}\n`;
                        errorMsg += `• 結束日期：${new Date(end).toLocaleDateString('zh-TW')}\n`;
                        errorMsg += `• 記錄總數：${total_records} 筆\n\n`;
                    }
                    errorMsg += `💡 建議：${kmResponse.data.suggestion}`;
                    setError(errorMsg);
                    setKmData(null);
                    setKmPlot(null);
                } else {
                    setKmData(kmResponse.data);
                    
                    // 獲取 KM 圖表
                    try {
                        const plotResponse = await axios.get('/api/survival/kaplan-meier/plot', { params });
                        setKmPlot(plotResponse.data.image);
                    } catch (plotErr) {
                        // 圖表生成失敗不影響數據顯示
                        console.warn('Plot generation failed:', plotErr);
                    }
                }
                
            } else if (analysisType === 'cox') {
                // 獲取 Cox 回歸數據
                const coxResponse = await axios.get('/api/survival/cox-regression', { params });
                
                // 檢查是否返回錯誤
                if (coxResponse.data.error) {
                    setError(`${coxResponse.data.message}\n\n建議：${coxResponse.data.suggestion}`);
                    setCoxData(null);
                } else {
                    setCoxData(coxResponse.data);
                }
                
            } else if (analysisType === 'summary') {
                // 獲取摘要統計
                const summaryResponse = await axios.get('/api/survival/survival-summary', { params });
                setSummaryData(summaryResponse.data);
            }
            
        } catch (err) {
            // 處理不同類型的錯誤
            if (err.response?.data?.message) {
                setError(`${err.response.data.message}\n\n建議：${err.response.data.suggestion || ''}`);
            } else {
                setError(err.response?.data?.detail || '分析失敗，請稍後再試');
            }
            console.error('Analysis error:', err);
        } finally {
            setLoading(false);
        }
    };

    const renderKaplanMeierResults = () => {
        if (!kmData) return null;
        
        if (kmData.analysis_type === 'kaplan_meier_overall') {
            return (
                <div className="survival-results">
                    <h3>Kaplan-Meier 存活分析結果</h3>
                    
                    <div className="survival-stats">
                        <div className="stat-card">
                            <div className="stat-label">總病患數</div>
                            <div className="stat-value">{kmData.total_patients}</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-label">事件發生</div>
                            <div className="stat-value">{kmData.events_observed}</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-label">被審查（Censored）</div>
                            <div className="stat-value">{kmData.censored}</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-label">中位存活時間</div>
                            <div className="stat-value">
                                {kmData.median_survival_days ? `${kmData.median_survival_days.toFixed(0)} 天` : '未達到'}
                            </div>
                        </div>
                    </div>
                    
                    {kmPlot && (
                        <div className="survival-plot">
                            <h4>存活曲線</h4>
                            <img src={kmPlot} alt="Kaplan-Meier Survival Curve" />
                        </div>
                    )}
                    
                    <div className="survival-table">
                        <h4>存活機率表</h4>
                        <table>
                            <thead>
                                <tr>
                                    <th>追蹤時間（天）</th>
                                    <th>存活機率</th>
                                    <th>95% 信賴區間</th>
                                </tr>
                            </thead>
                            <tbody>
                                {kmData.timeline.map((time, idx) => {
                                    if (idx % 10 === 0 || idx === kmData.timeline.length - 1) {
                                        return (
                                            <tr key={idx}>
                                                <td>{time.toFixed(0)}</td>
                                                <td>{(kmData.survival_probability[idx] * 100).toFixed(1)}%</td>
                                                <td>
                                                    [{(kmData.confidence_interval_lower[idx] * 100).toFixed(1)}%, {(kmData.confidence_interval_upper[idx] * 100).toFixed(1)}%]
                                                </td>
                                            </tr>
                                        );
                                    }
                                    return null;
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            );
        } else if (kmData.analysis_type === 'kaplan_meier_stratified') {
            return (
                <div className="survival-results">
                    <h3>分層 Kaplan-Meier 分析結果</h3>
                    <p className="stratified-by">分層變數：<strong>{kmData.stratified_by}</strong></p>
                    
                    {kmPlot && (
                        <div className="survival-plot">
                            <h4>分層存活曲線</h4>
                            <img src={kmPlot} alt="Stratified Kaplan-Meier Curves" />
                        </div>
                    )}
                    
                    <div className="groups-comparison">
                        <h4>各組比較</h4>
                        {Object.entries(kmData.groups).map(([groupName, groupData]) => (
                            <div key={groupName} className="group-card">
                                <h5>{groupName}</h5>
                                <div className="group-stats">
                                    <div className="stat-item">
                                        <span className="stat-label">樣本數：</span>
                                        <span className="stat-value">{groupData.sample_size}</span>
                                    </div>
                                    <div className="stat-item">
                                        <span className="stat-label">中位存活時間：</span>
                                        <span className="stat-value">
                                            {groupData.median_survival ? `${groupData.median_survival.toFixed(0)} 天` : '未達到'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                    
                    {kmData.statistical_test && (
                        <div className="statistical-test">
                            <h4>統計檢定結果</h4>
                            <p><strong>檢定方法：</strong>{kmData.statistical_test.test}</p>
                            <p><strong>檢定統計量：</strong>{kmData.statistical_test.statistic.toFixed(4)}</p>
                            <p><strong>P 值：</strong>{kmData.statistical_test.p_value.toFixed(4)}</p>
                            <p className={kmData.statistical_test.significant ? 'significant' : 'not-significant'}>
                                <strong>結論：</strong>
                                {kmData.statistical_test.significant 
                                    ? '兩組存活曲線有顯著差異（p < 0.05）' 
                                    : '兩組存活曲線無顯著差異（p ≥ 0.05）'}
                            </p>
                        </div>
                    )}
                </div>
            );
        }
    };

    const renderCoxResults = () => {
        if (!coxData) return null;
        
        // 檢查是否是錯誤對象
        if (coxData.error) {
            return null; // 錯誤已經由 error state 顯示
        }
        
        return (
            <div className="survival-results">
                <h3>Cox 比例風險模型分析結果</h3>
                
                <div className="cox-stats">
                    <div className="stat-card">
                        <div className="stat-label">總病患數</div>
                        <div className="stat-value">{coxData.total_patients}</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-label">一致性指數（C-index）</div>
                        <div className="stat-value">{coxData.concordance_index?.toFixed(3) || 'N/A'}</div>
                    </div>
                </div>
                
                <div className="cox-interpretation">
                    <h4>風險比（Hazard Ratio）解釋</h4>
                    <ul>
                        <li><strong>HR &gt; 1：</strong>{coxData.interpretation.hazard_ratio_greater_than_1}</li>
                        <li><strong>HR = 1：</strong>{coxData.interpretation.hazard_ratio_equals_1}</li>
                        <li><strong>HR &lt; 1：</strong>{coxData.interpretation.hazard_ratio_less_than_1}</li>
                    </ul>
                </div>
                
                <div className="cox-table">
                    <h4>協變量分析</h4>
                    <table>
                        <thead>
                            <tr>
                                <th>變數</th>
                                <th>風險比（HR）</th>
                                <th>95% 信賴區間</th>
                                <th>P 值</th>
                                <th>顯著性</th>
                            </tr>
                        </thead>
                        <tbody>
                            {Object.entries(coxData.covariates).map(([covariate, data]) => (
                                <tr key={covariate} className={data.significant ? 'significant-row' : ''}>
                                    <td>{covariate}</td>
                                    <td>{data.hazard_ratio.toFixed(3)}</td>
                                    <td>[{data.confidence_interval_lower.toFixed(3)}, {data.confidence_interval_upper.toFixed(3)}]</td>
                                    <td>{data.p_value.toFixed(4)}</td>
                                    <td>{data.significant ? '✓ 顯著' : '× 不顯著'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    const renderSummaryResults = () => {
        if (!summaryData) return null;
        
        return (
            <div className="survival-results">
                <h3>存活分析摘要統計</h3>
                
                <div className="summary-section">
                    <h4>基本資訊</h4>
                    <p><strong>總病患數：</strong>{summaryData.total_patients}</p>
                </div>
                
                <div className="summary-section">
                    <h4>追蹤時間統計</h4>
                    <div className="stats-grid">
                        <div className="stat-item">
                            <span className="label">平均追蹤時間：</span>
                            <span className="value">{summaryData.follow_up_statistics.mean_days.toFixed(0)} 天</span>
                        </div>
                        <div className="stat-item">
                            <span className="label">中位追蹤時間：</span>
                            <span className="value">{summaryData.follow_up_statistics.median_days.toFixed(0)} 天</span>
                        </div>
                        <div className="stat-item">
                            <span className="label">最短追蹤時間：</span>
                            <span className="value">{summaryData.follow_up_statistics.min_days} 天</span>
                        </div>
                        <div className="stat-item">
                            <span className="label">最長追蹤時間：</span>
                            <span className="value">{summaryData.follow_up_statistics.max_days} 天</span>
                        </div>
                    </div>
                </div>
                
                <div className="summary-section">
                    <h4>性別分佈</h4>
                    <div className="distribution-chart">
                        <div className="chart-item">
                            <span className="label">男性：</span>
                            <span className="value">{summaryData.gender_distribution.male}</span>
                            <div className="bar" style={{width: `${(summaryData.gender_distribution.male / summaryData.total_patients) * 100}%`}}></div>
                        </div>
                        <div className="chart-item">
                            <span className="label">女性：</span>
                            <span className="value">{summaryData.gender_distribution.female}</span>
                            <div className="bar" style={{width: `${(summaryData.gender_distribution.female / summaryData.total_patients) * 100}%`}}></div>
                        </div>
                        <div className="chart-item">
                            <span className="label">未知：</span>
                            <span className="value">{summaryData.gender_distribution.unknown}</span>
                            <div className="bar" style={{width: `${(summaryData.gender_distribution.unknown / summaryData.total_patients) * 100}%`}}></div>
                        </div>
                    </div>
                </div>
                
                <div className="summary-section">
                    <h4>年齡組分佈</h4>
                    <div className="distribution-chart">
                        {Object.entries(summaryData.age_groups).map(([ageGroup, count]) => (
                            <div key={ageGroup} className="chart-item">
                                <span className="label">{ageGroup} 歲：</span>
                                <span className="value">{count}</span>
                                <div className="bar" style={{width: `${(count / summaryData.total_patients) * 100}%`}}></div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="survival-analysis-container">
            <div className="survival-header">
                <h1>🔬 存活分析（Survival Analysis）</h1>
                <p className="subtitle">Kaplan-Meier 存活曲線、Cox 比例風險模型分析</p>
            </div>
            
            <div className="survival-controls">
                <div className="control-section">
                    <h3>分析設定</h3>
                    
                    <div className="form-group">
                        <label>分析類型</label>
                        <select 
                            value={analysisType} 
                            onChange={(e) => setAnalysisType(e.target.value)}
                            className="form-control"
                        >
                            <option value="kaplan-meier">Kaplan-Meier 存活分析</option>
                            <option value="cox">Cox 比例風險模型</option>
                            <option value="summary">存活統計摘要</option>
                        </select>
                    </div>
                    
                    <div className="form-group">
                        <label>診斷條件（可選）</label>
                        <input 
                            type="text"
                            value={diagnosisCode}
                            onChange={(e) => setDiagnosisCode(e.target.value)}
                            placeholder="例如：Influenza, Myocardial"
                            className="form-control"
                            list="diagnoses-list"
                        />
                        <datalist id="diagnoses-list">
                            {diagnosesList.map((diag, idx) => (
                                <option key={idx} value={diag.code_text} />
                            ))}
                        </datalist>
                    </div>
                    
                    <div className="form-row">
                        <div className="form-group">
                            <label>開始日期</label>
                            <input 
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                className="form-control"
                            />
                        </div>
                        <div className="form-group">
                            <label>結束日期</label>
                            <input 
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                className="form-control"
                            />
                        </div>
                    </div>
                    
                    <div className="form-group">
                        <label>最大追蹤期間（天）</label>
                        <input 
                            type="number"
                            value={maxFollowUpDays}
                            onChange={(e) => setMaxFollowUpDays(parseInt(e.target.value))}
                            min="30"
                            max="7300"
                            className="form-control"
                        />
                        <small className="form-text">建議：365（1年）、1825（5年）、3650（10年）</small>
                    </div>
                    
                    {analysisType === 'kaplan-meier' && (
                        <div className="form-group">
                            <label>分層變數（可選）</label>
                            <select 
                                value={stratifyBy}
                                onChange={(e) => setStratifyBy(e.target.value)}
                                className="form-control"
                            >
                                <option value="">不分層</option>
                                <option value="gender">性別</option>
                                <option value="age_group">年齡組</option>
                            </select>
                        </div>
                    )}
                    
                    <button 
                        onClick={handleAnalyze}
                        disabled={loading}
                        className="btn btn-primary btn-analyze"
                    >
                        {loading ? '分析中...' : '開始分析'}
                    </button>
                </div>
            </div>
            
            {error && (
                <div className="error-message">
                    <strong>錯誤：</strong>{error}
                </div>
            )}
            
            {analysisType === 'kaplan-meier' && renderKaplanMeierResults()}
            {analysisType === 'cox' && renderCoxResults()}
            {analysisType === 'summary' && renderSummaryResults()}
            
            {!loading && !error && !kmData && !coxData && !summaryData && (
                <div className="empty-state">
                    <div className="empty-icon">📊</div>
                    <h3>準備開始存活分析</h3>
                    <p>請設定分析參數，然後點擊「開始分析」按鈕</p>
                    
                    <div className="info-cards">
                        <div className="info-card">
                            <h4>🔬 Kaplan-Meier 分析</h4>
                            <p>計算存活機率隨時間的變化，生成存活曲線，並進行組間比較</p>
                        </div>
                        <div className="info-card">
                            <h4>📈 Cox 比例風險模型</h4>
                            <p>評估不同變數（年齡、性別等）對存活的影響，計算風險比</p>
                        </div>
                        <div className="info-card">
                            <h4>📊 統計摘要</h4>
                            <p>查看基本統計資訊，包括追蹤時間、性別分佈、年齡組分佈等</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default SurvivalAnalysis;

