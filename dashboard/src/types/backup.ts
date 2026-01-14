// Backup & Recovery Management Type Definitions

export interface BackupPolicy {
  id: string
  name: string
  description: string
  enabled: boolean
  type: BackupType
  scope: BackupScope
  schedule: BackupSchedule
  retention: RetentionPolicy
  storage: StorageConfiguration
  encryption: EncryptionConfiguration
  compression: CompressionConfiguration
  verification: VerificationConfiguration
  notification: NotificationConfiguration
  metadata: BackupMetadata
  tags: string[]
  createdAt: string
  updatedAt: string
  createdBy: string
  lastExecuted?: string
  nextExecution?: string
  status: PolicyStatus
}

export interface BackupScope {
  databases: DatabaseScope[]
  files: FileScope[]
  configurations: ConfigurationScope[]
  artifacts: ArtifactScope[]
  exclusions: ExclusionRule[]
}

export interface DatabaseScope {
  id: string
  name: string
  type: DatabaseType
  connection: string
  tables?: string[]
  schemas?: string[]
  includeData: boolean
  includeSchema: boolean
  includeIndexes: boolean
  includeTriggers: boolean
  includeViews: boolean
  includeProcedures: boolean
}

export interface FileScope {
  id: string
  name: string
  paths: string[]
  patterns: string[]
  recursive: boolean
  followSymlinks: boolean
  preservePermissions: boolean
  preserveTimestamps: boolean
  includeHidden: boolean
}

export interface ConfigurationScope {
  id: string
  name: string
  type: ConfigurationType
  source: string
  format: ConfigurationFormat
  includeSecrets: boolean
  maskSensitive: boolean
}

export interface ArtifactScope {
  id: string
  name: string
  type: ArtifactType
  repository: string
  versions: VersionScope
  includeMetadata: boolean
  includeDependencies: boolean
}

export interface VersionScope {
  strategy: VersionStrategy
  count?: number
  pattern?: string
  tags?: string[]
  branches?: string[]
  dateRange?: {
    start: string
    end: string
  }
}

export interface ExclusionRule {
  id: string
  type: ExclusionType
  pattern: string
  reason: string
  enabled: boolean
}

export interface BackupSchedule {
  type: ScheduleType
  frequency: ScheduleFrequency
  time?: string
  timezone: string
  days?: string[]
  dates?: number[]
  interval?: number
  cron?: string
  enabled: boolean
  maxDuration?: number
  concurrency?: number
  priority: SchedulePriority
}

export interface RetentionPolicy {
  type: RetentionType
  duration: string
  count?: number
  rules: RetentionRule[]
  archival: ArchivalPolicy
  deletion: DeletionPolicy
}

export interface RetentionRule {
  id: string
  name: string
  condition: RetentionCondition
  action: RetentionAction
  duration: string
  enabled: boolean
}

export interface RetentionCondition {
  type: ConditionType
  field: string
  operator: ComparisonOperator
  value: any
}

export interface ArchivalPolicy {
  enabled: boolean
  threshold: string
  storage: StorageConfiguration
  compression: CompressionConfiguration
  encryption: EncryptionConfiguration
}

export interface DeletionPolicy {
  enabled: boolean
  threshold: string
  confirmation: boolean
  audit: boolean
  secure: boolean
}

export interface StorageConfiguration {
  type: StorageType
  location: string
  credentials: StorageCredentials
  options: StorageOptions
  redundancy: RedundancyConfiguration
  performance: PerformanceConfiguration
}

export interface StorageCredentials {
  accessKey?: string
  secretKey?: string
  token?: string
  region?: string
  endpoint?: string
  bucket?: string
  container?: string
  path?: string
  custom?: Record<string, any>
}

export interface StorageOptions {
  multipart: boolean
  chunkSize: number
  parallelUploads: number
  retryAttempts: number
  timeout: number
  checksums: boolean
  metadata: boolean
}

export interface RedundancyConfiguration {
  type: RedundancyType
  replicas: number
  locations: string[]
  crossRegion: boolean
  validation: boolean
}

export interface PerformanceConfiguration {
  bandwidth: number
  iops: number
  latency: number
  throughput: number
  optimization: PerformanceOptimization
}

export interface PerformanceOptimization {
  deduplication: boolean
  compression: boolean
  caching: boolean
  prefetching: boolean
  parallelization: boolean
}

export interface EncryptionConfiguration {
  enabled: boolean
  algorithm: EncryptionAlgorithm
  keySize: number
  mode: EncryptionMode
  keyManagement: KeyManagement
  inTransit: boolean
  atRest: boolean
}

export interface KeyManagement {
  type: KeyManagementType
  provider: string
  keyId?: string
  rotation: KeyRotation
  escrow: boolean
}

export interface KeyRotation {
  enabled: boolean
  frequency: string
  automatic: boolean
  notification: boolean
}

export interface CompressionConfiguration {
  enabled: boolean
  algorithm: CompressionAlgorithm
  level: number
  blockSize: number
  dictionary?: string
  adaptive: boolean
}

export interface VerificationConfiguration {
  enabled: boolean
  type: VerificationType
  frequency: VerificationFrequency
  scope: VerificationScope
  tolerance: VerificationTolerance
  reporting: VerificationReporting
}

export interface VerificationTolerance {
  checksumMismatch: number
  sizeDifference: number
  timeDifference: number
  missingFiles: number
}

export interface VerificationReporting {
  onSuccess: boolean
  onFailure: boolean
  detailed: boolean
  recipients: string[]
  channels: string[]
}

export interface NotificationConfiguration {
  enabled: boolean
  events: NotificationEvent[]
  recipients: NotificationRecipient[]
  channels: NotificationChannel[]
  templates: NotificationTemplate[]
  escalation: NotificationEscalation
}

export interface NotificationRecipient {
  id: string
  type: RecipientType
  address: string
  name?: string
  role?: string
  preferences: RecipientPreferences
}

export interface RecipientPreferences {
  events: NotificationEvent[]
  channels: NotificationChannelType[]
  frequency: NotificationFrequency
  format: NotificationFormat
  quietHours: QuietHours
}

export interface QuietHours {
  enabled: boolean
  start: string
  end: string
  timezone: string
  days: string[]
}

export interface NotificationChannel {
  type: NotificationChannelType
  configuration: ChannelConfiguration
  enabled: boolean
  priority: number
}

export interface ChannelConfiguration {
  endpoint?: string
  credentials?: ChannelCredentials
  template?: string
  format?: NotificationFormat
  retries?: number
  timeout?: number
}

export interface ChannelCredentials {
  apiKey?: string
  token?: string
  webhook?: string
  custom?: Record<string, any>
}

export interface NotificationTemplate {
  event: NotificationEvent
  channel: NotificationChannelType
  subject: string
  body: string
  format: NotificationFormat
  variables: TemplateVariable[]
}

export interface TemplateVariable {
  name: string
  type: VariableType
  description: string
  required: boolean
  defaultValue?: any
}

export interface NotificationEscalation {
  enabled: boolean
  levels: EscalationLevel[]
  timeout: number
}

export interface EscalationLevel {
  level: number
  delay: number
  recipients: string[]
  channels: NotificationChannelType[]
  conditions: EscalationCondition[]
}

export interface EscalationCondition {
  type: string
  value: any
  operator: string
}

export interface BackupMetadata {
  version: string
  source: string
  environment: string
  application: string
  component: string
  owner: string
  contact: string
  criticality: CriticalityLevel
  compliance: string[]
  customFields: Record<string, any>
}

export interface BackupJob {
  id: string
  policyId: string
  policyName: string
  type: BackupType
  status: JobStatus
  phase: JobPhase
  progress: JobProgress
  startTime: string
  endTime?: string
  duration?: number
  size: BackupSize
  statistics: BackupStatistics
  errors: BackupError[]
  warnings: BackupWarning[]
  logs: BackupLog[]
  artifacts: BackupArtifact[]
  metadata: JobMetadata
  triggeredBy: string
  triggerType: TriggerType
}

export interface JobProgress {
  percentage: number
  currentPhase: JobPhase
  phases: PhaseProgress[]
  estimatedCompletion?: string
  throughput: ThroughputMetrics
}

export interface PhaseProgress {
  phase: JobPhase
  status: PhaseStatus
  percentage: number
  startTime?: string
  endTime?: string
  duration?: number
  size?: number
  items?: number
}

export interface ThroughputMetrics {
  current: number
  average: number
  peak: number
  unit: ThroughputUnit
}

export interface BackupSize {
  original: number
  compressed: number
  encrypted: number
  stored: number
  ratio: number
  unit: SizeUnit
}

export interface BackupStatistics {
  files: FileStatistics
  databases: DatabaseStatistics
  performance: PerformanceStatistics
  verification: VerificationStatistics
}

export interface FileStatistics {
  total: number
  processed: number
  skipped: number
  failed: number
  size: number
  types: FileTypeStatistics[]
}

export interface FileTypeStatistics {
  type: string
  count: number
  size: number
  percentage: number
}

export interface DatabaseStatistics {
  tables: number
  rows: number
  size: number
  indexes: number
  views: number
  procedures: number
}

export interface PerformanceStatistics {
  throughput: number
  iops: number
  latency: number
  cpu: number
  memory: number
  network: number
  storage: number
}

export interface VerificationStatistics {
  checksums: ChecksumStatistics
  integrity: IntegrityStatistics
  completeness: CompletenessStatistics
}

export interface ChecksumStatistics {
  calculated: number
  verified: number
  mismatched: number
  algorithm: string
}

export interface IntegrityStatistics {
  files: number
  corrupted: number
  recovered: number
  unrecoverable: number
}

export interface CompletenessStatistics {
  expected: number
  found: number
  missing: number
  extra: number
}

export interface BackupError {
  id: string
  type: ErrorType
  severity: ErrorSeverity
  code: string
  message: string
  details: string
  source: string
  timestamp: string
  retryable: boolean
  retryCount: number
}

export interface BackupWarning {
  id: string
  type: WarningType
  message: string
  details: string
  source: string
  timestamp: string
  impact: ImpactLevel
}

export interface BackupLog {
  id: string
  level: LogLevel
  message: string
  details?: string
  source: string
  timestamp: string
  metadata: Record<string, any>
}

export interface BackupArtifact {
  id: string
  name: string
  type: ArtifactType
  path: string
  size: number
  checksum: string
  algorithm: string
  compressed: boolean
  encrypted: boolean
  metadata: ArtifactMetadata
}

export interface ArtifactMetadata {
  created: string
  modified: string
  permissions: string
  owner: string
  group: string
  mimeType?: string
  encoding?: string
  customFields: Record<string, any>
}

export interface JobMetadata {
  version: string
  agent: string
  environment: string
  resources: ResourceUsage
  configuration: JobConfiguration
  dependencies: string[]
}

export interface ResourceUsage {
  cpu: number
  memory: number
  storage: number
  network: number
  duration: number
}

export interface JobConfiguration {
  parallelism: number
  timeout: number
  retries: number
  bufferSize: number
  chunkSize: number
  compression: boolean
  encryption: boolean
  verification: boolean
}

export interface RecoveryPoint {
  id: string
  name: string
  description?: string
  backupJobId: string
  policyId: string
  type: RecoveryPointType
  status: RecoveryPointStatus
  createdAt: string
  expiresAt?: string
  size: BackupSize
  location: string
  checksum: string
  metadata: RecoveryPointMetadata
  dependencies: string[]
  tags: string[]
  verified: boolean
  verifiedAt?: string
  accessible: boolean
  lastAccessed?: string
}

export interface RecoveryPointMetadata {
  source: RecoveryPointSource
  scope: BackupScope
  statistics: BackupStatistics
  environment: string
  version: string
  application: string
  component: string
  snapshot: SnapshotInfo
}

export interface RecoveryPointSource {
  type: SourceType
  identifier: string
  version: string
  timestamp: string
  location: string
}

export interface SnapshotInfo {
  id: string
  timestamp: string
  consistent: boolean
  applicationConsistent: boolean
  crashConsistent: boolean
  dependencies: string[]
}

export interface RecoveryOperation {
  id: string
  name: string
  description?: string
  type: RecoveryType
  status: RecoveryStatus
  phase: RecoveryPhase
  progress: RecoveryProgress
  recoveryPointId: string
  target: RecoveryTarget
  options: RecoveryOptions
  validation: RecoveryValidation
  startTime: string
  endTime?: string
  duration?: number
  statistics: RecoveryStatistics
  errors: RecoveryError[]
  warnings: RecoveryWarning[]
  logs: RecoveryLog[]
  metadata: RecoveryMetadata
  triggeredBy: string
  approvedBy?: string
}

export interface RecoveryProgress {
  percentage: number
  currentPhase: RecoveryPhase
  phases: RecoveryPhaseProgress[]
  estimatedCompletion?: string
  throughput: ThroughputMetrics
}

export interface RecoveryPhaseProgress {
  phase: RecoveryPhase
  status: PhaseStatus
  percentage: number
  startTime?: string
  endTime?: string
  duration?: number
  items?: number
}

export interface RecoveryTarget {
  type: TargetType
  location: string
  credentials?: TargetCredentials
  configuration: TargetConfiguration
  validation: TargetValidation
}

export interface TargetCredentials {
  username?: string
  password?: string
  keyFile?: string
  token?: string
  custom?: Record<string, any>
}

export interface TargetConfiguration {
  overwrite: boolean
  merge: boolean
  preserve: PreservationOptions
  transformation: TransformationOptions
  validation: ValidationOptions
}

export interface PreservationOptions {
  permissions: boolean
  timestamps: boolean
  ownership: boolean
  attributes: boolean
  links: boolean
}

export interface TransformationOptions {
  renaming: RenamingRule[]
  filtering: FilteringRule[]
  mapping: MappingRule[]
}

export interface RenamingRule {
  pattern: string
  replacement: string
  scope: RenameScope
}

export interface FilteringRule {
  type: FilterType
  pattern: string
  action: FilterAction
}

export interface MappingRule {
  source: string
  target: string
  type: MappingType
}

export interface ValidationOptions {
  checksum: boolean
  size: boolean
  structure: boolean
  content: boolean
  permissions: boolean
}

export interface TargetValidation {
  preRecovery: ValidationCheck[]
  postRecovery: ValidationCheck[]
  rollback: RollbackConfiguration
}

export interface ValidationCheck {
  type: ValidationCheckType
  condition: string
  action: ValidationAction
  timeout: number
}

export interface RollbackConfiguration {
  enabled: boolean
  automatic: boolean
  conditions: RollbackCondition[]
  retention: string
}

export interface RollbackCondition {
  type: string
  threshold: any
  action: RollbackAction
}

export interface RecoveryOptions {
  pointInTime?: string
  partial: boolean
  scope: RecoveryScope
  priority: RecoveryPriority
  verification: boolean
  testing: boolean
  rollback: boolean
  notification: boolean
}

export interface RecoveryScope {
  databases?: string[]
  tables?: string[]
  files?: string[]
  configurations?: string[]
  timeRange?: {
    start: string
    end: string
  }
}

export interface RecoveryValidation {
  preRecovery: ValidationResult[]
  postRecovery: ValidationResult[]
  integrity: IntegrityValidation
  functionality: FunctionalityValidation
}

export interface ValidationResult {
  check: string
  status: ValidationStatus
  message: string
  details?: string
  timestamp: string
}

export interface IntegrityValidation {
  checksums: ChecksumValidation[]
  structure: StructureValidation[]
  consistency: ConsistencyValidation[]
}

export interface ChecksumValidation {
  file: string
  expected: string
  actual: string
  match: boolean
  algorithm: string
}

export interface StructureValidation {
  component: string
  expected: any
  actual: any
  match: boolean
  differences: string[]
}

export interface ConsistencyValidation {
  type: string
  status: ValidationStatus
  issues: ConsistencyIssue[]
}

export interface ConsistencyIssue {
  type: string
  description: string
  severity: IssueSeverity
  resolution?: string
}

export interface FunctionalityValidation {
  tests: FunctionalityTest[]
  overall: ValidationStatus
  coverage: number
}

export interface FunctionalityTest {
  name: string
  type: TestType
  status: TestStatus
  duration: number
  message?: string
  details?: string
}

export interface RecoveryStatistics {
  files: FileRecoveryStatistics
  databases: DatabaseRecoveryStatistics
  performance: PerformanceStatistics
  validation: ValidationStatistics
}

export interface FileRecoveryStatistics {
  total: number
  recovered: number
  failed: number
  skipped: number
  size: number
  throughput: number
}

export interface DatabaseRecoveryStatistics {
  tables: number
  rows: number
  indexes: number
  views: number
  procedures: number
  size: number
  duration: number
}

export interface ValidationStatistics {
  checks: number
  passed: number
  failed: number
  warnings: number
  coverage: number
}

export interface RecoveryError {
  id: string
  type: ErrorType
  severity: ErrorSeverity
  code: string
  message: string
  details: string
  source: string
  timestamp: string
  recoverable: boolean
  resolution?: string
}

export interface RecoveryWarning {
  id: string
  type: WarningType
  message: string
  details: string
  source: string
  timestamp: string
  impact: ImpactLevel
  recommendation?: string
}

export interface RecoveryLog {
  id: string
  level: LogLevel
  message: string
  details?: string
  source: string
  timestamp: string
  metadata: Record<string, any>
}

export interface RecoveryMetadata {
  version: string
  agent: string
  environment: string
  resources: ResourceUsage
  configuration: RecoveryConfiguration
  approvals: ApprovalRecord[]
}

export interface RecoveryConfiguration {
  parallelism: number
  timeout: number
  retries: number
  bufferSize: number
  verification: boolean
  testing: boolean
  rollback: boolean
}

export interface ApprovalRecord {
  approver: string
  timestamp: string
  decision: ApprovalDecision
  reason?: string
  conditions?: string[]
}

export interface DisasterRecoveryPlan {
  id: string
  name: string
  description: string
  type: DRPlanType
  scope: DRScope
  objectives: DRObjectives
  procedures: DRProcedure[]
  resources: DRResource[]
  dependencies: DRDependency[]
  testing: DRTesting
  communication: DRCommunication
  roles: DRRole[]
  escalation: DREscalation
  documentation: DRDocumentation
  status: DRPlanStatus
  version: string
  createdAt: string
  updatedAt: string
  createdBy: string
  approvedBy?: string
  approvedAt?: string
  lastTested?: string
  nextTest?: string
}

export interface DRScope {
  systems: string[]
  applications: string[]
  data: string[]
  locations: string[]
  criticality: CriticalityLevel[]
  dependencies: string[]
}

export interface DRObjectives {
  rto: number
  rpo: number
  availability: number
  dataLoss: number
  downtime: number
  recovery: RecoveryObjective[]
}

export interface RecoveryObjective {
  component: string
  rto: number
  rpo: number
  priority: RecoveryPriority
  dependencies: string[]
}

export interface DRProcedure {
  id: string
  name: string
  description: string
  type: ProcedureType
  phase: DRPhase
  steps: DRStep[]
  prerequisites: string[]
  dependencies: string[]
  resources: string[]
  duration: number
  criticality: CriticalityLevel
  automation: AutomationLevel
  testing: boolean
  documentation: string[]
}

export interface DRStep {
  id: string
  order: number
  name: string
  description: string
  type: StepType
  action: string
  parameters: Record<string, any>
  expectedResult: string
  verification: string[]
  rollback: string[]
  timeout: number
  retries: number
  dependencies: string[]
  responsible: string[]
  automated: boolean
  critical: boolean
}

export interface DRResource {
  id: string
  name: string
  type: ResourceType
  location: string
  capacity: ResourceCapacity
  availability: ResourceAvailability
  cost: ResourceCost
  dependencies: string[]
  alternatives: string[]
  contact: string
}

export interface ResourceCapacity {
  cpu: number
  memory: number
  storage: number
  network: number
  concurrent: number
}

export interface ResourceAvailability {
  sla: number
  uptime: number
  maintenance: MaintenanceWindow[]
  restrictions: string[]
}

export interface MaintenanceWindow {
  start: string
  end: string
  frequency: string
  impact: ImpactLevel
  notification: number
}

export interface ResourceCost {
  setup: number
  monthly: number
  usage: number
  currency: string
  billing: BillingModel
}

export interface DRDependency {
  id: string
  name: string
  type: DependencyType
  source: string
  target: string
  relationship: DependencyRelationship
  criticality: CriticalityLevel
  impact: DependencyImpact
  mitigation: string[]
}

export interface DependencyImpact {
  availability: number
  performance: number
  functionality: string[]
  recovery: number
}

export interface DRTesting {
  frequency: TestingFrequency
  types: DRTestType[]
  scenarios: DRScenario[]
  schedule: TestingSchedule
  reporting: TestingReporting
  validation: TestingValidation
}

export interface DRScenario {
  id: string
  name: string
  description: string
  type: ScenarioType
  scope: string[]
  objectives: string[]
  procedures: string[]
  success: SuccessCriteria[]
  duration: number
  resources: string[]
  risks: string[]
}

export interface SuccessCriteria {
  metric: string
  target: number
  tolerance: number
  measurement: string
}

export interface TestingSchedule {
  planned: PlannedTest[]
  adhoc: boolean
  notification: number
  approval: boolean
}

export interface PlannedTest {
  id: string
  name: string
  type: DRTestType
  date: string
  duration: number
  scope: string[]
  responsible: string[]
  approved: boolean
}

export interface TestingReporting {
  template: string
  recipients: string[]
  frequency: ReportingFrequency
  metrics: string[]
  analysis: boolean
}

export interface TestingValidation {
  criteria: ValidationCriteria[]
  automation: boolean
  documentation: boolean
  approval: boolean
}

export interface ValidationCriteria {
  metric: string
  threshold: number
  operator: string
  critical: boolean
}

export interface DRCommunication {
  contacts: DRContact[]
  channels: CommunicationChannel[]
  templates: CommunicationTemplate[]
  escalation: CommunicationEscalation
  external: ExternalCommunication
}

export interface DRContact {
  id: string
  name: string
  role: string
  primary: boolean
  phone: string
  email: string
  alternate: string
  availability: string
  expertise: string[]
}

export interface CommunicationChannel {
  type: ChannelType
  configuration: ChannelConfiguration
  priority: number
  backup: boolean
  testing: boolean
}

export interface CommunicationTemplate {
  event: DREvent
  channel: ChannelType
  template: string
  variables: string[]
  approval: boolean
}

export interface CommunicationEscalation {
  levels: CommunicationLevel[]
  timeout: number
  automatic: boolean
}

export interface CommunicationLevel {
  level: number
  delay: number
  contacts: string[]
  channels: ChannelType[]
  message: string
}

export interface ExternalCommunication {
  customers: boolean
  partners: boolean
  vendors: boolean
  regulators: boolean
  media: boolean
  templates: ExternalTemplate[]
}

export interface ExternalTemplate {
  audience: string
  template: string
  approval: boolean
  timing: string
}

export interface DRRole {
  id: string
  name: string
  description: string
  responsibilities: string[]
  authorities: string[]
  skills: string[]
  training: string[]
  contacts: string[]
  backup: string[]
  escalation: string[]
}

export interface DREscalation {
  triggers: EscalationTrigger[]
  levels: DREscalationLevel[]
  timeout: number
  automatic: boolean
  notification: boolean
}

export interface EscalationTrigger {
  condition: string
  threshold: any
  duration: number
  automatic: boolean
}

export interface DREscalationLevel {
  level: number
  delay: number
  authority: string[]
  actions: string[]
  notification: string[]
}

export interface DRDocumentation {
  procedures: DocumentationItem[]
  contacts: DocumentationItem[]
  systems: DocumentationItem[]
  dependencies: DocumentationItem[]
  testing: DocumentationItem[]
  training: DocumentationItem[]
}

export interface DocumentationItem {
  name: string
  type: DocumentationType
  location: string
  version: string
  lastUpdated: string
  owner: string
  access: AccessLevel[]
}

// Enums and Union Types
export type BackupType = 'full' | 'incremental' | 'differential' | 'snapshot' | 'continuous'
export type PolicyStatus = 'active' | 'inactive' | 'suspended' | 'error' | 'draft'
export type DatabaseType = 'mysql' | 'postgresql' | 'mongodb' | 'redis' | 'elasticsearch' | 'cassandra' | 'oracle' | 'sqlserver'
export type ConfigurationType = 'application' | 'system' | 'network' | 'security' | 'database' | 'custom'
export type ConfigurationFormat = 'json' | 'yaml' | 'xml' | 'ini' | 'properties' | 'toml'
export type ArtifactType = 'code' | 'binary' | 'image' | 'document' | 'data' | 'configuration' | 'log'
export type VersionStrategy = 'all' | 'latest' | 'count' | 'pattern' | 'tag' | 'branch' | 'date'
export type ExclusionType = 'path' | 'pattern' | 'extension' | 'size' | 'age' | 'attribute'
export type ScheduleType = 'fixed' | 'interval' | 'cron' | 'event' | 'manual'
export type ScheduleFrequency = 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'custom'
export type SchedulePriority = 'low' | 'normal' | 'high' | 'critical'
export type RetentionType = 'time' | 'count' | 'size' | 'custom'
export type RetentionAction = 'archive' | 'delete' | 'compress' | 'move'
export type ConditionType = 'age' | 'size' | 'count' | 'tag' | 'status' | 'custom'
export type ComparisonOperator = 'equals' | 'not-equals' | 'greater' | 'less' | 'greater-equal' | 'less-equal' | 'contains'
export type StorageType = 'local' | 's3' | 'azure' | 'gcp' | 'nfs' | 'smb' | 'ftp' | 'sftp' | 'tape'
export type RedundancyType = 'none' | 'mirror' | 'stripe' | 'parity' | 'erasure' | 'replication'
export type EncryptionAlgorithm = 'aes-128' | 'aes-256' | 'chacha20' | 'rsa' | 'ecc'
export type EncryptionMode = 'cbc' | 'gcm' | 'ctr' | 'ecb' | 'cfb' | 'ofb'
export type KeyManagementType = 'local' | 'kms' | 'hsm' | 'vault' | 'external'
export type CompressionAlgorithm = 'gzip' | 'bzip2' | 'lz4' | 'zstd' | 'xz' | 'lzma'
export type VerificationType = 'checksum' | 'hash' | 'signature' | 'full' | 'sample'
export type VerificationFrequency = 'always' | 'daily' | 'weekly' | 'monthly' | 'never'
export type VerificationScope = 'all' | 'sample' | 'critical' | 'recent' | 'random'
export type NotificationEvent = 'started' | 'completed' | 'failed' | 'warning' | 'verified' | 'expired'
export type RecipientType = 'user' | 'group' | 'role' | 'email' | 'webhook'
export type NotificationChannelType = 'email' | 'slack' | 'teams' | 'webhook' | 'sms' | 'push'
export type NotificationFrequency = 'immediate' | 'batched' | 'digest' | 'summary'
export type NotificationFormat = 'text' | 'html' | 'json' | 'xml'
export type VariableType = 'string' | 'number' | 'boolean' | 'date' | 'array' | 'object'
export type CriticalityLevel = 'low' | 'medium' | 'high' | 'critical'
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused'
export type JobPhase = 'preparation' | 'backup' | 'compression' | 'encryption' | 'transfer' | 'verification' | 'cleanup'
export type PhaseStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
export type TriggerType = 'scheduled' | 'manual' | 'event' | 'api' | 'webhook'
export type ThroughputUnit = 'bps' | 'kbps' | 'mbps' | 'gbps' | 'files/s' | 'records/s'
export type SizeUnit = 'bytes' | 'kb' | 'mb' | 'gb' | 'tb' | 'pb'
export type ErrorType = 'system' | 'network' | 'storage' | 'permission' | 'configuration' | 'data' | 'timeout'
export type ErrorSeverity = 'info' | 'warning' | 'error' | 'critical' | 'fatal'
export type WarningType = 'performance' | 'capacity' | 'configuration' | 'security' | 'compatibility'
export type ImpactLevel = 'low' | 'medium' | 'high' | 'critical'
export type LogLevel = 'debug' | 'info' | 'warning' | 'error' | 'fatal'
export type RecoveryPointType = 'full' | 'incremental' | 'differential' | 'snapshot'
export type RecoveryPointStatus = 'available' | 'archived' | 'expired' | 'corrupted' | 'restoring'
export type SourceType = 'database' | 'filesystem' | 'application' | 'vm' | 'container' | 'cloud'
export type RecoveryType = 'full' | 'partial' | 'point-in-time' | 'bare-metal' | 'vm' | 'file-level'
export type RecoveryStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'validating'
export type RecoveryPhase = 'preparation' | 'validation' | 'recovery' | 'verification' | 'testing' | 'cleanup'
export type TargetType = 'original' | 'alternate' | 'test' | 'development' | 'cloud' | 'vm'
export type RenameScope = 'file' | 'directory' | 'path' | 'extension'
export type FilterType = 'include' | 'exclude' | 'transform'
export type FilterAction = 'allow' | 'deny' | 'modify'
export type MappingType = 'path' | 'name' | 'attribute' | 'content'
export type ValidationCheckType = 'space' | 'permission' | 'connectivity' | 'dependency' | 'integrity'
export type ValidationAction = 'continue' | 'warn' | 'fail' | 'retry'
export type RollbackAction = 'automatic' | 'manual' | 'notify' | 'abort'
export type RecoveryPriority = 'low' | 'normal' | 'high' | 'critical'
export type ValidationStatus = 'passed' | 'failed' | 'warning' | 'skipped' | 'pending'
export type IssueSeverity = 'low' | 'medium' | 'high' | 'critical'
export type TestType = 'connectivity' | 'functionality' | 'performance' | 'integrity' | 'security'
export type TestStatus = 'passed' | 'failed' | 'warning' | 'skipped' | 'error'
export type ApprovalDecision = 'approved' | 'rejected' | 'conditional' | 'deferred'
export type DRPlanType = 'hot-site' | 'warm-site' | 'cold-site' | 'cloud' | 'hybrid' | 'mobile'
export type DRPlanStatus = 'active' | 'inactive' | 'draft' | 'testing' | 'updating' | 'archived'
export type ProcedureType = 'manual' | 'automated' | 'hybrid' | 'decision' | 'notification'
export type DRPhase = 'assessment' | 'activation' | 'recovery' | 'restoration' | 'testing' | 'deactivation'
export type StepType = 'action' | 'decision' | 'verification' | 'notification' | 'wait'
export type ResourceType = 'compute' | 'storage' | 'network' | 'application' | 'data' | 'personnel'
export type BillingModel = 'fixed' | 'usage' | 'tiered' | 'spot' | 'reserved'
export type DependencyType = 'technical' | 'business' | 'operational' | 'regulatory' | 'contractual'
export type DependencyRelationship = 'depends-on' | 'provides-to' | 'shares-with' | 'conflicts-with'
export type TestingFrequency = 'monthly' | 'quarterly' | 'semi-annually' | 'annually' | 'ad-hoc'
export type DRTestType = 'tabletop' | 'walkthrough' | 'simulation' | 'parallel' | 'full-interruption'
export type ScenarioType = 'natural-disaster' | 'cyber-attack' | 'hardware-failure' | 'software-failure' | 'human-error'
export type ReportingFrequency = 'immediate' | 'daily' | 'weekly' | 'monthly' | 'quarterly'
export type ChannelType = 'phone' | 'email' | 'sms' | 'radio' | 'satellite' | 'internet'
export type DREvent = 'activation' | 'escalation' | 'recovery' | 'restoration' | 'deactivation' | 'test'
export type DocumentationType = 'procedure' | 'contact' | 'diagram' | 'checklist' | 'template' | 'training'
export type AccessLevel = 'public' | 'internal' | 'restricted' | 'confidential' | 'secret'
export type AutomationLevel = 'none' | 'partial' | 'full' | 'intelligent'

// Service Interfaces
export interface BackupService {
  getBackupPolicies(filters?: BackupFilters): Promise<BackupPolicy[]>
  getBackupPolicy(policyId: string): Promise<BackupPolicy>
  createBackupPolicy(policy: Omit<BackupPolicy, 'id' | 'createdAt' | 'updatedAt'>): Promise<BackupPolicy>
  updateBackupPolicy(policyId: string, updates: Partial<BackupPolicy>): Promise<BackupPolicy>
  deleteBackupPolicy(policyId: string): Promise<void>
  enableBackupPolicy(policyId: string): Promise<void>
  disableBackupPolicy(policyId: string): Promise<void>
  testBackupPolicy(policyId: string): Promise<BackupTestResult>
  executeBackupPolicy(policyId: string): Promise<BackupJob>
  getBackupJobs(filters?: JobFilters): Promise<BackupJob[]>
  getBackupJob(jobId: string): Promise<BackupJob>
  cancelBackupJob(jobId: string): Promise<void>
  pauseBackupJob(jobId: string): Promise<void>
  resumeBackupJob(jobId: string): Promise<void>
  retryBackupJob(jobId: string): Promise<BackupJob>
  getRecoveryPoints(filters?: RecoveryPointFilters): Promise<RecoveryPoint[]>
  getRecoveryPoint(recoveryPointId: string): Promise<RecoveryPoint>
  deleteRecoveryPoint(recoveryPointId: string): Promise<void>
  verifyRecoveryPoint(recoveryPointId: string): Promise<VerificationResult>
  createRecoveryOperation(operation: Omit<RecoveryOperation, 'id' | 'startTime'>): Promise<RecoveryOperation>
  getRecoveryOperations(filters?: RecoveryFilters): Promise<RecoveryOperation[]>
  getRecoveryOperation(operationId: string): Promise<RecoveryOperation>
  cancelRecoveryOperation(operationId: string): Promise<void>
  pauseRecoveryOperation(operationId: string): Promise<void>
  resumeRecoveryOperation(operationId: string): Promise<void>
  approveRecoveryOperation(operationId: string, approverId: string): Promise<void>
  testRecoveryOperation(operationId: string): Promise<RecoveryTestResult>
  getDisasterRecoveryPlans(): Promise<DisasterRecoveryPlan[]>
  getDisasterRecoveryPlan(planId: string): Promise<DisasterRecoveryPlan>
  createDisasterRecoveryPlan(plan: Omit<DisasterRecoveryPlan, 'id' | 'createdAt' | 'updatedAt'>): Promise<DisasterRecoveryPlan>
  updateDisasterRecoveryPlan(planId: string, updates: Partial<DisasterRecoveryPlan>): Promise<DisasterRecoveryPlan>
  deleteDisasterRecoveryPlan(planId: string): Promise<void>
  activateDisasterRecoveryPlan(planId: string): Promise<DRActivationResult>
  testDisasterRecoveryPlan(planId: string, testType: DRTestType): Promise<DRTestResult>
  getBackupStatistics(filters?: StatisticsFilters): Promise<BackupStatistics>
  getStorageUtilization(): Promise<StorageUtilization>
  getComplianceReport(framework?: string): Promise<ComplianceReport>
  exportBackupData(filters?: ExportFilters, format?: ExportFormat): Promise<string>
  importBackupConfiguration(data: any, format: ImportFormat): Promise<ImportResult>
  validateBackupConfiguration(configuration: any): Promise<ValidationResult>
  getBackupHealth(): Promise<BackupHealthStatus>
  getBackupAlerts(filters?: AlertFilters): Promise<BackupAlert[]>
  acknowledgeBackupAlert(alertId: string): Promise<void>
  resolveBackupAlert(alertId: string): Promise<void>
}

export interface BackupFilters {
  type?: BackupType[]
  status?: PolicyStatus[]
  enabled?: boolean
  tags?: string[]
  createdBy?: string
  dateRange?: {
    start: string
    end: string
  }
  search?: string
}

export interface JobFilters {
  policyId?: string
  status?: JobStatus[]
  type?: BackupType[]
  triggeredBy?: string
  dateRange?: {
    start: string
    end: string
  }
  size?: {
    min: number
    max: number
  }
}

export interface RecoveryPointFilters {
  policyId?: string
  type?: RecoveryPointType[]
  status?: RecoveryPointStatus[]
  verified?: boolean
  accessible?: boolean
  dateRange?: {
    start: string
    end: string
  }
  size?: {
    min: number
    max: number
  }
  tags?: string[]
}

export interface RecoveryFilters {
  type?: RecoveryType[]
  status?: RecoveryStatus[]
  target?: TargetType[]
  priority?: RecoveryPriority[]
  triggeredBy?: string
  approvedBy?: string
  dateRange?: {
    start: string
    end: string
  }
}

export interface StatisticsFilters {
  period?: string
  policies?: string[]
  types?: BackupType[]
  dateRange?: {
    start: string
    end: string
  }
}

export interface ExportFilters {
  policies?: string[]
  jobs?: string[]
  recoveryPoints?: string[]
  dateRange?: {
    start: string
    end: string
  }
}

export interface AlertFilters {
  severity?: ErrorSeverity[]
  type?: string[]
  status?: string[]
  dateRange?: {
    start: string
    end: string
  }
}

export interface BackupTestResult {
  success: boolean
  duration: number
  size: BackupSize
  errors: BackupError[]
  warnings: BackupWarning[]
  performance: PerformanceStatistics
  recommendations: string[]
}

export interface VerificationResult {
  success: boolean
  checksums: ChecksumValidation[]
  integrity: IntegrityValidation[]
  completeness: CompletenessStatistics
  errors: BackupError[]
  warnings: BackupWarning[]
}

export interface RecoveryTestResult {
  success: boolean
  duration: number
  validation: RecoveryValidation
  functionality: FunctionalityValidation
  performance: PerformanceStatistics
  errors: RecoveryError[]
  warnings: RecoveryWarning[]
  recommendations: string[]
}

export interface DRActivationResult {
  success: boolean
  activatedAt: string
  procedures: ProcedureResult[]
  resources: ResourceActivation[]
  communications: CommunicationResult[]
  issues: DRIssue[]
}

export interface ProcedureResult {
  procedureId: string
  status: ExecutionStatus
  duration: number
  steps: StepResult[]
  errors: string[]
}

export interface StepResult {
  stepId: string
  status: ExecutionStatus
  duration: number
  result: string
  error?: string
}

export interface ResourceActivation {
  resourceId: string
  status: ActivationStatus
  duration: number
  issues: string[]
}

export interface CommunicationResult {
  channel: ChannelType
  recipients: number
  delivered: number
  failed: number
  errors: string[]
}

export interface DRIssue {
  type: string
  severity: IssueSeverity
  description: string
  impact: string
  resolution: string
  status: IssueStatus
}

export interface DRTestResult {
  success: boolean
  testType: DRTestType
  duration: number
  scenarios: ScenarioResult[]
  objectives: ObjectiveResult[]
  issues: DRIssue[]
  recommendations: string[]
  report: string
}

export interface ScenarioResult {
  scenarioId: string
  status: TestStatus
  duration: number
  objectives: ObjectiveResult[]
  issues: string[]
}

export interface ObjectiveResult {
  objective: string
  target: number
  actual: number
  achieved: boolean
  gap: number
}

export interface StorageUtilization {
  total: number
  used: number
  available: number
  utilization: number
  byType: Record<StorageType, StorageTypeUtilization>
  byPolicy: PolicyUtilization[]
  trends: UtilizationTrend[]
  forecasts: UtilizationForecast[]
}

export interface StorageTypeUtilization {
  total: number
  used: number
  available: number
  utilization: number
  cost: number
}

export interface PolicyUtilization {
  policyId: string
  policyName: string
  size: number
  percentage: number
  trend: TrendDirection
}

export interface UtilizationTrend {
  date: string
  total: number
  used: number
  utilization: number
}

export interface UtilizationForecast {
  date: string
  predicted: number
  confidence: number
  capacity: number
}

export interface ComplianceReport {
  framework: string
  score: number
  controls: ComplianceControl[]
  violations: ComplianceViolation[]
  recommendations: ComplianceRecommendation[]
  lastAssessment: string
  nextAssessment: string
}

export interface ComplianceControl {
  id: string
  name: string
  status: ComplianceStatus
  score: number
  evidence: string[]
  gaps: string[]
}

export interface ComplianceViolation {
  id: string
  control: string
  severity: ViolationSeverity
  description: string
  remediation: string
  dueDate: string
}

export interface ComplianceRecommendation {
  id: string
  priority: RecommendationPriority
  description: string
  effort: EffortLevel
  impact: ImpactLevel
  timeline: string
}

export interface ImportResult {
  success: boolean
  imported: number
  skipped: number
  errors: ImportError[]
  warnings: string[]
}

export interface ImportError {
  item: string
  error: string
  line?: number
}

export interface ValidationResult {
  valid: boolean
  errors: ValidationError[]
  warnings: string[]
  recommendations: string[]
}

export interface ValidationError {
  field: string
  message: string
  code: string
  severity: ErrorSeverity
}

export interface BackupHealthStatus {
  overall: HealthStatus
  policies: PolicyHealth[]
  storage: StorageHealth
  performance: PerformanceHealth
  compliance: ComplianceHealth
  issues: HealthIssue[]
  recommendations: HealthRecommendation[]
}

export interface PolicyHealth {
  policyId: string
  policyName: string
  status: HealthStatus
  lastBackup: string
  successRate: number
  issues: string[]
}

export interface StorageHealth {
  status: HealthStatus
  utilization: number
  availability: number
  performance: number
  issues: string[]
}

export interface PerformanceHealth {
  status: HealthStatus
  throughput: number
  latency: number
  reliability: number
  issues: string[]
}

export interface ComplianceHealth {
  status: HealthStatus
  score: number
  violations: number
  issues: string[]
}

export interface HealthIssue {
  type: string
  severity: IssueSeverity
  description: string
  impact: string
  recommendation: string
}

export interface HealthRecommendation {
  priority: RecommendationPriority
  description: string
  effort: EffortLevel
  impact: ImpactLevel
  timeline: string
}

export interface BackupAlert {
  id: string
  type: AlertType
  severity: AlertSeverity
  title: string
  description: string
  source: string
  status: AlertStatus
  createdAt: string
  acknowledgedAt?: string
  resolvedAt?: string
  metadata: Record<string, any>
}

export type ComplianceStatus = 'compliant' | 'non-compliant' | 'partial' | 'not-applicable'
export type ViolationSeverity = 'low' | 'medium' | 'high' | 'critical'
export type RecommendationPriority = 'low' | 'medium' | 'high' | 'critical'
export type EffortLevel = 'low' | 'medium' | 'high' | 'very-high'
export type HealthStatus = 'healthy' | 'warning' | 'critical' | 'unknown'
export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
export type ActivationStatus = 'pending' | 'activating' | 'active' | 'failed' | 'deactivated'
export type IssueStatus = 'open' | 'investigating' | 'resolved' | 'closed'
export type TrendDirection = 'up' | 'down' | 'stable' | 'volatile'
export type AlertType = 'policy' | 'job' | 'storage' | 'performance' | 'security' | 'compliance'
export type AlertSeverity = 'info' | 'warning' | 'error' | 'critical'
export type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'suppressed'
export type ExportFormat = 'json' | 'csv' | 'xml' | 'yaml'
export type ImportFormat = 'json' | 'csv' | 'xml' | 'yaml'

// Constants
export const BACKUP_TYPES: BackupType[] = ['full', 'incremental', 'differential', 'snapshot', 'continuous']
export const STORAGE_TYPES: StorageType[] = ['local', 's3', 'azure', 'gcp', 'nfs', 'smb', 'ftp', 'sftp', 'tape']
export const SCHEDULE_FREQUENCIES: ScheduleFrequency[] = ['hourly', 'daily', 'weekly', 'monthly', 'yearly', 'custom']
export const JOB_STATUSES: JobStatus[] = ['pending', 'running', 'completed', 'failed', 'cancelled', 'paused']
export const RECOVERY_TYPES: RecoveryType[] = ['full', 'partial', 'point-in-time', 'bare-metal', 'vm', 'file-level']

export const STATUS_COLORS = {
  active: 'green',
  inactive: 'gray',
  suspended: 'orange',
  error: 'red',
  draft: 'blue'
} as const

export const SEVERITY_COLORS = {
  info: '#1890ff',
  warning: '#faad14',
  error: '#ff7a45',
  critical: '#f5222d',
  fatal: '#a8071a'
} as const

export const BACKUP_TYPE_ICONS = {
  full: 'database',
  incremental: 'plus-circle',
  differential: 'delta',
  snapshot: 'camera',
  continuous: 'refresh-cw'
} as const

export const DEFAULT_RETENTION_POLICY: RetentionPolicy = {
  type: 'time',
  duration: '30d',
  rules: [],
  archival: {
    enabled: false,
    threshold: '90d',
    storage: {} as StorageConfiguration,
    compression: {} as CompressionConfiguration,
    encryption: {} as EncryptionConfiguration
  },
  deletion: {
    enabled: true,
    threshold: '365d',
    confirmation: true,
    audit: true,
    secure: true
  }
}

export const DEFAULT_BACKUP_SCHEDULE: BackupSchedule = {
  type: 'fixed',
  frequency: 'daily',
  time: '02:00',
  timezone: 'UTC',
  enabled: true,
  priority: 'normal'
}