// Audit & Compliance Type Definitions

export interface AuditEvent {
  id: string
  timestamp: string
  userId: string
  username: string
  userEmail: string
  action: AuditAction
  resource: string
  resourceId?: string
  resourceType: ResourceType
  details: AuditDetails
  outcome: AuditOutcome
  severity: AuditSeverity
  category: AuditCategory
  source: AuditSource
  sessionId?: string
  ipAddress?: string
  userAgent?: string
  location?: GeoLocation
  metadata: Record<string, any>
  tags: string[]
}

export interface AuditDetails {
  description: string
  changes?: ChangeRecord[]
  context: Record<string, any>
  beforeState?: any
  afterState?: any
  affectedFields?: string[]
  reason?: string
  approver?: string
  requestId?: string
}

export interface ChangeRecord {
  field: string
  oldValue: any
  newValue: any
  changeType: ChangeType
}

export interface GeoLocation {
  country: string
  region: string
  city: string
  latitude?: number
  longitude?: number
  timezone?: string
}

export interface AuditTrail {
  resourceId: string
  resourceType: ResourceType
  events: AuditEvent[]
  summary: AuditSummary
  timeline: AuditTimelineEntry[]
  totalEvents: number
  dateRange: {
    start: string
    end: string
  }
}

export interface AuditSummary {
  totalEvents: number
  eventsByAction: Record<AuditAction, number>
  eventsByUser: Record<string, number>
  eventsByOutcome: Record<AuditOutcome, number>
  eventsBySeverity: Record<AuditSeverity, number>
  uniqueUsers: number
  timeSpan: string
  mostActiveUser: string
  mostCommonAction: AuditAction
}

export interface AuditTimelineEntry {
  timestamp: string
  event: AuditEvent
  relatedEvents: string[]
  impact: ImpactLevel
}

export interface ComplianceFramework {
  id: string
  name: string
  displayName: string
  version: string
  description: string
  type: ComplianceType
  status: FrameworkStatus
  controls: ComplianceControl[]
  requirements: ComplianceRequirement[]
  assessments: ComplianceAssessment[]
  certifications: Certification[]
  lastUpdated: string
  nextReview: string
  owner: string
  tags: string[]
  metadata: Record<string, any>
}

export interface ComplianceControl {
  id: string
  frameworkId: string
  controlId: string
  name: string
  description: string
  category: ControlCategory
  type: ControlType
  status: ControlStatus
  implementation: ControlImplementation
  evidence: Evidence[]
  tests: ComplianceTest[]
  gaps: ComplianceGap[]
  remediation: RemediationPlan
  lastAssessed: string
  nextAssessment: string
  assignee: string
  priority: CompliancePriority
  riskLevel: RiskLevel
  metadata: Record<string, any>
}

export interface ComplianceRequirement {
  id: string
  frameworkId: string
  requirementId: string
  title: string
  description: string
  category: RequirementCategory
  mandatory: boolean
  controls: string[]
  status: RequirementStatus
  compliance: ComplianceLevel
  evidence: Evidence[]
  lastVerified: string
  nextVerification: string
  owner: string
  metadata: Record<string, any>
}

export interface ComplianceAssessment {
  id: string
  frameworkId: string
  name: string
  description: string
  type: AssessmentType
  status: AssessmentStatus
  scope: AssessmentScope
  methodology: string
  assessor: string
  startDate: string
  endDate?: string
  duration?: number
  findings: AssessmentFinding[]
  recommendations: ComplianceRecommendation[]
  score: ComplianceScore
  report: AssessmentReport
  metadata: Record<string, any>
}

export interface AssessmentScope {
  systems: string[]
  processes: string[]
  controls: string[]
  timeframe: {
    start: string
    end: string
  }
  exclusions: string[]
}

export interface AssessmentFinding {
  id: string
  assessmentId: string
  controlId: string
  type: FindingType
  severity: FindingSeverity
  title: string
  description: string
  evidence: Evidence[]
  impact: ImpactAssessment
  recommendation: string
  status: FindingStatus
  assignee?: string
  dueDate?: string
  resolvedDate?: string
  metadata: Record<string, any>
}

export interface ImpactAssessment {
  likelihood: LikelihoodLevel
  impact: ImpactLevel
  riskScore: number
  businessImpact: string
  technicalImpact: string
  complianceImpact: string
}

export interface ComplianceRecommendation {
  id: string
  title: string
  description: string
  priority: RecommendationPriority
  category: RecommendationCategory
  effort: EffortEstimate
  timeline: string
  resources: string[]
  dependencies: string[]
  benefits: string[]
  risks: string[]
  implementation: ImplementationPlan
  status: RecommendationStatus
  assignee?: string
  dueDate?: string
  metadata: Record<string, any>
}

export interface ImplementationPlan {
  phases: ImplementationPhase[]
  milestones: Milestone[]
  resources: ResourceRequirement[]
  timeline: string
  budget?: number
  risks: string[]
  successCriteria: string[]
}

export interface ImplementationPhase {
  id: string
  name: string
  description: string
  duration: string
  dependencies: string[]
  deliverables: string[]
  resources: string[]
  status: PhaseStatus
}

export interface Milestone {
  id: string
  name: string
  description: string
  dueDate: string
  status: MilestoneStatus
  deliverables: string[]
  criteria: string[]
}

export interface ResourceRequirement {
  type: ResourceType
  role: string
  effort: string
  skills: string[]
  availability: string
}

export interface Evidence {
  id: string
  type: EvidenceType
  name: string
  description: string
  source: string
  location: string
  format: string
  size?: number
  hash?: string
  collectedAt: string
  collectedBy: string
  verified: boolean
  verifiedAt?: string
  verifiedBy?: string
  retention: RetentionPolicy
  metadata: Record<string, any>
}

export interface RetentionPolicy {
  period: string
  action: RetentionAction
  reason: string
  approver?: string
}

export interface ComplianceTest {
  id: string
  controlId: string
  name: string
  description: string
  type: TestType
  frequency: TestFrequency
  automated: boolean
  procedure: TestProcedure
  criteria: TestCriteria
  lastRun: string
  nextRun: string
  results: TestResult[]
  status: TestStatus
  assignee: string
  metadata: Record<string, any>
}

export interface TestProcedure {
  steps: TestStep[]
  tools: string[]
  environment: string
  prerequisites: string[]
  duration: string
}

export interface TestStep {
  id: string
  order: number
  description: string
  action: string
  expectedResult: string
  actualResult?: string
  status?: StepStatus
  evidence?: string[]
}

export interface TestCriteria {
  passCriteria: string[]
  failCriteria: string[]
  warningCriteria: string[]
  measurements: Measurement[]
}

export interface Measurement {
  name: string
  type: MeasurementType
  unit: string
  target: number
  threshold: number
  actual?: number
}

export interface TestResult {
  id: string
  testId: string
  runDate: string
  runBy: string
  status: TestResultStatus
  score: number
  findings: TestFinding[]
  evidence: Evidence[]
  duration: number
  environment: string
  metadata: Record<string, any>
}

export interface TestFinding {
  id: string
  type: FindingType
  severity: FindingSeverity
  description: string
  evidence: string[]
  recommendation: string
}

export interface ComplianceGap {
  id: string
  controlId: string
  type: GapType
  severity: GapSeverity
  title: string
  description: string
  currentState: string
  requiredState: string
  impact: ImpactAssessment
  remediation: RemediationPlan
  status: GapStatus
  assignee?: string
  dueDate?: string
  metadata: Record<string, any>
}

export interface RemediationPlan {
  id: string
  title: string
  description: string
  approach: string
  steps: RemediationStep[]
  timeline: string
  effort: EffortEstimate
  cost?: number
  resources: string[]
  risks: string[]
  dependencies: string[]
  successCriteria: string[]
  status: RemediationStatus
  assignee?: string
  approver?: string
  startDate?: string
  targetDate?: string
  completedDate?: string
}

export interface RemediationStep {
  id: string
  order: number
  title: string
  description: string
  action: string
  assignee: string
  duration: string
  dependencies: string[]
  deliverables: string[]
  status: StepStatus
  startDate?: string
  endDate?: string
}

export interface EffortEstimate {
  hours: number
  complexity: ComplexityLevel
  confidence: ConfidenceLevel
  assumptions: string[]
  risks: string[]
}

export interface ComplianceScore {
  overall: number
  byCategory: Record<string, number>
  byControl: Record<string, number>
  trend: ScoreTrend[]
  lastUpdated: string
}

export interface ScoreTrend {
  date: string
  score: number
  change: number
  factors: string[]
}

export interface AssessmentReport {
  id: string
  assessmentId: string
  title: string
  summary: string
  methodology: string
  scope: AssessmentScope
  findings: AssessmentFinding[]
  recommendations: ComplianceRecommendation[]
  score: ComplianceScore
  appendices: ReportAppendix[]
  generatedAt: string
  generatedBy: string
  approvedAt?: string
  approvedBy?: string
  version: string
  format: ReportFormat
  distribution: string[]
}

export interface ReportAppendix {
  id: string
  title: string
  type: AppendixType
  content: string
  attachments: string[]
}

export interface Certification {
  id: string
  frameworkId: string
  name: string
  type: CertificationType
  status: CertificationStatus
  issuer: string
  issuedDate: string
  expiryDate: string
  renewalDate?: string
  scope: string
  conditions: string[]
  evidence: Evidence[]
  auditor?: string
  auditDate?: string
  nextAudit?: string
  metadata: Record<string, any>
}

export interface ComplianceViolation {
  id: string
  frameworkId: string
  controlId: string
  type: ViolationType
  severity: ViolationSeverity
  title: string
  description: string
  detectedAt: string
  detectedBy: string
  source: ViolationSource
  evidence: Evidence[]
  impact: ImpactAssessment
  status: ViolationStatus
  assignee?: string
  resolvedAt?: string
  resolvedBy?: string
  resolution: string
  preventionMeasures: string[]
  metadata: Record<string, any>
}

// Enums and Union Types
export type AuditAction = 'create' | 'read' | 'update' | 'delete' | 'execute' | 'login' | 'logout' | 'access' | 'export' | 'import' | 'approve' | 'reject' | 'configure' | 'deploy'
export type ResourceType = 'user' | 'role' | 'permission' | 'test' | 'environment' | 'configuration' | 'data' | 'system' | 'integration' | 'policy' | 'report'
export type AuditOutcome = 'success' | 'failure' | 'partial' | 'denied' | 'error'
export type AuditSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type AuditCategory = 'authentication' | 'authorization' | 'data-access' | 'configuration' | 'system' | 'security' | 'compliance' | 'operational'
export type AuditSource = 'user' | 'system' | 'api' | 'integration' | 'automated' | 'scheduled'
export type ChangeType = 'create' | 'update' | 'delete' | 'move' | 'rename'
export type ComplianceType = 'regulatory' | 'industry' | 'internal' | 'contractual' | 'certification'
export type FrameworkStatus = 'active' | 'draft' | 'deprecated' | 'archived'
export type ControlCategory = 'access-control' | 'audit' | 'configuration' | 'data-protection' | 'incident-response' | 'risk-management' | 'security' | 'operational'
export type ControlType = 'preventive' | 'detective' | 'corrective' | 'compensating' | 'directive'
export type ControlStatus = 'implemented' | 'partially-implemented' | 'not-implemented' | 'not-applicable' | 'under-review'
export type ControlImplementation = 'manual' | 'automated' | 'hybrid' | 'outsourced'
export type RequirementCategory = 'technical' | 'administrative' | 'physical' | 'legal' | 'operational'
export type RequirementStatus = 'compliant' | 'non-compliant' | 'partial' | 'not-applicable' | 'under-review'
export type ComplianceLevel = 'full' | 'substantial' | 'partial' | 'minimal' | 'none'
export type AssessmentType = 'self-assessment' | 'internal-audit' | 'external-audit' | 'certification' | 'gap-analysis'
export type AssessmentStatus = 'planned' | 'in-progress' | 'completed' | 'cancelled' | 'on-hold'
export type FindingType = 'gap' | 'weakness' | 'non-compliance' | 'observation' | 'best-practice'
export type FindingSeverity = 'critical' | 'high' | 'medium' | 'low' | 'informational'
export type FindingStatus = 'open' | 'in-progress' | 'resolved' | 'accepted-risk' | 'false-positive'
export type LikelihoodLevel = 'very-high' | 'high' | 'medium' | 'low' | 'very-low'
export type ImpactLevel = 'very-high' | 'high' | 'medium' | 'low' | 'very-low'
export type RecommendationPriority = 'critical' | 'high' | 'medium' | 'low'
export type RecommendationCategory = 'technical' | 'process' | 'policy' | 'training' | 'governance'
export type RecommendationStatus = 'open' | 'in-progress' | 'completed' | 'deferred' | 'rejected'
export type PhaseStatus = 'not-started' | 'in-progress' | 'completed' | 'on-hold' | 'cancelled'
export type MilestoneStatus = 'not-started' | 'in-progress' | 'completed' | 'overdue' | 'cancelled'
export type EvidenceType = 'document' | 'screenshot' | 'log' | 'configuration' | 'report' | 'certificate' | 'policy' | 'procedure'
export type RetentionAction = 'archive' | 'delete' | 'review' | 'extend'
export type TestType = 'manual' | 'automated' | 'hybrid' | 'interview' | 'observation' | 'document-review'
export type TestFrequency = 'continuous' | 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annually' | 'ad-hoc'
export type TestStatus = 'active' | 'inactive' | 'draft' | 'deprecated'
export type StepStatus = 'not-started' | 'in-progress' | 'completed' | 'failed' | 'skipped'
export type MeasurementType = 'count' | 'percentage' | 'duration' | 'size' | 'score'
export type TestResultStatus = 'pass' | 'fail' | 'warning' | 'not-applicable' | 'error'
export type GapType = 'control-gap' | 'process-gap' | 'technology-gap' | 'skill-gap' | 'documentation-gap'
export type GapSeverity = 'critical' | 'high' | 'medium' | 'low'
export type GapStatus = 'identified' | 'analyzing' | 'planning' | 'remediating' | 'resolved' | 'accepted'
export type RemediationStatus = 'planned' | 'in-progress' | 'completed' | 'on-hold' | 'cancelled'
export type ComplexityLevel = 'low' | 'medium' | 'high' | 'very-high'
export type ConfidenceLevel = 'low' | 'medium' | 'high'
export type ReportFormat = 'pdf' | 'html' | 'docx' | 'xlsx' | 'json'
export type AppendixType = 'evidence' | 'procedure' | 'reference' | 'glossary' | 'technical'
export type CertificationType = 'iso' | 'soc' | 'pci' | 'hipaa' | 'gdpr' | 'nist' | 'custom'
export type CertificationStatus = 'active' | 'expired' | 'suspended' | 'revoked' | 'pending'
export type ViolationType = 'policy-violation' | 'control-failure' | 'process-deviation' | 'unauthorized-access' | 'data-breach'
export type ViolationSeverity = 'critical' | 'high' | 'medium' | 'low'
export type ViolationSource = 'automated-scan' | 'manual-review' | 'incident' | 'audit' | 'self-reported'
export type ViolationStatus = 'open' | 'investigating' | 'resolved' | 'false-positive' | 'accepted-risk'
export type CompliancePriority = 'critical' | 'high' | 'medium' | 'low'
export type RiskLevel = 'very-high' | 'high' | 'medium' | 'low' | 'very-low'

// Service Interfaces
export interface AuditService {
  getAuditEvents(filters?: AuditFilters): Promise<AuditEvent[]>
  getAuditTrail(resourceId: string, resourceType: ResourceType): Promise<AuditTrail>
  createAuditEvent(event: Omit<AuditEvent, 'id' | 'timestamp'>): Promise<AuditEvent>
  searchAuditEvents(query: string, filters?: AuditFilters): Promise<AuditEvent[]>
  exportAuditEvents(filters?: AuditFilters, format?: 'csv' | 'json' | 'pdf'): Promise<string>
  getAuditSummary(filters?: AuditFilters): Promise<AuditSummary>
  getComplianceFrameworks(): Promise<ComplianceFramework[]>
  getComplianceFramework(frameworkId: string): Promise<ComplianceFramework>
  createComplianceFramework(framework: Omit<ComplianceFramework, 'id' | 'lastUpdated'>): Promise<ComplianceFramework>
  updateComplianceFramework(frameworkId: string, updates: Partial<ComplianceFramework>): Promise<ComplianceFramework>
  deleteComplianceFramework(frameworkId: string): Promise<void>
  getComplianceAssessments(frameworkId?: string): Promise<ComplianceAssessment[]>
  createComplianceAssessment(assessment: Omit<ComplianceAssessment, 'id' | 'startDate'>): Promise<ComplianceAssessment>
  updateComplianceAssessment(assessmentId: string, updates: Partial<ComplianceAssessment>): Promise<ComplianceAssessment>
  generateComplianceReport(frameworkId: string, options?: ReportOptions): Promise<AssessmentReport>
  getComplianceViolations(filters?: ViolationFilters): Promise<ComplianceViolation[]>
  resolveComplianceViolation(violationId: string, resolution: ViolationResolution): Promise<void>
}

export interface AuditFilters {
  userId?: string
  action?: AuditAction[]
  resource?: string
  resourceType?: ResourceType[]
  outcome?: AuditOutcome[]
  severity?: AuditSeverity[]
  category?: AuditCategory[]
  source?: AuditSource[]
  dateRange?: {
    start: string
    end: string
  }
  ipAddress?: string
  sessionId?: string
  search?: string
  tags?: string[]
}

export interface ViolationFilters {
  frameworkId?: string
  controlId?: string
  type?: ViolationType[]
  severity?: ViolationSeverity[]
  status?: ViolationStatus[]
  source?: ViolationSource[]
  assignee?: string
  dateRange?: {
    start: string
    end: string
  }
  search?: string
}

export interface ReportOptions {
  format: ReportFormat
  includeEvidence: boolean
  includeRecommendations: boolean
  includeAppendices: boolean
  customSections?: string[]
  distribution?: string[]
}

export interface ViolationResolution {
  status: ViolationStatus
  resolution: string
  preventionMeasures: string[]
  assignee?: string
  dueDate?: string
  metadata?: Record<string, any>
}

// Constants
export const AUDIT_ACTIONS: AuditAction[] = ['create', 'read', 'update', 'delete', 'execute', 'login', 'logout', 'access', 'export', 'import', 'approve', 'reject', 'configure', 'deploy']
export const AUDIT_OUTCOMES: AuditOutcome[] = ['success', 'failure', 'partial', 'denied', 'error']
export const AUDIT_SEVERITIES: AuditSeverity[] = ['critical', 'high', 'medium', 'low', 'info']
export const COMPLIANCE_TYPES: ComplianceType[] = ['regulatory', 'industry', 'internal', 'contractual', 'certification']

export const DEFAULT_AUDIT_FILTERS: AuditFilters = {
  dateRange: {
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    end: new Date().toISOString()
  }
}

export const SEVERITY_COLORS = {
  critical: '#ff4d4f',
  high: '#ff7a45',
  medium: '#ffa940',
  low: '#52c41a',
  info: '#1890ff'
} as const

export const STATUS_COLORS = {
  'compliant': 'green',
  'non-compliant': 'red',
  'partial': 'orange',
  'not-applicable': 'gray',
  'under-review': 'blue'
} as const