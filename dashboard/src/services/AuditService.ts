import {
  AuditEvent,
  AuditTrail,
  AuditSummary,
  ComplianceFramework,
  ComplianceAssessment,
  AssessmentReport,
  ComplianceViolation,
  AuditFilters,
  ViolationFilters,
  ReportOptions,
  ViolationResolution,
  AuditService as IAuditService,
  ResourceType,
  AuditAction,
  AuditOutcome,
  AuditSeverity,
  AuditCategory,
  AuditSource
} from '../types/audit';

class AuditService implements IAuditService {
  private baseUrl = '/api/audit';

  // Audit Events Management
  async getAuditEvents(filters?: AuditFilters): Promise<AuditEvent[]> {
    try {
      const queryParams = new URLSearchParams();
      
      if (filters) {
        if (filters.userId) queryParams.append('userId', filters.userId);
        if (filters.action) filters.action.forEach(a => queryParams.append('action', a));
        if (filters.resource) queryParams.append('resource', filters.resource);
        if (filters.resourceType) filters.resourceType.forEach(rt => queryParams.append('resourceType', rt));
        if (filters.outcome) filters.outcome.forEach(o => queryParams.append('outcome', o));
        if (filters.severity) filters.severity.forEach(s => queryParams.append('severity', s));
        if (filters.category) filters.category.forEach(c => queryParams.append('category', c));
        if (filters.source) filters.source.forEach(s => queryParams.append('source', s));
        if (filters.dateRange) {
          queryParams.append('startDate', filters.dateRange.start);
          queryParams.append('endDate', filters.dateRange.end);
        }
        if (filters.ipAddress) queryParams.append('ipAddress', filters.ipAddress);
        if (filters.sessionId) queryParams.append('sessionId', filters.sessionId);
        if (filters.search) queryParams.append('search', filters.search);
        if (filters.tags) filters.tags.forEach(t => queryParams.append('tags', t));
      }

      const response = await fetch(`${this.baseUrl}/events?${queryParams}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch audit events: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching audit events:', error);
      throw error;
    }
  }

  async getAuditTrail(resourceId: string, resourceType: ResourceType): Promise<AuditTrail> {
    try {
      const response = await fetch(`${this.baseUrl}/trail/${resourceType}/${resourceId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch audit trail: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching audit trail:', error);
      throw error;
    }
  }

  async createAuditEvent(event: Omit<AuditEvent, 'id' | 'timestamp'>): Promise<AuditEvent> {
    try {
      const response = await fetch(`${this.baseUrl}/events`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(event),
      });

      if (!response.ok) {
        throw new Error(`Failed to create audit event: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating audit event:', error);
      throw error;
    }
  }

  async searchAuditEvents(query: string, filters?: AuditFilters): Promise<AuditEvent[]> {
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('q', query);
      
      if (filters) {
        if (filters.userId) queryParams.append('userId', filters.userId);
        if (filters.action) filters.action.forEach(a => queryParams.append('action', a));
        if (filters.resourceType) filters.resourceType.forEach(rt => queryParams.append('resourceType', rt));
        if (filters.outcome) filters.outcome.forEach(o => queryParams.append('outcome', o));
        if (filters.severity) filters.severity.forEach(s => queryParams.append('severity', s));
        if (filters.category) filters.category.forEach(c => queryParams.append('category', c));
        if (filters.source) filters.source.forEach(s => queryParams.append('source', s));
        if (filters.dateRange) {
          queryParams.append('startDate', filters.dateRange.start);
          queryParams.append('endDate', filters.dateRange.end);
        }
        if (filters.tags) filters.tags.forEach(t => queryParams.append('tags', t));
      }

      const response = await fetch(`${this.baseUrl}/search?${queryParams}`);
      if (!response.ok) {
        throw new Error(`Failed to search audit events: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error searching audit events:', error);
      throw error;
    }
  }

  async exportAuditEvents(filters?: AuditFilters, format: 'csv' | 'json' | 'pdf' = 'csv'): Promise<string> {
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('format', format);
      
      if (filters) {
        if (filters.userId) queryParams.append('userId', filters.userId);
        if (filters.action) filters.action.forEach(a => queryParams.append('action', a));
        if (filters.resourceType) filters.resourceType.forEach(rt => queryParams.append('resourceType', rt));
        if (filters.outcome) filters.outcome.forEach(o => queryParams.append('outcome', o));
        if (filters.severity) filters.severity.forEach(s => queryParams.append('severity', s));
        if (filters.category) filters.category.forEach(c => queryParams.append('category', c));
        if (filters.source) filters.source.forEach(s => queryParams.append('source', s));
        if (filters.dateRange) {
          queryParams.append('startDate', filters.dateRange.start);
          queryParams.append('endDate', filters.dateRange.end);
        }
        if (filters.tags) filters.tags.forEach(t => queryParams.append('tags', t));
      }

      const response = await fetch(`${this.baseUrl}/export?${queryParams}`);
      if (!response.ok) {
        throw new Error(`Failed to export audit events: ${response.statusText}`);
      }
      
      if (format === 'pdf') {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit-events-${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        return 'Export completed';
      } else {
        return await response.text();
      }
    } catch (error) {
      console.error('Error exporting audit events:', error);
      throw error;
    }
  }

  async getAuditSummary(filters?: AuditFilters): Promise<AuditSummary> {
    try {
      const queryParams = new URLSearchParams();
      
      if (filters) {
        if (filters.userId) queryParams.append('userId', filters.userId);
        if (filters.action) filters.action.forEach(a => queryParams.append('action', a));
        if (filters.resourceType) filters.resourceType.forEach(rt => queryParams.append('resourceType', rt));
        if (filters.outcome) filters.outcome.forEach(o => queryParams.append('outcome', o));
        if (filters.severity) filters.severity.forEach(s => queryParams.append('severity', s));
        if (filters.category) filters.category.forEach(c => queryParams.append('category', c));
        if (filters.source) filters.source.forEach(s => queryParams.append('source', s));
        if (filters.dateRange) {
          queryParams.append('startDate', filters.dateRange.start);
          queryParams.append('endDate', filters.dateRange.end);
        }
        if (filters.tags) filters.tags.forEach(t => queryParams.append('tags', t));
      }

      const response = await fetch(`${this.baseUrl}/summary?${queryParams}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch audit summary: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching audit summary:', error);
      throw error;
    }
  }

  // Compliance Framework Management
  async getComplianceFrameworks(): Promise<ComplianceFramework[]> {
    try {
      const response = await fetch(`${this.baseUrl}/compliance/frameworks`);
      if (!response.ok) {
        throw new Error(`Failed to fetch compliance frameworks: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching compliance frameworks:', error);
      throw error;
    }
  }

  async getComplianceFramework(frameworkId: string): Promise<ComplianceFramework> {
    try {
      const response = await fetch(`${this.baseUrl}/compliance/frameworks/${frameworkId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch compliance framework: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching compliance framework:', error);
      throw error;
    }
  }

  async createComplianceFramework(framework: Omit<ComplianceFramework, 'id' | 'lastUpdated'>): Promise<ComplianceFramework> {
    try {
      const response = await fetch(`${this.baseUrl}/compliance/frameworks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(framework),
      });

      if (!response.ok) {
        throw new Error(`Failed to create compliance framework: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating compliance framework:', error);
      throw error;
    }
  }

  async updateComplianceFramework(frameworkId: string, updates: Partial<ComplianceFramework>): Promise<ComplianceFramework> {
    try {
      const response = await fetch(`${this.baseUrl}/compliance/frameworks/${frameworkId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error(`Failed to update compliance framework: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating compliance framework:', error);
      throw error;
    }
  }

  async deleteComplianceFramework(frameworkId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/compliance/frameworks/${frameworkId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete compliance framework: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error deleting compliance framework:', error);
      throw error;
    }
  }

  // Compliance Assessment Management
  async getComplianceAssessments(frameworkId?: string): Promise<ComplianceAssessment[]> {
    try {
      const queryParams = new URLSearchParams();
      if (frameworkId) queryParams.append('frameworkId', frameworkId);

      const response = await fetch(`${this.baseUrl}/compliance/assessments?${queryParams}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch compliance assessments: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching compliance assessments:', error);
      throw error;
    }
  }

  async createComplianceAssessment(assessment: Omit<ComplianceAssessment, 'id' | 'startDate'>): Promise<ComplianceAssessment> {
    try {
      const response = await fetch(`${this.baseUrl}/compliance/assessments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(assessment),
      });

      if (!response.ok) {
        throw new Error(`Failed to create compliance assessment: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating compliance assessment:', error);
      throw error;
    }
  }

  async updateComplianceAssessment(assessmentId: string, updates: Partial<ComplianceAssessment>): Promise<ComplianceAssessment> {
    try {
      const response = await fetch(`${this.baseUrl}/compliance/assessments/${assessmentId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error(`Failed to update compliance assessment: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating compliance assessment:', error);
      throw error;
    }
  }

  // Report Generation
  async generateComplianceReport(frameworkId: string, options?: ReportOptions): Promise<AssessmentReport> {
    try {
      const response = await fetch(`${this.baseUrl}/compliance/frameworks/${frameworkId}/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options || {}),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate compliance report: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error generating compliance report:', error);
      throw error;
    }
  }

  // Compliance Violations Management
  async getComplianceViolations(filters?: ViolationFilters): Promise<ComplianceViolation[]> {
    try {
      const queryParams = new URLSearchParams();
      
      if (filters) {
        if (filters.frameworkId) queryParams.append('frameworkId', filters.frameworkId);
        if (filters.controlId) queryParams.append('controlId', filters.controlId);
        if (filters.type) filters.type.forEach(t => queryParams.append('type', t));
        if (filters.severity) filters.severity.forEach(s => queryParams.append('severity', s));
        if (filters.status) filters.status.forEach(s => queryParams.append('status', s));
        if (filters.source) filters.source.forEach(s => queryParams.append('source', s));
        if (filters.assignee) queryParams.append('assignee', filters.assignee);
        if (filters.dateRange) {
          queryParams.append('startDate', filters.dateRange.start);
          queryParams.append('endDate', filters.dateRange.end);
        }
        if (filters.search) queryParams.append('search', filters.search);
      }

      const response = await fetch(`${this.baseUrl}/compliance/violations?${queryParams}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch compliance violations: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching compliance violations:', error);
      throw error;
    }
  }

  async resolveComplianceViolation(violationId: string, resolution: ViolationResolution): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/compliance/violations/${violationId}/resolve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(resolution),
      });

      if (!response.ok) {
        throw new Error(`Failed to resolve compliance violation: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error resolving compliance violation:', error);
      throw error;
    }
  }

  // Audit Event Logging Utilities
  async logUserAction(
    action: AuditAction,
    resource: string,
    resourceType: ResourceType,
    details: {
      description: string;
      context?: Record<string, any>;
      changes?: Array<{
        field: string;
        oldValue: any;
        newValue: any;
      }>;
    },
    severity: AuditSeverity = 'info'
  ): Promise<AuditEvent> {
    const event = {
      userId: 'current-user', // This would be populated from auth context
      username: 'Current User',
      userEmail: 'user@example.com',
      action,
      resource,
      resourceType,
      details: {
        description: details.description,
        context: details.context || {},
        changes: details.changes?.map(change => ({
          field: change.field,
          oldValue: change.oldValue,
          newValue: change.newValue,
          changeType: 'update' as const
        })) || []
      },
      outcome: 'success' as AuditOutcome,
      severity,
      category: 'operational' as AuditCategory,
      source: 'user' as AuditSource,
      metadata: {},
      tags: []
    };

    return this.createAuditEvent(event);
  }

  // Data Masking for Sensitive Information
  maskSensitiveData(data: any, sensitiveFields: string[] = ['password', 'token', 'key', 'secret']): any {
    if (typeof data !== 'object' || data === null) {
      return data;
    }

    if (Array.isArray(data)) {
      return data.map(item => this.maskSensitiveData(item, sensitiveFields));
    }

    const masked = { ...data };
    
    for (const [key, value] of Object.entries(masked)) {
      const lowerKey = key.toLowerCase();
      
      if (sensitiveFields.some(field => lowerKey.includes(field))) {
        masked[key] = '***MASKED***';
      } else if (typeof value === 'object' && value !== null) {
        masked[key] = this.maskSensitiveData(value, sensitiveFields);
      }
    }

    return masked;
  }

  // Immutable Audit Logging
  async createImmutableAuditEntry(
    event: Omit<AuditEvent, 'id' | 'timestamp'>,
    digitalSignature?: string
  ): Promise<AuditEvent> {
    try {
      // Mask sensitive data before logging
      const maskedEvent = {
        ...event,
        details: {
          ...event.details,
          context: this.maskSensitiveData(event.details.context),
          beforeState: this.maskSensitiveData(event.details.beforeState),
          afterState: this.maskSensitiveData(event.details.afterState)
        }
      };

      // Add integrity metadata
      const eventWithIntegrity = {
        ...maskedEvent,
        metadata: {
          ...maskedEvent.metadata,
          immutable: true,
          digitalSignature,
          hash: await this.generateEventHash(maskedEvent)
        }
      };

      return this.createAuditEvent(eventWithIntegrity);
    } catch (error) {
      console.error('Error creating immutable audit entry:', error);
      throw error;
    }
  }

  // Generate hash for audit event integrity
  private async generateEventHash(event: any): Promise<string> {
    const eventString = JSON.stringify(event, Object.keys(event).sort());
    const encoder = new TextEncoder();
    const data = encoder.encode(eventString);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  // Compliance Tracking Utilities
  async trackComplianceStatus(frameworkId: string): Promise<{
    overallScore: number;
    compliantControls: number;
    totalControls: number;
    criticalGaps: number;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/compliance/frameworks/${frameworkId}/status`);
      if (!response.ok) {
        throw new Error(`Failed to fetch compliance status: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error tracking compliance status:', error);
      throw error;
    }
  }

  async scheduleComplianceAssessment(
    frameworkId: string,
    assessmentType: 'self-assessment' | 'internal-audit' | 'external-audit',
    scheduledDate: string,
    assessor: string
  ): Promise<ComplianceAssessment> {
    try {
      const assessment = {
        frameworkId,
        name: `${assessmentType} - ${new Date(scheduledDate).toLocaleDateString()}`,
        description: `Scheduled ${assessmentType} for compliance framework`,
        type: assessmentType,
        status: 'planned' as const,
        scope: {
          systems: [],
          processes: [],
          controls: [],
          timeframe: {
            start: scheduledDate,
            end: new Date(new Date(scheduledDate).getTime() + 30 * 24 * 60 * 60 * 1000).toISOString()
          },
          exclusions: []
        },
        methodology: 'Standard compliance assessment methodology',
        assessor,
        findings: [],
        recommendations: [],
        score: {
          overall: 0,
          byCategory: {},
          byControl: {},
          trend: [],
          lastUpdated: new Date().toISOString()
        },
        report: {
          id: '',
          assessmentId: '',
          title: '',
          summary: '',
          methodology: '',
          scope: {
            systems: [],
            processes: [],
            controls: [],
            timeframe: { start: '', end: '' },
            exclusions: []
          },
          findings: [],
          recommendations: [],
          score: {
            overall: 0,
            byCategory: {},
            byControl: {},
            trend: [],
            lastUpdated: ''
          },
          appendices: [],
          generatedAt: '',
          generatedBy: '',
          version: '1.0',
          format: 'pdf',
          distribution: []
        },
        metadata: {}
      };

      return this.createComplianceAssessment(assessment);
    } catch (error) {
      console.error('Error scheduling compliance assessment:', error);
      throw error;
    }
  }
}

export const auditService = new AuditService();
export default auditService;