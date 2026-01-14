import {
  SecurityMetrics,
  Vulnerability,
  FuzzingResult,
  SecurityPolicy,
  SecurityScan,
  SecurityAlert,
  SecurityReport,
  VulnerabilityFilter,
  FuzzingFilter,
  ScanConfiguration,
  FuzzingConfiguration,
  ReportConfiguration,
  SecurityMetricsResponse,
  VulnerabilitiesResponse,
  SecurityError
} from '../types/security';

class SecurityService {
  private baseUrl: string;
  private apiKey?: string;

  constructor(baseUrl: string = '/api/security', apiKey?: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new SecurityError(
          errorData.code || 'UNKNOWN_ERROR',
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          errorData.details,
          new Date()
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof SecurityError) {
        throw error;
      }
      
      throw new SecurityError(
        'NETWORK_ERROR',
        `Failed to communicate with security service: ${error instanceof Error ? error.message : 'Unknown error'}`,
        { originalError: error },
        new Date()
      );
    }
  }

  // Security Metrics
  async getSecurityMetrics(): Promise<SecurityMetrics> {
    const response = await this.request<SecurityMetricsResponse>('/metrics');
    return response.data;
  }

  // Vulnerability Management
  async getVulnerabilities(filters?: VulnerabilityFilter): Promise<Vulnerability[]> {
    const queryParams = new URLSearchParams();
    
    if (filters) {
      if (filters.severity?.length) {
        queryParams.append('severity', filters.severity.join(','));
      }
      if (filters.status?.length) {
        queryParams.append('status', filters.status.join(','));
      }
      if (filters.components?.length) {
        queryParams.append('components', filters.components.join(','));
      }
      if (filters.assignee) {
        queryParams.append('assignee', filters.assignee);
      }
      if (filters.tags?.length) {
        queryParams.append('tags', filters.tags.join(','));
      }
      if (filters.dateRange) {
        queryParams.append('startDate', filters.dateRange.start.toISOString());
        queryParams.append('endDate', filters.dateRange.end.toISOString());
      }
    }

    const endpoint = `/vulnerabilities${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await this.request<VulnerabilitiesResponse>(endpoint);
    return response.data;
  }

  async getVulnerability(id: string): Promise<Vulnerability> {
    return await this.request<Vulnerability>(`/vulnerabilities/${id}`);
  }

  async updateVulnerability(id: string, updates: Partial<Vulnerability>): Promise<Vulnerability> {
    return await this.request<Vulnerability>(`/vulnerabilities/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async assignVulnerability(id: string, assignee: string): Promise<Vulnerability> {
    return await this.updateVulnerability(id, { assignee });
  }

  async resolveVulnerability(id: string, resolution: string): Promise<Vulnerability> {
    return await this.updateVulnerability(id, { 
      status: 'patched',
      resolvedAt: new Date(),
      remediation: resolution
    });
  }

  // Fuzzing Management
  async getFuzzingResults(filters?: FuzzingFilter): Promise<FuzzingResult[]> {
    const queryParams = new URLSearchParams();
    
    if (filters) {
      if (filters.status?.length) {
        queryParams.append('status', filters.status.join(','));
      }
      if (filters.tool?.length) {
        queryParams.append('tool', filters.tool.join(','));
      }
      if (filters.component?.length) {
        queryParams.append('component', filters.component.join(','));
      }
      if (filters.dateRange) {
        queryParams.append('startDate', filters.dateRange.start.toISOString());
        queryParams.append('endDate', filters.dateRange.end.toISOString());
      }
    }

    const endpoint = `/fuzzing${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await this.request<FuzzingResult[]>(endpoint);
  }

  async getFuzzingResult(id: string): Promise<FuzzingResult> {
    return await this.request<FuzzingResult>(`/fuzzing/${id}`);
  }

  async startFuzzingCampaign(config: FuzzingConfiguration): Promise<FuzzingResult> {
    return await this.request<FuzzingResult>('/fuzzing', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async stopFuzzingCampaign(id: string): Promise<FuzzingResult> {
    return await this.request<FuzzingResult>(`/fuzzing/${id}/stop`, {
      method: 'POST',
    });
  }

  // Security Policy Management
  async getSecurityPolicies(): Promise<SecurityPolicy[]> {
    return await this.request<SecurityPolicy[]>('/policies');
  }

  async getSecurityPolicy(id: string): Promise<SecurityPolicy> {
    return await this.request<SecurityPolicy>(`/policies/${id}`);
  }

  async createSecurityPolicy(policy: Omit<SecurityPolicy, 'id' | 'createdAt' | 'updatedAt'>): Promise<SecurityPolicy> {
    return await this.request<SecurityPolicy>('/policies', {
      method: 'POST',
      body: JSON.stringify(policy),
    });
  }

  async updateSecurityPolicy(id: string, policy: Partial<SecurityPolicy>): Promise<SecurityPolicy> {
    return await this.request<SecurityPolicy>(`/policies/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(policy),
    });
  }

  async deleteSecurityPolicy(id: string): Promise<void> {
    await this.request<void>(`/policies/${id}`, {
      method: 'DELETE',
    });
  }

  // Security Scanning
  async startVulnerabilityScan(config: ScanConfiguration): Promise<SecurityScan> {
    return await this.request<SecurityScan>('/scans', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getSecurityScans(): Promise<SecurityScan[]> {
    return await this.request<SecurityScan[]>('/scans');
  }

  async getSecurityScan(id: string): Promise<SecurityScan> {
    return await this.request<SecurityScan>(`/scans/${id}`);
  }

  // Security Alerts
  async getSecurityAlerts(): Promise<SecurityAlert[]> {
    return await this.request<SecurityAlert[]>('/alerts');
  }

  async acknowledgeAlert(alertId: string): Promise<SecurityAlert> {
    return await this.request<SecurityAlert>(`/alerts/${alertId}/acknowledge`, {
      method: 'POST',
    });
  }

  async resolveAlert(alertId: string, resolution: string): Promise<SecurityAlert> {
    return await this.request<SecurityAlert>(`/alerts/${alertId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ resolution }),
    });
  }

  // Security Reporting
  async generateSecurityReport(config: ReportConfiguration): Promise<SecurityReport> {
    return await this.request<SecurityReport>('/reports', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getSecurityReports(): Promise<SecurityReport[]> {
    return await this.request<SecurityReport[]>('/reports');
  }

  async getSecurityReport(id: string): Promise<SecurityReport> {
    return await this.request<SecurityReport>(`/reports/${id}`);
  }

  // Utility Methods
  async healthCheck(): Promise<{ status: string; timestamp: Date }> {
    return await this.request<{ status: string; timestamp: Date }>('/health');
  }
}

// Singleton instance
export const securityService = new SecurityService();

export default SecurityService;