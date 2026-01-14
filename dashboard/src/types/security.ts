// Security Dashboard Types

export interface SecurityMetrics {
  vulnerabilityCount: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  complianceScore: number;
  activeFuzzingCampaigns: number;
  recentFindings: SecurityFinding[];
  securityTrends: SecurityTrend[];
}

export interface SecurityFinding {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  type: 'vulnerability' | 'compliance' | 'fuzzing';
  title: string;
  description: string;
  affectedComponents: string[];
  discoveredAt: Date;
  status: 'open' | 'investigating' | 'resolved' | 'false_positive';
  cveId?: string;
  remediation?: string;
  assignee?: string;
  resolvedAt?: Date;
}

export interface SecurityTrend {
  date: string;
  vulnerabilities: number;
  resolved: number;
}

export interface Vulnerability {
  id: string;
  cveId?: string;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  cvssScore?: number;
  affectedComponents: string[];
  discoveryMethod: 'scan' | 'fuzzing' | 'manual' | 'external';
  status: 'open' | 'investigating' | 'patched' | 'mitigated' | 'false_positive';
  assignee?: string;
  remediation?: string;
  discoveredAt: Date;
  resolvedAt?: Date;
  tags?: string[];
  references?: string[];
  exploitability?: 'high' | 'medium' | 'low' | 'none';
  impact?: 'high' | 'medium' | 'low';
}

export interface SecurityPolicy {
  id: string;
  name: string;
  framework: 'soc2' | 'iso27001' | 'nist' | 'custom';
  rules: SecurityRule[];
  thresholds: SecurityThreshold[];
  enabled: boolean;
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;
  description?: string;
}

export interface SecurityRule {
  id: string;
  type: 'vulnerability' | 'compliance' | 'access' | 'data';
  condition: string;
  action: 'alert' | 'block' | 'log' | 'escalate';
  severity: 'low' | 'medium' | 'high' | 'critical';
  enabled: boolean;
  description?: string;
}

export interface SecurityThreshold {
  severity: 'critical' | 'high' | 'medium' | 'low';
  maxCount: number;
  action: 'block' | 'warn' | 'log';
  timeWindow?: number; // in hours
}

export interface FuzzingResult {
  id: string;
  campaign: string;
  status: 'running' | 'completed' | 'failed' | 'paused';
  startTime: Date;
  endTime?: Date;
  duration: number; // in hours
  crashCount: number;
  uniqueCrashes: number;
  coverage: number; // percentage
  findings: string[];
  testCases: number;
  targetComponent: string;
  fuzzingTool: string;
  configuration?: FuzzingConfiguration;
}

export interface FuzzingConfiguration {
  tool: 'syzkaller' | 'afl' | 'libfuzzer' | 'custom';
  target: string;
  duration: number;
  parallelJobs: number;
  seedFiles?: string[];
  dictionary?: string;
  options?: Record<string, any>;
}

export interface ComplianceFramework {
  id: string;
  name: string;
  version: string;
  requirements: ComplianceRequirement[];
  certificationLevel?: string;
  validUntil?: Date;
}

export interface ComplianceRequirement {
  id: string;
  title: string;
  description: string;
  category: string;
  mandatory: boolean;
  status: 'compliant' | 'non_compliant' | 'partial' | 'not_applicable';
  evidence?: string[];
  lastAssessed?: Date;
  assessor?: string;
  notes?: string;
}

export interface SecurityScan {
  id: string;
  type: 'vulnerability' | 'compliance' | 'configuration' | 'dependency';
  status: 'running' | 'completed' | 'failed' | 'queued';
  startTime: Date;
  endTime?: Date;
  target: string;
  tool: string;
  findings: SecurityFinding[];
  summary: ScanSummary;
  configuration?: Record<string, any>;
}

export interface ScanSummary {
  totalFindings: number;
  criticalCount: number;
  highCount: number;
  mediumCount: number;
  lowCount: number;
  falsePositiveCount: number;
  newFindings: number;
  resolvedFindings: number;
}

export interface SecurityAlert {
  id: string;
  type: 'vulnerability' | 'compliance' | 'policy_violation' | 'security_event';
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  description: string;
  source: string;
  timestamp: Date;
  status: 'active' | 'acknowledged' | 'resolved' | 'suppressed';
  assignee?: string;
  acknowledgedAt?: Date;
  resolvedAt?: Date;
  metadata?: Record<string, any>;
  relatedFindings?: string[];
}

export interface SecurityDashboardConfig {
  refreshInterval: number; // in seconds
  defaultTimeRange: string;
  alertThresholds: Record<string, number>;
  visibleMetrics: string[];
  autoRefresh: boolean;
  notificationSettings: NotificationSettings;
}

export interface NotificationSettings {
  email: boolean;
  slack: boolean;
  webhook?: string;
  severityFilter: ('critical' | 'high' | 'medium' | 'low')[];
  channels: NotificationChannel[];
}

export interface NotificationChannel {
  type: 'email' | 'slack' | 'teams' | 'webhook' | 'sms';
  endpoint: string;
  enabled: boolean;
  filters?: NotificationFilter[];
}

export interface NotificationFilter {
  field: string;
  operator: 'equals' | 'contains' | 'greater_than' | 'less_than';
  value: any;
}

export interface SecurityReport {
  id: string;
  title: string;
  type: 'vulnerability' | 'compliance' | 'security_posture' | 'custom';
  generatedAt: Date;
  generatedBy: string;
  timeRange: {
    start: Date;
    end: Date;
  };
  summary: ReportSummary;
  sections: ReportSection[];
  format: 'pdf' | 'html' | 'json' | 'csv';
  status: 'generating' | 'completed' | 'failed';
}

export interface ReportSummary {
  totalVulnerabilities: number;
  criticalVulnerabilities: number;
  complianceScore: number;
  riskScore: number;
  trendsAnalysis: string;
  recommendations: string[];
}

export interface ReportSection {
  title: string;
  content: string;
  charts?: ChartData[];
  tables?: TableData[];
}

export interface ChartData {
  type: 'line' | 'bar' | 'pie' | 'area';
  title: string;
  data: any[];
  options?: Record<string, any>;
}

export interface TableData {
  title: string;
  headers: string[];
  rows: any[][];
}

// Service interfaces
export interface SecurityService {
  getSecurityMetrics(): Promise<SecurityMetrics>;
  getVulnerabilities(filters?: VulnerabilityFilter): Promise<Vulnerability[]>;
  getFuzzingResults(filters?: FuzzingFilter): Promise<FuzzingResult[]>;
  getSecurityPolicies(): Promise<SecurityPolicy[]>;
  createSecurityPolicy(policy: Omit<SecurityPolicy, 'id' | 'createdAt' | 'updatedAt'>): Promise<SecurityPolicy>;
  updateSecurityPolicy(id: string, policy: Partial<SecurityPolicy>): Promise<SecurityPolicy>;
  deleteSecurityPolicy(id: string): Promise<void>;
  startVulnerabilityScan(config: ScanConfiguration): Promise<SecurityScan>;
  startFuzzingCampaign(config: FuzzingConfiguration): Promise<FuzzingResult>;
  acknowledgeAlert(alertId: string): Promise<void>;
  resolveAlert(alertId: string, resolution: string): Promise<void>;
  generateSecurityReport(config: ReportConfiguration): Promise<SecurityReport>;
}

export interface VulnerabilityFilter {
  severity?: ('critical' | 'high' | 'medium' | 'low')[];
  status?: ('open' | 'investigating' | 'patched' | 'mitigated' | 'false_positive')[];
  components?: string[];
  dateRange?: {
    start: Date;
    end: Date;
  };
  assignee?: string;
  tags?: string[];
}

export interface FuzzingFilter {
  status?: ('running' | 'completed' | 'failed' | 'paused')[];
  tool?: string[];
  dateRange?: {
    start: Date;
    end: Date;
  };
  component?: string[];
}

export interface ScanConfiguration {
  type: 'vulnerability' | 'compliance' | 'configuration' | 'dependency';
  target: string;
  tool: string;
  options?: Record<string, any>;
  schedule?: CronSchedule;
}

export interface CronSchedule {
  enabled: boolean;
  expression: string;
  timezone?: string;
}

export interface ReportConfiguration {
  type: 'vulnerability' | 'compliance' | 'security_posture' | 'custom';
  timeRange: {
    start: Date;
    end: Date;
  };
  includeCharts: boolean;
  includeTables: boolean;
  format: 'pdf' | 'html' | 'json' | 'csv';
  filters?: Record<string, any>;
  customSections?: string[];
}

// API Response types
export interface SecurityMetricsResponse {
  success: boolean;
  data: SecurityMetrics;
  timestamp: Date;
}

export interface VulnerabilitiesResponse {
  success: boolean;
  data: Vulnerability[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
  timestamp: Date;
}

export class SecurityError extends Error {
  public code: string;
  public details?: Record<string, any>;
  public timestamp: Date;

  constructor(code: string, message: string, details?: Record<string, any>, timestamp?: Date) {
    super(message);
    this.name = 'SecurityError';
    this.code = code;
    this.details = details;
    this.timestamp = timestamp || new Date();
  }
}