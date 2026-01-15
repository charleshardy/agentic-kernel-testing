/**
 * Navigation Service
 * Provides cross-feature navigation, deep linking, and contextual navigation
 */

export interface NavigationLink {
  path: string;
  label: string;
  icon?: string;
  params?: Record<string, any>;
}

export interface BreadcrumbItem {
  label: string;
  path?: string;
  icon?: string;
}

export interface FeatureContext {
  feature: string;
  resourceId?: string;
  resourceType?: string;
  metadata?: Record<string, any>;
}

export interface SearchResult {
  id: string;
  title: string;
  description: string;
  type: 'test' | 'security' | 'user' | 'integration' | 'notification' | 'knowledge' | 'analytics';
  path: string;
  relevance: number;
  metadata?: Record<string, any>;
}

class NavigationService {
  /**
   * Generate deep link to a specific resource
   */
  generateDeepLink(resourceType: string, resourceId: string, context?: Record<string, any>): string {
    const baseLinks: Record<string, string> = {
      'test-case': '/test-cases',
      'test-plan': '/test-plans',
      'test-result': '/test-results',
      'security-finding': '/security',
      'vulnerability': '/security',
      'defect': '/defects',
      'user': '/users',
      'team': '/users',
      'integration': '/integrations',
      'notification': '/notifications',
      'article': '/knowledge-base',
      'analytics-report': '/analytics',
      'backup': '/backup'
    };

    const basePath = baseLinks[resourceType] || '/';
    const params = new URLSearchParams();
    
    if (context) {
      Object.entries(context).forEach(([key, value]) => {
        params.append(key, String(value));
      });
    }

    const queryString = params.toString();
    return `${basePath}/${resourceId}${queryString ? `?${queryString}` : ''}`;
  }

  /**
   * Generate navigation links from security finding to related resources
   */
  getSecurityFindingLinks(findingId: string, finding: any): NavigationLink[] {
    const links: NavigationLink[] = [];

    // Link to related test cases
    if (finding.relatedTestCases && finding.relatedTestCases.length > 0) {
      finding.relatedTestCases.forEach((testCaseId: string) => {
        links.push({
          path: this.generateDeepLink('test-case', testCaseId),
          label: `Test Case ${testCaseId}`,
          icon: 'FileTextOutlined'
        });
      });
    }

    // Link to related test results
    if (finding.relatedTestResults && finding.relatedTestResults.length > 0) {
      finding.relatedTestResults.forEach((resultId: string) => {
        links.push({
          path: this.generateDeepLink('test-result', resultId),
          label: `Test Result ${resultId}`,
          icon: 'CheckCircleOutlined'
        });
      });
    }

    // Link to related defects
    if (finding.relatedDefects && finding.relatedDefects.length > 0) {
      finding.relatedDefects.forEach((defectId: string) => {
        links.push({
          path: this.generateDeepLink('defect', defectId),
          label: `Defect ${defectId}`,
          icon: 'BugOutlined'
        });
      });
    }

    // Link to CVE details if available
    if (finding.cveId) {
      links.push({
        path: `https://cve.mitre.org/cgi-bin/cvename.cgi?name=${finding.cveId}`,
        label: `CVE Details: ${finding.cveId}`,
        icon: 'LinkOutlined'
      });
    }

    return links;
  }

  /**
   * Generate navigation links from user/team to related resources
   */
  getUserTeamLinks(userId: string, user: any): NavigationLink[] {
    const links: NavigationLink[] = [];

    // Link to user's test plans
    if (user.testPlans && user.testPlans.length > 0) {
      links.push({
        path: `/test-plans?userId=${userId}`,
        label: `Test Plans (${user.testPlans.length})`,
        icon: 'ProjectOutlined'
      });
    }

    // Link to user's test environments
    if (user.environments && user.environments.length > 0) {
      links.push({
        path: `/test-environment?userId=${userId}`,
        label: `Environments (${user.environments.length})`,
        icon: 'CloudServerOutlined'
      });
    }

    // Link to user's test results
    links.push({
      path: `/test-results?userId=${userId}`,
      label: 'Test Results',
      icon: 'BarChartOutlined'
    });

    // Link to user's teams
    if (user.teams && user.teams.length > 0) {
      user.teams.forEach((team: any) => {
        links.push({
          path: this.generateDeepLink('team', team.id),
          label: `Team: ${team.name}`,
          icon: 'TeamOutlined'
        });
      });
    }

    return links;
  }

  /**
   * Generate navigation links from notification to related feature
   */
  getNotificationLink(notification: any): NavigationLink | null {
    if (!notification.metadata || !notification.metadata.resourceType || !notification.metadata.resourceId) {
      return null;
    }

    return {
      path: this.generateDeepLink(notification.metadata.resourceType, notification.metadata.resourceId),
      label: `View ${notification.metadata.resourceType.replace('-', ' ')}`,
      icon: 'LinkOutlined'
    };
  }

  /**
   * Generate breadcrumb trail for current context
   */
  generateBreadcrumbs(context: FeatureContext): BreadcrumbItem[] {
    const breadcrumbs: BreadcrumbItem[] = [
      { label: 'Home', path: '/', icon: 'HomeOutlined' }
    ];

    const featureBreadcrumbs: Record<string, BreadcrumbItem[]> = {
      'security': [
        { label: 'Security', path: '/security', icon: 'SafetyOutlined' }
      ],
      'ai-models': [
        { label: 'AI Models', path: '/ai-models', icon: 'RobotOutlined' }
      ],
      'audit': [
        { label: 'Audit & Compliance', path: '/audit', icon: 'AuditOutlined' }
      ],
      'resources': [
        { label: 'Resource Monitoring', path: '/resources', icon: 'DashboardOutlined' }
      ],
      'integrations': [
        { label: 'Integrations', path: '/integrations', icon: 'ApiOutlined' }
      ],
      'users': [
        { label: 'Users & Teams', path: '/users', icon: 'TeamOutlined' }
      ],
      'notifications': [
        { label: 'Notifications', path: '/notifications', icon: 'BellOutlined' }
      ],
      'knowledge-base': [
        { label: 'Knowledge Base', path: '/knowledge-base', icon: 'BookOutlined' }
      ],
      'analytics': [
        { label: 'Analytics', path: '/analytics', icon: 'LineChartOutlined' }
      ],
      'backup': [
        { label: 'Backup & Recovery', path: '/backup', icon: 'DatabaseOutlined' }
      ]
    };

    if (featureBreadcrumbs[context.feature]) {
      breadcrumbs.push(...featureBreadcrumbs[context.feature]);
    }

    // Add resource-specific breadcrumb if available
    if (context.resourceId && context.resourceType) {
      breadcrumbs.push({
        label: `${context.resourceType} ${context.resourceId}`,
        icon: 'FileOutlined'
      });
    }

    return breadcrumbs;
  }

  /**
   * Unified search across all features
   */
  async unifiedSearch(query: string, filters?: {
    types?: string[];
    dateRange?: { start: Date; end: Date };
    limit?: number;
  }): Promise<SearchResult[]> {
    // In a real implementation, this would call multiple backend APIs
    // For now, return mock results
    const mockResults: SearchResult[] = [
      {
        id: 'test-001',
        title: 'Kernel Security Test Suite',
        description: 'Comprehensive security testing for Linux kernel',
        type: 'test',
        path: '/test-cases/test-001',
        relevance: 0.95
      },
      {
        id: 'vuln-001',
        title: 'CVE-2024-0001: Buffer Overflow',
        description: 'Critical buffer overflow vulnerability in network stack',
        type: 'security',
        path: '/security/vuln-001',
        relevance: 0.92
      },
      {
        id: 'user-001',
        title: 'John Doe',
        description: 'Senior Kernel Developer',
        type: 'user',
        path: '/users/user-001',
        relevance: 0.88
      }
    ];

    // Filter by type if specified
    let results = mockResults;
    if (filters?.types && filters.types.length > 0) {
      results = results.filter(r => filters.types!.includes(r.type));
    }

    // Apply limit
    const limit = filters?.limit || 10;
    results = results.slice(0, limit);

    // Sort by relevance
    results.sort((a, b) => b.relevance - a.relevance);

    return results;
  }

  /**
   * Get related resources for a given context
   */
  getRelatedResources(context: FeatureContext): NavigationLink[] {
    const links: NavigationLink[] = [];

    // Add feature-specific related resources
    switch (context.feature) {
      case 'security':
        links.push(
          { path: '/test-cases', label: 'Related Test Cases', icon: 'FileTextOutlined' },
          { path: '/defects', label: 'Related Defects', icon: 'BugOutlined' },
          { path: '/audit', label: 'Audit Trail', icon: 'AuditOutlined' }
        );
        break;
      
      case 'test-cases':
        links.push(
          { path: '/test-results', label: 'Test Results', icon: 'CheckCircleOutlined' },
          { path: '/security', label: 'Security Findings', icon: 'SafetyOutlined' },
          { path: '/analytics', label: 'Analytics', icon: 'LineChartOutlined' }
        );
        break;
      
      case 'users':
        links.push(
          { path: '/test-plans', label: 'Test Plans', icon: 'ProjectOutlined' },
          { path: '/test-environment', label: 'Environments', icon: 'CloudServerOutlined' },
          { path: '/audit', label: 'Activity Log', icon: 'AuditOutlined' }
        );
        break;
      
      case 'analytics':
        links.push(
          { path: '/test-results', label: 'Test Results', icon: 'CheckCircleOutlined' },
          { path: '/resources', label: 'Resource Usage', icon: 'DashboardOutlined' },
          { path: '/security', label: 'Security Metrics', icon: 'SafetyOutlined' }
        );
        break;
    }

    return links;
  }

  /**
   * Get contextual help article suggestions
   */
  getContextualHelp(context: FeatureContext): NavigationLink[] {
    const helpLinks: NavigationLink[] = [];

    const featureHelp: Record<string, NavigationLink[]> = {
      'security': [
        { path: '/knowledge-base/security-scanning', label: 'Security Scanning Guide', icon: 'BookOutlined' },
        { path: '/knowledge-base/vulnerability-management', label: 'Vulnerability Management', icon: 'BookOutlined' }
      ],
      'ai-models': [
        { path: '/knowledge-base/ai-model-configuration', label: 'AI Model Configuration', icon: 'BookOutlined' },
        { path: '/knowledge-base/prompt-engineering', label: 'Prompt Engineering Best Practices', icon: 'BookOutlined' }
      ],
      'audit': [
        { path: '/knowledge-base/compliance-frameworks', label: 'Compliance Frameworks', icon: 'BookOutlined' },
        { path: '/knowledge-base/audit-trail', label: 'Understanding Audit Trails', icon: 'BookOutlined' }
      ],
      'integrations': [
        { path: '/knowledge-base/ci-cd-integration', label: 'CI/CD Integration Guide', icon: 'BookOutlined' },
        { path: '/knowledge-base/webhook-setup', label: 'Webhook Setup', icon: 'BookOutlined' }
      ]
    };

    return featureHelp[context.feature] || [];
  }

  /**
   * Navigate to resource with context preservation
   */
  navigateWithContext(path: string, context?: Record<string, any>): void {
    const params = new URLSearchParams();
    
    if (context) {
      Object.entries(context).forEach(([key, value]) => {
        params.append(key, String(value));
      });
    }

    const queryString = params.toString();
    const fullPath = `${path}${queryString ? `?${queryString}` : ''}`;
    
    // In a real implementation, this would use React Router
    window.location.href = fullPath;
  }

  /**
   * Get quick actions for current context
   */
  getQuickActions(context: FeatureContext): NavigationLink[] {
    const actions: NavigationLink[] = [];

    switch (context.feature) {
      case 'security':
        actions.push(
          { path: '/security/scan/new', label: 'Run Security Scan', icon: 'ScanOutlined' },
          { path: '/security/policy/new', label: 'Create Policy', icon: 'PlusOutlined' }
        );
        break;
      
      case 'test-cases':
        actions.push(
          { path: '/test-cases/new', label: 'Create Test Case', icon: 'PlusOutlined' },
          { path: '/test-execution/new', label: 'Execute Tests', icon: 'PlayCircleOutlined' }
        );
        break;
      
      case 'users':
        actions.push(
          { path: '/users/new', label: 'Add User', icon: 'UserAddOutlined' },
          { path: '/users/teams/new', label: 'Create Team', icon: 'TeamOutlined' }
        );
        break;
    }

    return actions;
  }
}

export default new NavigationService();
