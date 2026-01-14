// Integration Management Type Definitions

export interface Integration {
  id: string
  name: string
  displayName: string
  description: string
  type: IntegrationType
  provider: IntegrationProvider
  status: IntegrationStatus
  category: IntegrationCategory
  configuration: IntegrationConfig
  authentication: AuthenticationConfig
  webhooks: WebhookConfig[]
  metrics: IntegrationMetrics
  health: HealthCheck
  lastActivity: string
  createdAt: string
  updatedAt: string
  createdBy: string
  tags: string[]
  metadata: Record<string, any>
}

export interface IntegrationConfig {
  endpoint: string
  version?: string
  timeout: number
  retryPolicy: RetryPolicy
  rateLimit: RateLimit
  headers: Record<string, string>
  parameters: Record<string, any>
  features: IntegrationFeature[]
  environment: EnvironmentConfig
  security: SecurityConfig
}

export interface AuthenticationConfig {
  type: AuthenticationType
  credentials: CredentialConfig
  tokenRefresh: TokenRefreshConfig
  scopes: string[]
  permissions: string[]
  expiry?: string
  lastRefresh?: string
}

export interface CredentialConfig {
  apiKey?: string
  clientId?: string
  clientSecret?: string
  username?: string
  password?: string
  token?: string
  certificate?: CertificateConfig
  oauth?: OAuthConfig
  custom?: Record<string, any>
}

export interface CertificateConfig {
  cert: string
  key: string
  ca?: string
  passphrase?: string
  format: CertificateFormat
}

export interface OAuthConfig {
  authUrl: string
  tokenUrl: string
  redirectUri: string
  state?: string
  codeChallenge?: string
  codeChallengeMethod?: string
}

export interface TokenRefreshConfig {
  enabled: boolean
  threshold: number
  endpoint?: string
  method?: string
  headers?: Record<string, string>
  body?: Record<string, any>
}

export interface WebhookConfig {
  id: string
  integrationId: string
  name: string
  description: string
  type: WebhookType
  direction: WebhookDirection
  endpoint: string
  method: HTTPMethod
  headers: Record<string, string>
  authentication: WebhookAuth
  payload: PayloadConfig
  filters: WebhookFilter[]
  retryPolicy: RetryPolicy
  security: WebhookSecurity
  status: WebhookStatus
  lastTriggered?: string
  statistics: WebhookStatistics
  metadata: Record<string, any>
}

export interface WebhookAuth {
  type: WebhookAuthType
  secret?: string
  signature?: SignatureConfig
  headers?: Record<string, string>
  query?: Record<string, string>
}

export interface SignatureConfig {
  algorithm: SignatureAlgorithm
  header: string
  prefix?: string
  encoding: SignatureEncoding
}

export interface PayloadConfig {
  template: string
  format: PayloadFormat
  compression?: CompressionType
  encryption?: EncryptionConfig
  transformation: PayloadTransformation[]
  validation: PayloadValidation
}

export interface PayloadTransformation {
  type: TransformationType
  source: string
  target: string
  operation: TransformationOperation
  parameters: Record<string, any>
}

export interface PayloadValidation {
  schema?: string
  rules: ValidationRule[]
  required: string[]
  maxSize: number
}

export interface ValidationRule {
  field: string
  type: ValidationRuleType
  constraint: any
  message: string
}

export interface WebhookFilter {
  id: string
  name: string
  condition: FilterCondition
  enabled: boolean
}

export interface FilterCondition {
  field: string
  operator: FilterOperator
  value: any
  logicalOperator?: LogicalOperator
}

export interface WebhookSecurity {
  ipWhitelist: string[]
  userAgent?: string
  rateLimiting: RateLimit
  encryption: boolean
  verification: boolean
}

export interface WebhookStatistics {
  totalRequests: number
  successfulRequests: number
  failedRequests: number
  averageResponseTime: number
  lastSuccess?: string
  lastFailure?: string
  errorRate: number
  uptime: number
}

export interface IntegrationMetrics {
  requests: RequestMetrics
  performance: PerformanceMetrics
  reliability: ReliabilityMetrics
  usage: UsageMetrics
  errors: ErrorMetrics
  trends: MetricTrend[]
  lastUpdated: string
}

export interface RequestMetrics {
  total: number
  successful: number
  failed: number
  pending: number
  rate: number
  averageSize: number
  distribution: RequestDistribution
}

export interface RequestDistribution {
  byMethod: Record<HTTPMethod, number>
  byStatus: Record<number, number>
  byEndpoint: Record<string, number>
  byTime: TimeDistribution[]
}

export interface TimeDistribution {
  timestamp: string
  count: number
  success: number
  failure: number
}

export interface PerformanceMetrics {
  responseTime: ResponseTimeMetrics
  throughput: number
  latency: LatencyMetrics
  availability: number
  uptime: number
}

export interface ResponseTimeMetrics {
  average: number
  median: number
  p95: number
  p99: number
  minimum: number
  maximum: number
}

export interface LatencyMetrics {
  network: number
  processing: number
  queue: number
  total: number
}

export interface ReliabilityMetrics {
  successRate: number
  errorRate: number
  timeoutRate: number
  retryRate: number
  mtbf: number
  mttr: number
}

export interface UsageMetrics {
  activeConnections: number
  dataTransferred: number
  apiCalls: number
  uniqueUsers: number
  peakUsage: PeakUsage
  quotaUsage: QuotaUsage
}

export interface PeakUsage {
  value: number
  timestamp: string
  duration: number
}

export interface QuotaUsage {
  current: number
  limit: number
  remaining: number
  resetTime?: string
}

export interface ErrorMetrics {
  total: number
  byType: Record<string, number>
  byCode: Record<number, number>
  recent: ErrorSummary[]
  patterns: ErrorPattern[]
}

export interface ErrorSummary {
  timestamp: string
  type: string
  code: number
  message: string
  count: number
}

export interface ErrorPattern {
  pattern: string
  frequency: number
  impact: string
  recommendation: string
}

export interface MetricTrend {
  metric: string
  period: string
  values: TrendValue[]
  direction: TrendDirection
  change: number
  forecast: TrendForecast[]
}

export interface TrendValue {
  timestamp: string
  value: number
  change?: number
}

export interface TrendForecast {
  timestamp: string
  predicted: number
  confidence: number
  lower: number
  upper: number
}

export interface HealthCheck {
  status: HealthStatus
  lastCheck: string
  nextCheck: string
  checks: HealthCheckResult[]
  overall: HealthScore
  issues: HealthIssue[]
}

export interface HealthCheckResult {
  name: string
  status: HealthStatus
  message: string
  duration: number
  timestamp: string
  details: Record<string, any>
}

export interface HealthScore {
  current: number
  average: number
  trend: TrendDirection
  factors: ScoreFactor[]
}

export interface ScoreFactor {
  name: string
  weight: number
  score: number
  impact: string
}

export interface HealthIssue {
  id: string
  type: IssueType
  severity: IssueSeverity
  title: string
  description: string
  impact: string
  recommendation: string
  detectedAt: string
  resolvedAt?: string
}

export interface RetryPolicy {
  maxRetries: number
  backoffStrategy: BackoffStrategy
  initialDelay: number
  maxDelay: number
  multiplier: number
  jitter: boolean
  retryableErrors: string[]
  nonRetryableErrors: string[]
}

export interface RateLimit {
  requests: number
  period: number
  burst?: number
  concurrent?: number
  strategy: RateLimitStrategy
}

export interface IntegrationFeature {
  name: string
  enabled: boolean
  configuration: Record<string, any>
  dependencies: string[]
  version?: string
}

export interface EnvironmentConfig {
  name: string
  variables: Record<string, string>
  secrets: string[]
  region?: string
  zone?: string
}

export interface SecurityConfig {
  encryption: EncryptionConfig
  authentication: boolean
  authorization: boolean
  audit: boolean
  compliance: string[]
  policies: SecurityPolicy[]
}

export interface EncryptionConfig {
  enabled: boolean
  algorithm: string
  keySize: number
  mode: string
  padding?: string
}

export interface SecurityPolicy {
  id: string
  name: string
  type: PolicyType
  rules: PolicyRule[]
  enabled: boolean
}

export interface PolicyRule {
  condition: string
  action: PolicyAction
  parameters: Record<string, any>
}

export interface CIPipeline {
  id: string
  integrationId: string
  name: string
  provider: CIProvider
  repository: RepositoryInfo
  configuration: PipelineConfig
  triggers: PipelineTrigger[]
  stages: PipelineStage[]
  variables: PipelineVariable[]
  secrets: PipelineSecret[]
  status: PipelineStatus
  lastRun?: PipelineRun
  statistics: PipelineStatistics
  metadata: Record<string, any>
}

export interface RepositoryInfo {
  url: string
  branch: string
  commit?: string
  provider: string
  owner: string
  name: string
  private: boolean
}

export interface PipelineConfig {
  file: string
  syntax: string
  validation: boolean
  caching: CacheConfig
  artifacts: ArtifactConfig
  notifications: NotificationConfig[]
}

export interface CacheConfig {
  enabled: boolean
  key: string
  paths: string[]
  ttl: number
}

export interface ArtifactConfig {
  enabled: boolean
  paths: string[]
  retention: number
  compression: boolean
}

export interface NotificationConfig {
  type: NotificationType
  events: PipelineEvent[]
  recipients: string[]
  template?: string
  conditions: NotificationCondition[]
}

export interface NotificationCondition {
  field: string
  operator: string
  value: any
}

export interface PipelineTrigger {
  id: string
  type: TriggerType
  events: string[]
  conditions: TriggerCondition[]
  enabled: boolean
}

export interface TriggerCondition {
  type: ConditionType
  value: any
  operator: string
}

export interface PipelineStage {
  id: string
  name: string
  type: StageType
  dependencies: string[]
  jobs: PipelineJob[]
  conditions: StageCondition[]
  timeout: number
  retries: number
}

export interface StageCondition {
  type: string
  expression: string
}

export interface PipelineJob {
  id: string
  name: string
  type: JobType
  image?: string
  commands: string[]
  environment: Record<string, string>
  artifacts: string[]
  reports: JobReport[]
  timeout: number
  retries: number
}

export interface JobReport {
  type: ReportType
  path: string
  format: string
  public: boolean
}

export interface PipelineVariable {
  name: string
  value: string
  type: VariableType
  scope: VariableScope
  protected: boolean
  masked: boolean
}

export interface PipelineSecret {
  name: string
  value: string
  scope: VariableScope
  expiry?: string
  lastUsed?: string
}

export interface PipelineRun {
  id: string
  pipelineId: string
  number: number
  status: RunStatus
  trigger: RunTrigger
  startTime: string
  endTime?: string
  duration?: number
  stages: StageRun[]
  variables: Record<string, string>
  artifacts: RunArtifact[]
  logs: string[]
  metadata: Record<string, any>
}

export interface RunTrigger {
  type: TriggerType
  user?: string
  commit?: string
  branch?: string
  tag?: string
  event?: string
}

export interface StageRun {
  id: string
  stageId: string
  name: string
  status: RunStatus
  startTime: string
  endTime?: string
  duration?: number
  jobs: JobRun[]
  logs: string[]
}

export interface JobRun {
  id: string
  jobId: string
  name: string
  status: RunStatus
  startTime: string
  endTime?: string
  duration?: number
  exitCode?: number
  logs: string[]
  artifacts: string[]
  reports: string[]
}

export interface RunArtifact {
  name: string
  path: string
  size: number
  type: string
  url: string
  expiry?: string
}

export interface PipelineStatistics {
  totalRuns: number
  successfulRuns: number
  failedRuns: number
  averageDuration: number
  successRate: number
  trends: PipelineTrend[]
  performance: PipelinePerformance
}

export interface PipelineTrend {
  period: string
  runs: number
  success: number
  failure: number
  duration: number
}

export interface PipelinePerformance {
  buildTime: number
  testTime: number
  deployTime: number
  queueTime: number
  bottlenecks: string[]
}

export interface ExternalTool {
  id: string
  integrationId: string
  name: string
  type: ToolType
  provider: string
  configuration: ToolConfig
  authentication: AuthenticationConfig
  features: ToolFeature[]
  status: ToolStatus
  lastSync?: string
  syncFrequency: number
  mapping: FieldMapping[]
  filters: DataFilter[]
  metadata: Record<string, any>
}

export interface ToolConfig {
  endpoint: string
  version: string
  timeout: number
  batchSize: number
  syncMode: SyncMode
  conflictResolution: ConflictResolution
  customFields: CustomField[]
}

export interface ToolFeature {
  name: string
  enabled: boolean
  configuration: Record<string, any>
  permissions: string[]
}

export interface FieldMapping {
  source: string
  target: string
  transformation?: string
  validation?: string
  required: boolean
}

export interface DataFilter {
  field: string
  operator: string
  value: any
  enabled: boolean
}

export interface CustomField {
  name: string
  type: string
  required: boolean
  defaultValue?: any
  validation?: string
}

// Enums and Union Types
export type IntegrationType = 'ci-cd' | 'webhook' | 'api' | 'notification' | 'monitoring' | 'storage' | 'communication' | 'custom'
export type IntegrationProvider = 'github' | 'gitlab' | 'jenkins' | 'slack' | 'teams' | 'jira' | 'aws' | 'azure' | 'gcp' | 'custom'
export type IntegrationStatus = 'active' | 'inactive' | 'error' | 'configuring' | 'testing' | 'suspended'
export type IntegrationCategory = 'development' | 'testing' | 'deployment' | 'monitoring' | 'communication' | 'security' | 'analytics'
export type AuthenticationType = 'api-key' | 'oauth' | 'basic' | 'bearer' | 'certificate' | 'custom'
export type CertificateFormat = 'pem' | 'der' | 'p12' | 'jks'
export type WebhookType = 'incoming' | 'outgoing' | 'bidirectional'
export type WebhookDirection = 'inbound' | 'outbound'
export type HTTPMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD' | 'OPTIONS'
export type WebhookAuthType = 'none' | 'secret' | 'signature' | 'header' | 'query' | 'oauth'
export type SignatureAlgorithm = 'hmac-sha1' | 'hmac-sha256' | 'hmac-sha512' | 'rsa-sha256'
export type SignatureEncoding = 'hex' | 'base64'
export type PayloadFormat = 'json' | 'xml' | 'form' | 'text' | 'binary'
export type CompressionType = 'gzip' | 'deflate' | 'brotli'
export type TransformationType = 'map' | 'filter' | 'transform' | 'aggregate' | 'split'
export type TransformationOperation = 'copy' | 'rename' | 'format' | 'calculate' | 'lookup'
export type ValidationRuleType = 'required' | 'type' | 'format' | 'range' | 'pattern' | 'custom'
export type FilterOperator = 'equals' | 'not-equals' | 'contains' | 'not-contains' | 'greater' | 'less' | 'in' | 'not-in'
export type LogicalOperator = 'and' | 'or' | 'not'
export type WebhookStatus = 'active' | 'inactive' | 'error' | 'suspended'
export type HealthStatus = 'healthy' | 'warning' | 'critical' | 'unknown'
export type TrendDirection = 'up' | 'down' | 'stable' | 'volatile'
export type IssueType = 'connectivity' | 'authentication' | 'authorization' | 'performance' | 'configuration' | 'data'
export type IssueSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type BackoffStrategy = 'fixed' | 'linear' | 'exponential' | 'random'
export type RateLimitStrategy = 'fixed-window' | 'sliding-window' | 'token-bucket' | 'leaky-bucket'
export type PolicyType = 'access' | 'data' | 'security' | 'compliance'
export type PolicyAction = 'allow' | 'deny' | 'log' | 'alert' | 'transform'
export type CIProvider = 'github-actions' | 'gitlab-ci' | 'jenkins' | 'azure-devops' | 'circleci' | 'travis' | 'custom'
export type PipelineStatus = 'active' | 'inactive' | 'error' | 'draft'
export type PipelineEvent = 'started' | 'completed' | 'failed' | 'cancelled' | 'stage-completed' | 'job-failed'
export type TriggerType = 'push' | 'pull-request' | 'tag' | 'schedule' | 'manual' | 'webhook'
export type ConditionType = 'branch' | 'tag' | 'file' | 'variable' | 'expression'
export type StageType = 'build' | 'test' | 'deploy' | 'security' | 'quality' | 'custom'
export type JobType = 'script' | 'docker' | 'kubernetes' | 'aws' | 'azure' | 'gcp' | 'custom'
export type ReportType = 'junit' | 'coverage' | 'security' | 'quality' | 'performance' | 'custom'
export type VariableType = 'string' | 'number' | 'boolean' | 'secret'
export type VariableScope = 'global' | 'pipeline' | 'stage' | 'job'
export type RunStatus = 'pending' | 'running' | 'success' | 'failed' | 'cancelled' | 'skipped'
export type ToolType = 'issue-tracker' | 'chat' | 'email' | 'monitoring' | 'storage' | 'analytics' | 'custom'
export type ToolStatus = 'connected' | 'disconnected' | 'error' | 'syncing'
export type SyncMode = 'real-time' | 'batch' | 'scheduled' | 'manual'
export type ConflictResolution = 'source-wins' | 'target-wins' | 'merge' | 'manual'
export type NotificationType = 'email' | 'slack' | 'teams' | 'webhook' | 'sms' | 'push'

// Service Interfaces
export interface IntegrationService {
  getIntegrations(filters?: IntegrationFilters): Promise<Integration[]>
  getIntegration(integrationId: string): Promise<Integration>
  createIntegration(integration: Omit<Integration, 'id' | 'createdAt' | 'updatedAt'>): Promise<Integration>
  updateIntegration(integrationId: string, updates: Partial<Integration>): Promise<Integration>
  deleteIntegration(integrationId: string): Promise<void>
  testIntegration(integrationId: string): Promise<IntegrationTestResult>
  getIntegrationMetrics(integrationId: string, period?: string): Promise<IntegrationMetrics>
  getWebhooks(integrationId?: string): Promise<WebhookConfig[]>
  createWebhook(webhook: Omit<WebhookConfig, 'id' | 'statistics'>): Promise<WebhookConfig>
  updateWebhook(webhookId: string, updates: Partial<WebhookConfig>): Promise<WebhookConfig>
  deleteWebhook(webhookId: string): Promise<void>
  testWebhook(webhookId: string, payload?: any): Promise<WebhookTestResult>
  getCIPipelines(integrationId?: string): Promise<CIPipeline[]>
  createCIPipeline(pipeline: Omit<CIPipeline, 'id' | 'statistics'>): Promise<CIPipeline>
  updateCIPipeline(pipelineId: string, updates: Partial<CIPipeline>): Promise<CIPipeline>
  deleteCIPipeline(pipelineId: string): Promise<void>
  triggerPipeline(pipelineId: string, parameters?: Record<string, any>): Promise<PipelineRun>
  getPipelineRuns(pipelineId: string, limit?: number): Promise<PipelineRun[]>
  getPipelineRun(runId: string): Promise<PipelineRun>
  cancelPipelineRun(runId: string): Promise<void>
  getExternalTools(integrationId?: string): Promise<ExternalTool[]>
  createExternalTool(tool: Omit<ExternalTool, 'id' | 'lastSync'>): Promise<ExternalTool>
  updateExternalTool(toolId: string, updates: Partial<ExternalTool>): Promise<ExternalTool>
  deleteExternalTool(toolId: string): Promise<void>
  syncExternalTool(toolId: string): Promise<SyncResult>
  getIntegrationHealth(integrationId: string): Promise<HealthCheck>
  refreshAuthentication(integrationId: string): Promise<void>
}

export interface IntegrationFilters {
  type?: IntegrationType[]
  provider?: IntegrationProvider[]
  status?: IntegrationStatus[]
  category?: IntegrationCategory[]
  search?: string
  tags?: string[]
  createdBy?: string
  dateRange?: {
    start: string
    end: string
  }
}

export interface IntegrationTestResult {
  success: boolean
  responseTime: number
  status: number
  message: string
  details: Record<string, any>
  timestamp: string
}

export interface WebhookTestResult {
  success: boolean
  responseTime: number
  status: number
  response: any
  error?: string
  timestamp: string
}

export interface SyncResult {
  success: boolean
  recordsProcessed: number
  recordsCreated: number
  recordsUpdated: number
  recordsSkipped: number
  errors: SyncError[]
  duration: number
  timestamp: string
}

export interface SyncError {
  record: string
  error: string
  details: Record<string, any>
}

// Constants
export const INTEGRATION_TYPES: IntegrationType[] = ['ci-cd', 'webhook', 'api', 'notification', 'monitoring', 'storage', 'communication', 'custom']
export const INTEGRATION_PROVIDERS: IntegrationProvider[] = ['github', 'gitlab', 'jenkins', 'slack', 'teams', 'jira', 'aws', 'azure', 'gcp', 'custom']
export const INTEGRATION_STATUSES: IntegrationStatus[] = ['active', 'inactive', 'error', 'configuring', 'testing', 'suspended']
export const HTTP_METHODS: HTTPMethod[] = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']

export const DEFAULT_RETRY_POLICY: RetryPolicy = {
  maxRetries: 3,
  backoffStrategy: 'exponential',
  initialDelay: 1000,
  maxDelay: 30000,
  multiplier: 2,
  jitter: true,
  retryableErrors: ['timeout', 'network', '5xx'],
  nonRetryableErrors: ['4xx', 'authentication', 'authorization']
}

export const DEFAULT_RATE_LIMIT: RateLimit = {
  requests: 100,
  period: 60000,
  burst: 10,
  concurrent: 5,
  strategy: 'sliding-window'
}

export const STATUS_COLORS = {
  active: 'green',
  inactive: 'gray',
  error: 'red',
  configuring: 'blue',
  testing: 'orange',
  suspended: 'purple'
} as const

export const PROVIDER_ICONS = {
  github: 'github',
  gitlab: 'gitlab',
  jenkins: 'jenkins',
  slack: 'slack',
  teams: 'teams',
  jira: 'jira',
  aws: 'aws',
  azure: 'azure',
  gcp: 'gcp',
  custom: 'api'
} as const