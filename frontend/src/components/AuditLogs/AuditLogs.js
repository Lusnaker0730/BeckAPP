import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './AuditLogs.css';

const AuditLogs = () => {
    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // 过滤条件
    const [filters, setFilters] = useState({
        username: '',
        action: '',
        resource: '',
        is_success: '',
        start_date: '',
        end_date: '',
        search: ''
    });
    
    // 分页
    const [pagination, setPagination] = useState({
        skip: 0,
        limit: 50,
        total: 0
    });
    
    // 可用的过滤器选项
    const [actions, setActions] = useState([]);
    const [resources, setResources] = useState([]);
    
    // 选中的日志（用于查看详情）
    const [selectedLog, setSelectedLog] = useState(null);
    
    useEffect(() => {
        fetchAuditLogs();
        fetchStats();
        fetchFilterOptions();
    }, [pagination.skip, pagination.limit]);
    
    const fetchAuditLogs = async () => {
        setLoading(true);
        try {
            const params = {
                skip: pagination.skip,
                limit: pagination.limit,
                ...filters
            };
            
            // 移除空值
            Object.keys(params).forEach(key => {
                if (params[key] === '' || params[key] === null) {
                    delete params[key];
                }
            });
            
            const response = await axios.get('/api/audit/logs', { params });
            setLogs(response.data.logs);
            setPagination(prev => ({ ...prev, total: response.data.total }));
            setError(null);
        } catch (err) {
            setError('获取审计日志失败: ' + (err.response?.data?.detail || err.message));
            console.error(err);
        } finally {
            setLoading(false);
        }
    };
    
    const fetchStats = async () => {
        try {
            const response = await axios.get('/api/audit/stats', { params: { days: 7 } });
            setStats(response.data);
        } catch (err) {
            console.error('获取统计信息失败:', err);
        }
    };
    
    const fetchFilterOptions = async () => {
        try {
            const [actionsRes, resourcesRes] = await Promise.all([
                axios.get('/api/audit/actions'),
                axios.get('/api/audit/resources')
            ]);
            setActions(actionsRes.data);
            setResources(resourcesRes.data);
        } catch (err) {
            console.error('获取过滤选项失败:', err);
        }
    };
    
    const handleFilterChange = (e) => {
        const { name, value } = e.target;
        setFilters(prev => ({ ...prev, [name]: value }));
    };
    
    const handleApplyFilters = () => {
        setPagination(prev => ({ ...prev, skip: 0 }));
        fetchAuditLogs();
    };
    
    const handleClearFilters = () => {
        setFilters({
            username: '',
            action: '',
            resource: '',
            is_success: '',
            start_date: '',
            end_date: '',
            search: ''
        });
        setPagination(prev => ({ ...prev, skip: 0 }));
    };
    
    const handlePageChange = (newSkip) => {
        setPagination(prev => ({ ...prev, skip: newSkip }));
    };
    
    const viewLogDetail = async (logId) => {
        try {
            const response = await axios.get(`/api/audit/logs/${logId}`);
            setSelectedLog(response.data);
        } catch (err) {
            setError('获取日志详情失败: ' + (err.response?.data?.detail || err.message));
        }
    };
    
    const getStatusBadgeClass = (isSuccess) => {
        if (isSuccess === 'success') return 'status-success';
        if (isSuccess === 'failure') return 'status-failure';
        return 'status-unknown';
    };
    
    const getActionBadgeClass = (action) => {
        if (action === 'login' || action === 'logout') return 'action-auth';
        if (action === 'export_data') return 'action-export';
        if (action === 'delete') return 'action-delete';
        if (action === 'admin_operation') return 'action-admin';
        return 'action-default';
    };
    
    const formatTimestamp = (timestamp) => {
        if (!timestamp) return 'N/A';
        const date = new Date(timestamp);
        return date.toLocaleString('zh-TW', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };
    
    return (
        <div className="audit-logs-container">
            <div className="audit-header">
                <h1>🔐 審計日誌</h1>
                <p className="subtitle">系統操作記錄與安全審計</p>
            </div>
            
            {/* 統計卡片 */}
            {stats && (
                <div className="stats-cards">
                    <div className="stat-card">
                        <div className="stat-icon">📊</div>
                        <div className="stat-content">
                            <div className="stat-value">{stats.summary.total_operations.toLocaleString()}</div>
                            <div className="stat-label">總操作數（7天）</div>
                        </div>
                    </div>
                    
                    <div className="stat-card">
                        <div className="stat-icon">✅</div>
                        <div className="stat-content">
                            <div className="stat-value">{stats.summary.success_rate}%</div>
                            <div className="stat-label">成功率</div>
                        </div>
                    </div>
                    
                    <div className="stat-card">
                        <div className="stat-icon">👥</div>
                        <div className="stat-content">
                            <div className="stat-value">{stats.summary.active_users}</div>
                            <div className="stat-label">活躍用戶</div>
                        </div>
                    </div>
                    
                    <div className="stat-card">
                        <div className="stat-icon">❌</div>
                        <div className="stat-content">
                            <div className="stat-value">{stats.summary.failed_operations}</div>
                            <div className="stat-label">失敗操作</div>
                        </div>
                    </div>
                </div>
            )}
            
            {/* 过滤器 */}
            <div className="filters-panel">
                <h3>📋 過濾條件</h3>
                <div className="filters-grid">
                    <div className="filter-group">
                        <label>用戶名</label>
                        <input
                            type="text"
                            name="username"
                            value={filters.username}
                            onChange={handleFilterChange}
                            placeholder="輸入用戶名"
                        />
                    </div>
                    
                    <div className="filter-group">
                        <label>操作類型</label>
                        <select name="action" value={filters.action} onChange={handleFilterChange}>
                            <option value="">全部</option>
                            {actions.map(action => (
                                <option key={action} value={action}>{action}</option>
                            ))}
                        </select>
                    </div>
                    
                    <div className="filter-group">
                        <label>資源類型</label>
                        <select name="resource" value={filters.resource} onChange={handleFilterChange}>
                            <option value="">全部</option>
                            {resources.map(resource => (
                                <option key={resource} value={resource}>{resource}</option>
                            ))}
                        </select>
                    </div>
                    
                    <div className="filter-group">
                        <label>狀態</label>
                        <select name="is_success" value={filters.is_success} onChange={handleFilterChange}>
                            <option value="">全部</option>
                            <option value="success">成功</option>
                            <option value="failure">失敗</option>
                        </select>
                    </div>
                    
                    <div className="filter-group">
                        <label>開始日期</label>
                        <input
                            type="date"
                            name="start_date"
                            value={filters.start_date}
                            onChange={handleFilterChange}
                        />
                    </div>
                    
                    <div className="filter-group">
                        <label>結束日期</label>
                        <input
                            type="date"
                            name="end_date"
                            value={filters.end_date}
                            onChange={handleFilterChange}
                        />
                    </div>
                    
                    <div className="filter-group full-width">
                        <label>全文搜索</label>
                        <input
                            type="text"
                            name="search"
                            value={filters.search}
                            onChange={handleFilterChange}
                            placeholder="搜索描述、端點、錯誤信息..."
                        />
                    </div>
                </div>
                
                <div className="filter-actions">
                    <button className="btn btn-primary" onClick={handleApplyFilters}>
                        🔍 應用過濾
                    </button>
                    <button className="btn btn-secondary" onClick={handleClearFilters}>
                        🔄 清除過濾
                    </button>
                </div>
            </div>
            
            {/* 错误提示 */}
            {error && (
                <div className="error-message">
                    <strong>錯誤：</strong> {error}
                </div>
            )}
            
            {/* 日志表格 */}
            {loading ? (
                <div className="loading">載入中...</div>
            ) : (
                <>
                    <div className="logs-table-container">
                        <table className="logs-table">
                            <thead>
                                <tr>
                                    <th>時間</th>
                                    <th>用戶</th>
                                    <th>操作</th>
                                    <th>資源</th>
                                    <th>方法</th>
                                    <th>端點</th>
                                    <th>IP地址</th>
                                    <th>狀態</th>
                                    <th>耗時</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                {logs.map(log => (
                                    <tr key={log.id}>
                                        <td>{formatTimestamp(log.timestamp)}</td>
                                        <td>
                                            <div className="user-info">
                                                <div className="username">{log.username || 'N/A'}</div>
                                                {log.user_role && (
                                                    <div className="user-role">{log.user_role}</div>
                                                )}
                                            </div>
                                        </td>
                                        <td>
                                            <span className={`badge ${getActionBadgeClass(log.action)}`}>
                                                {log.action}
                                            </span>
                                        </td>
                                        <td>{log.resource || '-'}</td>
                                        <td>
                                            <span className="method-badge">{log.method}</span>
                                        </td>
                                        <td className="endpoint-cell">{log.endpoint}</td>
                                        <td>{log.ip_address}</td>
                                        <td>
                                            <span className={`status-badge ${getStatusBadgeClass(log.is_success)}`}>
                                                {log.is_success === 'success' ? '✓ 成功' : '✗ 失敗'}
                                            </span>
                                            <div className="status-code">HTTP {log.status_code}</div>
                                        </td>
                                        <td>{log.duration_ms ? `${log.duration_ms}ms` : '-'}</td>
                                        <td>
                                            <button
                                                className="btn-small btn-view"
                                                onClick={() => viewLogDetail(log.id)}
                                            >
                                                查看詳情
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    
                    {/* 分页 */}
                    <div className="pagination">
                        <button
                            className="btn btn-pagination"
                            onClick={() => handlePageChange(Math.max(0, pagination.skip - pagination.limit))}
                            disabled={pagination.skip === 0}
                        >
                            ‹ 上一頁
                        </button>
                        <span className="pagination-info">
                            顯示 {pagination.skip + 1} - {Math.min(pagination.skip + pagination.limit, pagination.total)} / 共 {pagination.total} 條
                        </span>
                        <button
                            className="btn btn-pagination"
                            onClick={() => handlePageChange(pagination.skip + pagination.limit)}
                            disabled={pagination.skip + pagination.limit >= pagination.total}
                        >
                            下一頁 ›
                        </button>
                    </div>
                </>
            )}
            
            {/* 日志详情模态框 */}
            {selectedLog && (
                <div className="modal-overlay" onClick={() => setSelectedLog(null)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>📋 審計日誌詳情</h2>
                            <button className="modal-close" onClick={() => setSelectedLog(null)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <div className="detail-grid">
                                <div className="detail-row">
                                    <label>時間戳：</label>
                                    <span>{formatTimestamp(selectedLog.timestamp)}</span>
                                </div>
                                <div className="detail-row">
                                    <label>用戶ID：</label>
                                    <span>{selectedLog.user_id || 'N/A'}</span>
                                </div>
                                <div className="detail-row">
                                    <label>用戶名：</label>
                                    <span>{selectedLog.username || 'N/A'}</span>
                                </div>
                                <div className="detail-row">
                                    <label>用戶角色：</label>
                                    <span>{selectedLog.user_role || 'N/A'}</span>
                                </div>
                                <div className="detail-row">
                                    <label>操作類型：</label>
                                    <span className={`badge ${getActionBadgeClass(selectedLog.action)}`}>
                                        {selectedLog.action}
                                    </span>
                                </div>
                                <div className="detail-row">
                                    <label>資源類型：</label>
                                    <span>{selectedLog.resource || 'N/A'}</span>
                                </div>
                                <div className="detail-row">
                                    <label>資源ID：</label>
                                    <span>{selectedLog.resource_id || 'N/A'}</span>
                                </div>
                                <div className="detail-row">
                                    <label>HTTP方法：</label>
                                    <span className="method-badge">{selectedLog.method}</span>
                                </div>
                                <div className="detail-row">
                                    <label>API端點：</label>
                                    <span className="code">{selectedLog.endpoint}</span>
                                </div>
                                <div className="detail-row">
                                    <label>IP地址：</label>
                                    <span>{selectedLog.ip_address}</span>
                                </div>
                                <div className="detail-row">
                                    <label>狀態碼：</label>
                                    <span>{selectedLog.status_code}</span>
                                </div>
                                <div className="detail-row">
                                    <label>操作結果：</label>
                                    <span className={`status-badge ${getStatusBadgeClass(selectedLog.is_success)}`}>
                                        {selectedLog.is_success}
                                    </span>
                                </div>
                                <div className="detail-row">
                                    <label>處理時間：</label>
                                    <span>{selectedLog.duration_ms ? `${selectedLog.duration_ms} 毫秒` : 'N/A'}</span>
                                </div>
                                <div className="detail-row full-width">
                                    <label>描述：</label>
                                    <span>{selectedLog.description}</span>
                                </div>
                                {selectedLog.user_agent && (
                                    <div className="detail-row full-width">
                                        <label>User Agent：</label>
                                        <span className="code">{selectedLog.user_agent}</span>
                                    </div>
                                )}
                                {selectedLog.error_message && (
                                    <div className="detail-row full-width error">
                                        <label>錯誤信息：</label>
                                        <span>{selectedLog.error_message}</span>
                                    </div>
                                )}
                                {selectedLog.request_params && Object.keys(selectedLog.request_params).length > 0 && (
                                    <div className="detail-row full-width">
                                        <label>請求參數：</label>
                                        <pre className="json-display">
                                            {JSON.stringify(selectedLog.request_params, null, 2)}
                                        </pre>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AuditLogs;

