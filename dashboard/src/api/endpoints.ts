/**
 * API Endpoint definitions for all feature areas
 */

import { apiClient } from './client';

/**
 * Security API endpoints
 */
export const securityAPI = {
  getMetrics: () => apiClient.get('/security/metrics'),
  getVulnerabilities: (params?: { severity?: string; status?: string; limit?: number; offset?: number }) =>
    apiClient.get('/security/vulnerabilities', params),
  getFuzzingResults: (params?: { limit?: number; offset?: number }) =>
    apiClient.get('/security/fuzzing-results', params),
  getPolicies: () => apiClient.get('/security/policies'),
  triggerScan: (target: string, scanType: string) =>
    apiClient.post('/security/scan', { target, scan_type: scanType }),
};

/**
 * AI Models API endpoints
 */
export const aiModelsAPI = {
  listModels: (params?: { status?: string }) => apiClient.get('/ai-models/', params),
  getModelMetrics: (modelId: string) => apiClient.get(`/ai-models/${modelId}/metrics`),
  listPromptTemplates: (params?: { model_id?: string }) => apiClient.get('/ai-models/prompts', params),
  getFallbackConfig: () => apiClient.get('/ai-models/fallback-config'),
  createModel: (model: any) => apiClient.post('/ai-models/', model),
  updateModel: (modelId: string, model: any) => apiClient.put(`/ai-models/${modelId}`, model),
};

/**
 * Audit & Compliance API endpoints
 */
export const auditAPI = {
  getEvents: (params?: {
    user?: string;
    action?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }) => apiClient.get('/audit/events', params),
  getFrameworks: () => apiClient.get('/audit/frameworks'),
  getReports: (params?: { framework?: string; limit?: number; offset?: number }) =>
    apiClient.get('/audit/reports', params),
  generateReport: (framework: string, periodStart: string, periodEnd: string) =>
    apiClient.post('/audit/reports/generate', { framework, period_start: periodStart, period_end: periodEnd }),
  searchEvents: (query: string, limit?: number) => apiClient.get('/audit/search', { query, limit }),
};

/**
 * Resource Monitoring API endpoints
 */
export const resourcesAPI = {
  getCurrentMetrics: () => apiClient.get('/resources/metrics/current'),
  getMetricsHistory: (params?: { start_date?: string; end_date?: string; interval?: string }) =>
    apiClient.get('/resources/metrics/history', params),
  getInfrastructure: () => apiClient.get('/resources/infrastructure'),
  getCapacityForecast: (params?: { resource_type?: string; days_ahead?: number }) =>
    apiClient.get('/resources/capacity/forecast', params),
  getAlerts: (params?: { severity?: string; acknowledged?: boolean }) =>
    apiClient.get('/resources/alerts', params),
  acknowledgeAlert: (alertId: string) => apiClient.post(`/resources/alerts/${alertId}/acknowledge`),
};

/**
 * Integrations API endpoints
 */
export const integrationsAPI = {
  listIntegrations: (params?: { type?: string; status?: string }) =>
    apiClient.get('/integrations/', params),
  getIntegration: (integrationId: string) => apiClient.get(`/integrations/${integrationId}`),
  getIntegrationHealth: (integrationId: string) => apiClient.get(`/integrations/${integrationId}/health`),
  listWebhooks: (integrationId: string) => apiClient.get(`/integrations/${integrationId}/webhooks`),
  createIntegration: (integration: any) => apiClient.post('/integrations/', integration),
  updateIntegration: (integrationId: string, integration: any) =>
    apiClient.put(`/integrations/${integrationId}`, integration),
  testIntegration: (integrationId: string) => apiClient.post(`/integrations/${integrationId}/test`),
  syncIntegration: (integrationId: string) => apiClient.post(`/integrations/${integrationId}/sync`),
};

/**
 * User Management API endpoints
 */
export const usersAPI = {
  listUsers: (params?: { role?: string; team?: string; status?: string; limit?: number; offset?: number }) =>
    apiClient.get('/users/', params),
  getUser: (userId: string) => apiClient.get(`/users/${userId}`),
  listTeams: (params?: { limit?: number; offset?: number }) => apiClient.get('/users/teams/list', params),
  listRoles: () => apiClient.get('/users/roles/list'),
  listPermissions: () => apiClient.get('/users/permissions/list'),
  createUser: (user: any) => apiClient.post('/users/', user),
  updateUser: (userId: string, user: any) => apiClient.put(`/users/${userId}`, user),
  createTeam: (team: any) => apiClient.post('/users/teams', team),
  updateTeamMembers: (teamId: string, memberIds: string[]) =>
    apiClient.put(`/users/teams/${teamId}/members`, { member_ids: memberIds }),
};

/**
 * Notifications API endpoints
 */
export const notificationsAPI = {
  listNotifications: (params?: {
    category?: string;
    severity?: string;
    read?: boolean;
    limit?: number;
    offset?: number;
  }) => apiClient.get('/notifications/', params),
  getUnreadCount: () => apiClient.get('/notifications/unread-count'),
  getPreferences: () => apiClient.get('/notifications/preferences'),
  updatePreferences: (preferences: any) => apiClient.put('/notifications/preferences', preferences),
  listPolicies: () => apiClient.get('/notifications/policies'),
  createPolicy: (policy: any) => apiClient.post('/notifications/policies', policy),
  markAsRead: (notificationId: string) => apiClient.post(`/notifications/${notificationId}/read`),
  markAllAsRead: () => apiClient.post('/notifications/mark-all-read'),
  deleteNotification: (notificationId: string) => apiClient.delete(`/notifications/${notificationId}`),
};

/**
 * Knowledge Base API endpoints
 */
export const knowledgeBaseAPI = {
  listArticles: (params?: { category?: string; tag?: string; limit?: number; offset?: number }) =>
    apiClient.get('/knowledge-base/articles', params),
  getArticle: (articleId: string) => apiClient.get(`/knowledge-base/articles/${articleId}`),
  searchArticles: (query: string, params?: { category?: string; limit?: number }) =>
    apiClient.get('/knowledge-base/search', { query, ...params }),
  getContextualHelp: (page: string, section?: string) =>
    apiClient.get('/knowledge-base/contextual-help', { page, section }),
  listCategories: () => apiClient.get('/knowledge-base/categories'),
  createArticle: (article: any) => apiClient.post('/knowledge-base/articles', article),
  updateArticle: (articleId: string, article: any) =>
    apiClient.put(`/knowledge-base/articles/${articleId}`, article),
  markArticleHelpful: (articleId: string, helpful: boolean) =>
    apiClient.post(`/knowledge-base/articles/${articleId}/helpful`, { helpful }),
};

/**
 * Analytics API endpoints
 */
export const analyticsAPI = {
  getMetrics: (period?: string) => apiClient.get('/analytics/metrics', { period }),
  getTrendAnalysis: (metric: string, period?: string) =>
    apiClient.get('/analytics/trends', { metric, period }),
  getInsights: (params?: { type?: string; severity?: string; limit?: number }) =>
    apiClient.get('/analytics/insights', params),
  getPredictions: (metric: string, daysAhead?: number) =>
    apiClient.get('/analytics/predictions', { metric, days_ahead: daysAhead }),
  listCustomReports: (params?: { limit?: number; offset?: number }) =>
    apiClient.get('/analytics/reports', params),
  createCustomReport: (report: any) => apiClient.post('/analytics/reports', report),
  generateReport: (reportId: string) => apiClient.post(`/analytics/reports/${reportId}/generate`),
  getDashboardData: (widgets?: string) => apiClient.get('/analytics/dashboard-data', { widgets }),
};

/**
 * Backup & Recovery API endpoints
 */
export const backupAPI = {
  listPolicies: () => apiClient.get('/backup/policies'),
  listRecoveryPoints: (params?: {
    backup_type?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }) => apiClient.get('/backup/recovery-points', params),
  getBackupStatus: (params?: { policy_id?: string; status?: string; limit?: number; offset?: number }) =>
    apiClient.get('/backup/status', params),
  listRecoveryTests: (params?: { limit?: number; offset?: number }) =>
    apiClient.get('/backup/recovery-tests', params),
  createPolicy: (policy: any) => apiClient.post('/backup/policies', policy),
  updatePolicy: (policyId: string, policy: any) => apiClient.put(`/backup/policies/${policyId}`, policy),
  executeBackup: (policyId: string) => apiClient.post(`/backup/policies/${policyId}/execute`),
  restoreFromRecoveryPoint: (recoveryPointId: string, targetLocation?: string) =>
    apiClient.post(`/backup/recovery-points/${recoveryPointId}/restore`, { target_location: targetLocation }),
  createRecoveryTest: (recoveryPointId: string, testType: string) =>
    apiClient.post('/backup/recovery-tests', { recovery_point_id: recoveryPointId, test_type: testType }),
  deleteRecoveryPoint: (recoveryPointId: string) =>
    apiClient.delete(`/backup/recovery-points/${recoveryPointId}`),
};

/**
 * Export all API endpoints
 */
export const api = {
  security: securityAPI,
  aiModels: aiModelsAPI,
  audit: auditAPI,
  resources: resourcesAPI,
  integrations: integrationsAPI,
  users: usersAPI,
  notifications: notificationsAPI,
  knowledgeBase: knowledgeBaseAPI,
  analytics: analyticsAPI,
  backup: backupAPI,
};

export default api;
