// Cross-feature navigation utilities
import { NavigateFunction } from 'react-router-dom';

export interface NavigationContext {
  source: string;
  sourceId?: string;
  metadata?: Record<string, any>;
}

export interface NavigationLink {
  path: string;
  label: string;
  icon?: string;
  context?: NavigationContext;
}

/**
 * Deep linking utilities for cross-feature navigation
 */
export class CrossFeatureNavigator {
  private navigate: NavigateFunction;
  private navigationHistory: NavigationContext[] = [];

  constructor(navigate: NavigateFunction) {
    this.navigate = navigate;
  }

  /**
   * Navigate to a security finding from any feature
   */
  navigateToSecurityFinding(findingId: string, context?: NavigationContext) {
    this.addToHistory({ source: 'security-finding', sourceId: findingId, ...context });
    this.navigate(`/security?finding=${findingId}`, { state: context });
  }

  /**
   * Navigate to a test case from security findings
   */
  navigateToTestCase(testCaseId: string, context?: NavigationContext) {
    this.addToHistory({ source: 'test-case', sourceId: testCaseId, ...context });
    this.navigate(`/test-cases/${testCaseId}`, { state: context });
  }

  /**
   * Navigate to test results from various features
   */
  navigateToTestResults(resultId: string, context?: NavigationContext) {
    this.addToHistory({ source: 'test-results', sourceId: resultId, ...context });
    this.navigate(`/test-results/${resultId}`, { state: context });
  }

  /**
   * Navigate to user profile from team management
   */
  navigateToUserProfile(userId: string, context?: NavigationContext) {
    this.addToHistory({ source: 'user-profile', sourceId: userId, ...context });
    this.navigate(`/users/${userId}`, { state: context });
  }

  /**
   * Navigate to team workspace
   */
  navigateToTeamWorkspace(teamId: string, context?: NavigationContext) {
    this.addToHistory({ source: 'team-workspace', sourceId: teamId, ...context });
    this.navigate(`/teams/${teamId}`, { state: context });
  }

  /**
   * Navigate to notification source
   */
  navigateToNotificationSource(notification: any) {
    const context: NavigationContext = {
      source: 'notification',
      sourceId: notification.id,
      metadata: notification.metadata
    };

    switch (notification.category) {
      case 'security':
        this.navigateToSecurityFinding(notification.metadata?.findingId, context);
        break;
      case 'test-execution':
        this.navigateToTestResults(notification.metadata?.resultId, context);
        break;
      case 'compliance':
        this.navigate('/audit-compliance', { state: context });
        break;
      case 'resource':
        this.navigate('/resource-monitoring', { state: context });
        break;
      case 'integration':
        this.navigate('/integrations', { state: context });
        break;
      default:
        this.navigate('/notifications', { state: context });
    }
  }

  /**
   * Navigate to knowledge base article
   */
  navigateToKnowledgeArticle(articleId: string, context?: NavigationContext) {
    this.addToHistory({ source: 'knowledge-base', sourceId: articleId, ...context });
    this.navigate(`/knowledge-base/${articleId}`, { state: context });
  }

  /**
   * Navigate to analytics report
   */
  navigateToAnalyticsReport(reportId: string, context?: NavigationContext) {
    this.addToHistory({ source: 'analytics', sourceId: reportId, ...context });
    this.navigate(`/analytics?report=${reportId}`, { state: context });
  }

  /**
   * Navigate to AI model details
   */
  navigateToAIModel(modelId: string, context?: NavigationContext) {
    this.addToHistory({ source: 'ai-model', sourceId: modelId, ...context });
    this.navigate(`/ai-models/${modelId}`, { state: context });
  }

  /**
   * Navigate to integration details
   */
  navigateToIntegration(integrationId: string, context?: NavigationContext) {
    this.addToHistory({ source: 'integration', sourceId: integrationId, ...context });
    this.navigate(`/integrations/${integrationId}`, { state: context });
  }

  /**
   * Navigate to backup details
   */
  navigateToBackup(backupId: string, context?: NavigationContext) {
    this.addToHistory({ source: 'backup', sourceId: backupId, ...context });
    this.navigate(`/backup-recovery?backup=${backupId}`, { state: context });
  }

  /**
   * Navigate to audit event
   */
  navigateToAuditEvent(eventId: string, context?: NavigationContext) {
    this.addToHistory({ source: 'audit-event', sourceId: eventId, ...context });
    this.navigate(`/audit-compliance?event=${eventId}`, { state: context });
  }

  /**
   * Get navigation history
   */
  getHistory(): NavigationContext[] {
    return [...this.navigationHistory];
  }

  /**
   * Go back in navigation history
   */
  goBack() {
    if (this.navigationHistory.length > 1) {
      this.navigationHistory.pop();
      const previous = this.navigationHistory[this.navigationHistory.length - 1];
      // Navigate to previous context
      this.navigate(-1);
    }
  }

  /**
   * Clear navigation history
   */
  clearHistory() {
    this.navigationHistory = [];
  }

  private addToHistory(context: NavigationContext) {
    this.navigationHistory.push(context);
    // Keep only last 50 entries
    if (this.navigationHistory.length > 50) {
      this.navigationHistory.shift();
    }
  }
}

/**
 * Generate navigation links for related features
 */
export function getRelatedLinks(feature: string, id: string): NavigationLink[] {
  const links: NavigationLink[] = [];

  switch (feature) {
    case 'security-finding':
      links.push(
        { path: `/test-cases?security=${id}`, label: 'Related Test Cases', icon: 'FileText' },
        { path: `/test-results?security=${id}`, label: 'Test Results', icon: 'CheckCircle' },
        { path: `/audit-compliance?security=${id}`, label: 'Audit Trail', icon: 'Shield' }
      );
      break;

    case 'test-case':
      links.push(
        { path: `/test-results?testCase=${id}`, label: 'Execution Results', icon: 'PlayCircle' },
        { path: `/security?testCase=${id}`, label: 'Security Findings', icon: 'AlertTriangle' },
        { path: `/analytics?testCase=${id}`, label: 'Analytics', icon: 'BarChart' }
      );
      break;

    case 'user':
      links.push(
        { path: `/test-plans?user=${id}`, label: 'Test Plans', icon: 'FileText' },
        { path: `/teams?user=${id}`, label: 'Teams', icon: 'Users' },
        { path: `/audit-compliance?user=${id}`, label: 'Activity Log', icon: 'Clock' }
      );
      break;

    case 'team':
      links.push(
        { path: `/test-plans?team=${id}`, label: 'Team Test Plans', icon: 'FileText' },
        { path: `/test-environments?team=${id}`, label: 'Team Environments', icon: 'Server' },
        { path: `/resource-monitoring?team=${id}`, label: 'Resource Usage', icon: 'Activity' }
      );
      break;

    case 'notification':
      links.push(
        { path: `/notifications/settings`, label: 'Notification Settings', icon: 'Settings' },
        { path: `/audit-compliance?notification=${id}`, label: 'Audit Trail', icon: 'Shield' }
      );
      break;
  }

  return links;
}

/**
 * Generate breadcrumb trail for complex workflows
 */
export interface Breadcrumb {
  label: string;
  path?: string;
  active?: boolean;
}

export function generateBreadcrumbs(pathname: string, context?: NavigationContext): Breadcrumb[] {
  const breadcrumbs: Breadcrumb[] = [{ label: 'Home', path: '/' }];
  const parts = pathname.split('/').filter(Boolean);

  const pathMap: Record<string, string> = {
    'security': 'Security Dashboard',
    'ai-models': 'AI Model Management',
    'audit-compliance': 'Audit & Compliance',
    'resource-monitoring': 'Resource Monitoring',
    'integrations': 'Integration Hub',
    'users': 'User Management',
    'teams': 'Team Management',
    'notifications': 'Notification Center',
    'knowledge-base': 'Knowledge Base',
    'analytics': 'Analytics & Insights',
    'backup-recovery': 'Backup & Recovery',
    'test-cases': 'Test Cases',
    'test-plans': 'Test Plans',
    'test-results': 'Test Results',
    'test-execution': 'Test Execution'
  };

  let currentPath = '';
  parts.forEach((part, index) => {
    currentPath += `/${part}`;
    const label = pathMap[part] || part.charAt(0).toUpperCase() + part.slice(1);
    breadcrumbs.push({
      label,
      path: index === parts.length - 1 ? undefined : currentPath,
      active: index === parts.length - 1
    });
  });

  // Add context-based breadcrumb if available
  if (context?.source) {
    const sourceLabel = pathMap[context.source] || context.source;
    breadcrumbs.splice(breadcrumbs.length - 1, 0, {
      label: `From ${sourceLabel}`,
      path: undefined
    });
  }

  return breadcrumbs;
}
