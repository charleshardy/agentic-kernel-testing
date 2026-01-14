// Notification Center Type Definitions

export interface Notification {
  id: string
  type: NotificationType
  category: NotificationCategory
  priority: NotificationPriority
  severity: NotificationSeverity
  title: string
  message: string
  summary?: string
  details?: string
  source: NotificationSource
  sourceId?: string
  targetPath?: string
  targetResource?: string
  recipients: NotificationRecipient[]
  channels: NotificationChannel[]
  status: NotificationStatus
  readBy: string[]
  acknowledgedBy: string[]
  actions: NotificationAction[]
  attachments: NotificationAttachment[]
  metadata: Record<string, any>
  tags: string[]
  createdAt: string
  updatedAt: string
  scheduledAt?: string
  sentAt?: string
  deliveredAt?: string
  readAt?: string
  acknowledgedAt?: string
  expiresAt?: string
}

export interface NotificationRecipient {
  id: string
  type: RecipientType
  address: string
  name?: string
  preferences: RecipientPreferences
  status: DeliveryStatus
  deliveredAt?: string
  readAt?: string
  acknowledgedAt?: string
  error?: string
}

export interface RecipientPreferences {
  channels: NotificationChannelType[]
  frequency: NotificationFrequency
  quietHours: QuietHours
  categories: CategoryPreference[]
  priorities: PriorityPreference[]
  digest: DigestPreference
}

export interface QuietHours {
  enabled: boolean
  start: string
  end: string
  timezone: string
  days: string[]
  exceptions: string[]
}

export interface CategoryPreference {
  category: NotificationCategory
  enabled: boolean
  channels: NotificationChannelType[]
  threshold: NotificationPriority
}

export interface PriorityPreference {
  priority: NotificationPriority
  enabled: boolean
  channels: NotificationChannelType[]
  immediate: boolean
}

export interface DigestPreference {
  enabled: boolean
  frequency: DigestFrequency
  time: string
  timezone: string
  categories: NotificationCategory[]
  maxItems: number
}

export interface NotificationChannel {
  type: NotificationChannelType
  configuration: ChannelConfiguration
  status: ChannelStatus
  lastUsed?: string
  statistics: ChannelStatistics
  enabled: boolean
}

export interface ChannelConfiguration {
  endpoint?: string
  credentials?: ChannelCredentials
  template?: string
  format?: MessageFormat
  headers?: Record<string, string>
  parameters?: Record<string, any>
  retryPolicy?: RetryPolicy
  rateLimit?: RateLimit
}

export interface ChannelCredentials {
  apiKey?: string
  token?: string
  username?: string
  password?: string
  webhook?: string
  custom?: Record<string, any>
}

export interface ChannelStatistics {
  totalSent: number
  totalDelivered: number
  totalFailed: number
  averageDeliveryTime: number
  successRate: number
  lastSuccess?: string
  lastFailure?: string
  errorRate: number
}

export interface NotificationAction {
  id: string
  type: ActionType
  label: string
  description?: string
  icon?: string
  url?: string
  method?: string
  payload?: Record<string, any>
  confirmation?: boolean
  permissions?: string[]
  enabled: boolean
  order: number
}

export interface NotificationAttachment {
  id: string
  name: string
  type: AttachmentType
  size: number
  url: string
  mimeType: string
  description?: string
  thumbnail?: string
}

export interface AlertPolicy {
  id: string
  name: string
  description: string
  enabled: boolean
  conditions: AlertCondition[]
  actions: PolicyAction[]
  escalation: EscalationPolicy
  suppression: SuppressionPolicy
  schedule: AlertSchedule
  recipients: string[]
  channels: NotificationChannelType[]
  priority: NotificationPriority
  category: NotificationCategory
  tags: string[]
  metadata: Record<string, any>
  createdAt: string
  updatedAt: string
  createdBy: string
}

export interface AlertCondition {
  id: string
  type: ConditionType
  field: string
  operator: ComparisonOperator
  value: any
  threshold?: number
  duration?: number
  aggregation?: AggregationType
  logicalOperator?: LogicalOperator
  enabled: boolean
}

export interface PolicyAction {
  id: string
  type: PolicyActionType
  parameters: Record<string, any>
  delay?: number
  conditions?: ActionCondition[]
  enabled: boolean
  order: number
}

export interface ActionCondition {
  field: string
  operator: string
  value: any
}

export interface EscalationPolicy {
  enabled: boolean
  levels: EscalationLevel[]
  timeout: number
  maxLevels: number
  stopOnAcknowledge: boolean
}

export interface EscalationLevel {
  level: number
  delay: number
  recipients: string[]
  channels: NotificationChannelType[]
  actions: PolicyAction[]
  conditions?: EscalationCondition[]
}

export interface EscalationCondition {
  type: string
  value: any
  operator: string
}

export interface SuppressionPolicy {
  enabled: boolean
  rules: SuppressionRule[]
  duration: number
  conditions: SuppressionCondition[]
}

export interface SuppressionRule {
  id: string
  type: SuppressionType
  pattern: string
  duration: number
  conditions: string[]
  enabled: boolean
}

export interface SuppressionCondition {
  field: string
  operator: string
  value: any
  duration?: number
}

export interface AlertSchedule {
  enabled: boolean
  timezone: string
  windows: ScheduleWindow[]
  holidays: Holiday[]
  overrides: ScheduleOverride[]
}

export interface ScheduleWindow {
  id: string
  name: string
  days: string[]
  startTime: string
  endTime: string
  enabled: boolean
}

export interface Holiday {
  date: string
  name: string
  recurring: boolean
  enabled: boolean
}

export interface ScheduleOverride {
  id: string
  startTime: string
  endTime: string
  enabled: boolean
  reason: string
  createdBy: string
}

export interface NotificationTemplate {
  id: string
  name: string
  description: string
  type: TemplateType
  category: NotificationCategory
  channels: NotificationChannelType[]
  subject: string
  body: string
  format: MessageFormat
  variables: TemplateVariable[]
  conditions: TemplateCondition[]
  localization: TemplateLocalization[]
  version: string
  status: TemplateStatus
  createdAt: string
  updatedAt: string
  createdBy: string
  tags: string[]
  metadata: Record<string, any>
}

export interface TemplateVariable {
  name: string
  type: VariableType
  required: boolean
  defaultValue?: any
  description: string
  validation?: VariableValidation
  examples: any[]
}

export interface VariableValidation {
  pattern?: string
  minLength?: number
  maxLength?: number
  minValue?: number
  maxValue?: number
  allowedValues?: any[]
}

export interface TemplateCondition {
  field: string
  operator: string
  value: any
  template: string
}

export interface TemplateLocalization {
  locale: string
  subject: string
  body: string
  variables: Record<string, string>
}

export interface NotificationDigest {
  id: string
  recipientId: string
  type: DigestType
  period: DigestPeriod
  notifications: NotificationSummary[]
  summary: DigestSummary
  template: string
  status: DigestStatus
  generatedAt: string
  sentAt?: string
  deliveredAt?: string
  metadata: Record<string, any>
}

export interface NotificationSummary {
  id: string
  type: NotificationType
  category: NotificationCategory
  priority: NotificationPriority
  title: string
  summary: string
  count: number
  latestAt: string
  source: string
}

export interface DigestSummary {
  totalNotifications: number
  byCategory: Record<NotificationCategory, number>
  byPriority: Record<NotificationPriority, number>
  bySource: Record<string, number>
  period: {
    start: string
    end: string
  }
}

export interface NotificationRule {
  id: string
  name: string
  description: string
  enabled: boolean
  conditions: RuleCondition[]
  actions: RuleAction[]
  filters: NotificationFilter[]
  transformations: NotificationTransformation[]
  priority: number
  order: number
  createdAt: string
  updatedAt: string
  createdBy: string
  tags: string[]
  metadata: Record<string, any>
}

export interface RuleCondition {
  field: string
  operator: string
  value: any
  logicalOperator?: LogicalOperator
}

export interface RuleAction {
  type: RuleActionType
  parameters: Record<string, any>
  enabled: boolean
  order: number
}

export interface NotificationFilter {
  field: string
  operator: FilterOperator
  value: any
  enabled: boolean
}

export interface NotificationTransformation {
  type: TransformationType
  field: string
  operation: TransformationOperation
  parameters: Record<string, any>
  enabled: boolean
}

export interface NotificationStatistics {
  total: number
  byType: Record<NotificationType, number>
  byCategory: Record<NotificationCategory, number>
  byPriority: Record<NotificationPriority, number>
  byStatus: Record<NotificationStatus, number>
  byChannel: Record<NotificationChannelType, number>
  trends: StatisticTrend[]
  performance: NotificationPerformance
  engagement: EngagementMetrics
}

export interface StatisticTrend {
  period: string
  total: number
  sent: number
  delivered: number
  read: number
  acknowledged: number
  failed: number
}

export interface NotificationPerformance {
  averageDeliveryTime: number
  deliveryRate: number
  readRate: number
  acknowledgmentRate: number
  errorRate: number
  channelPerformance: Record<NotificationChannelType, ChannelPerformance>
}

export interface ChannelPerformance {
  deliveryTime: number
  successRate: number
  errorRate: number
  cost: number
  reliability: number
}

export interface EngagementMetrics {
  openRate: number
  clickRate: number
  actionRate: number
  unsubscribeRate: number
  bounceRate: number
  engagementScore: number
}

export interface NotificationQueue {
  id: string
  name: string
  type: QueueType
  priority: QueuePriority
  status: QueueStatus
  size: number
  maxSize: number
  processing: number
  failed: number
  retries: number
  configuration: QueueConfiguration
  statistics: QueueStatistics
  health: QueueHealth
}

export interface QueueConfiguration {
  maxRetries: number
  retryDelay: number
  batchSize: number
  timeout: number
  deadLetterQueue: boolean
  persistence: boolean
  ordering: QueueOrdering
}

export interface QueueStatistics {
  totalProcessed: number
  totalFailed: number
  averageProcessingTime: number
  throughput: number
  errorRate: number
  backlog: number
}

export interface QueueHealth {
  status: HealthStatus
  issues: QueueIssue[]
  lastCheck: string
  metrics: QueueMetrics
}

export interface QueueIssue {
  type: string
  severity: string
  description: string
  impact: string
  recommendation: string
}

export interface QueueMetrics {
  latency: number
  throughput: number
  errorRate: number
  backlogSize: number
  processingTime: number
}

// Enums and Union Types
export type NotificationType = 'alert' | 'info' | 'warning' | 'success' | 'error' | 'system' | 'user' | 'digest'
export type NotificationCategory = 'security' | 'performance' | 'system' | 'test' | 'deployment' | 'integration' | 'user' | 'compliance' | 'maintenance'
export type NotificationPriority = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type NotificationSeverity = 'critical' | 'major' | 'minor' | 'warning' | 'info'
export type NotificationSource = 'system' | 'user' | 'integration' | 'api' | 'webhook' | 'scheduled' | 'manual'
export type NotificationStatus = 'pending' | 'sent' | 'delivered' | 'read' | 'acknowledged' | 'failed' | 'expired' | 'cancelled'
export type RecipientType = 'user' | 'group' | 'role' | 'email' | 'webhook' | 'external'
export type DeliveryStatus = 'pending' | 'sent' | 'delivered' | 'failed' | 'bounced' | 'unsubscribed'
export type NotificationChannelType = 'email' | 'slack' | 'teams' | 'webhook' | 'sms' | 'push' | 'in-app' | 'desktop'
export type NotificationFrequency = 'immediate' | 'batched' | 'digest' | 'scheduled' | 'manual'
export type DigestFrequency = 'hourly' | 'daily' | 'weekly' | 'monthly'
export type ChannelStatus = 'active' | 'inactive' | 'error' | 'rate-limited' | 'suspended'
export type MessageFormat = 'text' | 'html' | 'markdown' | 'json' | 'xml'
export type ActionType = 'acknowledge' | 'resolve' | 'escalate' | 'snooze' | 'assign' | 'comment' | 'link' | 'custom'
export type AttachmentType = 'image' | 'document' | 'video' | 'audio' | 'archive' | 'data'
export type ConditionType = 'field' | 'threshold' | 'pattern' | 'time' | 'frequency' | 'custom'
export type ComparisonOperator = 'equals' | 'not-equals' | 'greater' | 'less' | 'greater-equal' | 'less-equal' | 'contains' | 'not-contains' | 'matches' | 'not-matches'
export type AggregationType = 'count' | 'sum' | 'average' | 'min' | 'max' | 'distinct'
export type LogicalOperator = 'and' | 'or' | 'not'
export type PolicyActionType = 'notify' | 'escalate' | 'suppress' | 'transform' | 'route' | 'log' | 'webhook'
export type SuppressionType = 'duplicate' | 'flood' | 'maintenance' | 'scheduled' | 'custom'
export type TemplateType = 'email' | 'slack' | 'teams' | 'sms' | 'push' | 'webhook' | 'in-app'
export type TemplateStatus = 'active' | 'draft' | 'deprecated' | 'archived'
export type VariableType = 'string' | 'number' | 'boolean' | 'date' | 'array' | 'object'
export type DigestType = 'summary' | 'detailed' | 'custom'
export type DigestPeriod = 'hour' | 'day' | 'week' | 'month'
export type DigestStatus = 'pending' | 'generated' | 'sent' | 'delivered' | 'failed'
export type RuleActionType = 'route' | 'transform' | 'filter' | 'enrich' | 'suppress' | 'escalate'
export type FilterOperator = 'equals' | 'not-equals' | 'contains' | 'not-contains' | 'in' | 'not-in' | 'matches'
export type TransformationType = 'field' | 'content' | 'format' | 'priority' | 'category'
export type TransformationOperation = 'set' | 'append' | 'prepend' | 'replace' | 'remove' | 'format'
export type QueueType = 'priority' | 'fifo' | 'lifo' | 'round-robin' | 'weighted'
export type QueuePriority = 'critical' | 'high' | 'normal' | 'low'
export type QueueStatus = 'active' | 'paused' | 'stopped' | 'error'
export type QueueOrdering = 'strict' | 'relaxed' | 'none'
export type HealthStatus = 'healthy' | 'warning' | 'critical' | 'unknown'

// Service Interfaces
export interface NotificationService {
  getNotifications(filters?: NotificationFilters): Promise<Notification[]>
  getNotification(notificationId: string): Promise<Notification>
  createNotification(notification: Omit<Notification, 'id' | 'createdAt' | 'updatedAt'>): Promise<Notification>
  updateNotification(notificationId: string, updates: Partial<Notification>): Promise<Notification>
  deleteNotification(notificationId: string): Promise<void>
  markAsRead(notificationId: string, userId: string): Promise<void>
  markAsAcknowledged(notificationId: string, userId: string): Promise<void>
  bulkMarkAsRead(notificationIds: string[], userId: string): Promise<void>
  bulkMarkAsAcknowledged(notificationIds: string[], userId: string): Promise<void>
  getUnreadCount(userId: string): Promise<number>
  getNotificationsByUser(userId: string, filters?: NotificationFilters): Promise<Notification[]>
  sendNotification(notification: Notification): Promise<DeliveryResult>
  resendNotification(notificationId: string): Promise<DeliveryResult>
  cancelNotification(notificationId: string): Promise<void>
  getAlertPolicies(): Promise<AlertPolicy[]>
  createAlertPolicy(policy: Omit<AlertPolicy, 'id' | 'createdAt' | 'updatedAt'>): Promise<AlertPolicy>
  updateAlertPolicy(policyId: string, updates: Partial<AlertPolicy>): Promise<AlertPolicy>
  deleteAlertPolicy(policyId: string): Promise<void>
  testAlertPolicy(policyId: string, testData: any): Promise<PolicyTestResult>
  getNotificationTemplates(): Promise<NotificationTemplate[]>
  createNotificationTemplate(template: Omit<NotificationTemplate, 'id' | 'createdAt' | 'updatedAt'>): Promise<NotificationTemplate>
  updateNotificationTemplate(templateId: string, updates: Partial<NotificationTemplate>): Promise<NotificationTemplate>
  deleteNotificationTemplate(templateId: string): Promise<void>
  renderTemplate(templateId: string, variables: Record<string, any>): Promise<RenderedTemplate>
  getNotificationRules(): Promise<NotificationRule[]>
  createNotificationRule(rule: Omit<NotificationRule, 'id' | 'createdAt' | 'updatedAt'>): Promise<NotificationRule>
  updateNotificationRule(ruleId: string, updates: Partial<NotificationRule>): Promise<NotificationRule>
  deleteNotificationRule(ruleId: string): Promise<void>
  getNotificationStatistics(filters?: StatisticsFilters): Promise<NotificationStatistics>
  getNotificationDigests(userId: string): Promise<NotificationDigest[]>
  generateDigest(userId: string, type: DigestType, period: DigestPeriod): Promise<NotificationDigest>
  getNotificationQueues(): Promise<NotificationQueue[]>
  getQueueHealth(queueId: string): Promise<QueueHealth>
  pauseQueue(queueId: string): Promise<void>
  resumeQueue(queueId: string): Promise<void>
  purgeQueue(queueId: string): Promise<void>
  getUserPreferences(userId: string): Promise<RecipientPreferences>
  updateUserPreferences(userId: string, preferences: Partial<RecipientPreferences>): Promise<RecipientPreferences>
  subscribe(userId: string, callback: (notification: Notification) => void): () => void
  unsubscribe(userId: string, subscriptionId: string): void
}

export interface NotificationFilters {
  type?: NotificationType[]
  category?: NotificationCategory[]
  priority?: NotificationPriority[]
  status?: NotificationStatus[]
  source?: NotificationSource[]
  recipient?: string
  channel?: NotificationChannelType[]
  read?: boolean
  acknowledged?: boolean
  dateRange?: {
    start: string
    end: string
  }
  search?: string
  tags?: string[]
}

export interface DeliveryResult {
  success: boolean
  channels: ChannelDeliveryResult[]
  totalRecipients: number
  successfulDeliveries: number
  failedDeliveries: number
  errors: DeliveryError[]
  timestamp: string
}

export interface ChannelDeliveryResult {
  channel: NotificationChannelType
  success: boolean
  recipients: number
  delivered: number
  failed: number
  responseTime: number
  error?: string
}

export interface DeliveryError {
  channel: NotificationChannelType
  recipient: string
  error: string
  code?: string
  retryable: boolean
}

export interface PolicyTestResult {
  matched: boolean
  conditions: ConditionTestResult[]
  actions: ActionTestResult[]
  notifications: Notification[]
  errors: string[]
}

export interface ConditionTestResult {
  condition: AlertCondition
  matched: boolean
  value: any
  expected: any
  error?: string
}

export interface ActionTestResult {
  action: PolicyAction
  executed: boolean
  result: any
  error?: string
}

export interface RenderedTemplate {
  subject: string
  body: string
  format: MessageFormat
  variables: Record<string, any>
  errors: string[]
}

export interface StatisticsFilters {
  period?: string
  categories?: NotificationCategory[]
  channels?: NotificationChannelType[]
  users?: string[]
  dateRange?: {
    start: string
    end: string
  }
}

export interface RetryPolicy {
  maxRetries: number
  backoffStrategy: string
  initialDelay: number
  maxDelay: number
  multiplier: number
}

export interface RateLimit {
  requests: number
  period: number
  burst?: number
}

// Constants
export const NOTIFICATION_TYPES: NotificationType[] = ['alert', 'info', 'warning', 'success', 'error', 'system', 'user', 'digest']
export const NOTIFICATION_CATEGORIES: NotificationCategory[] = ['security', 'performance', 'system', 'test', 'deployment', 'integration', 'user', 'compliance', 'maintenance']
export const NOTIFICATION_PRIORITIES: NotificationPriority[] = ['critical', 'high', 'medium', 'low', 'info']
export const NOTIFICATION_CHANNELS: NotificationChannelType[] = ['email', 'slack', 'teams', 'webhook', 'sms', 'push', 'in-app', 'desktop']

export const PRIORITY_COLORS = {
  critical: '#ff4d4f',
  high: '#ff7a45',
  medium: '#ffa940',
  low: '#52c41a',
  info: '#1890ff'
} as const

export const STATUS_COLORS = {
  pending: 'orange',
  sent: 'blue',
  delivered: 'green',
  read: 'green',
  acknowledged: 'green',
  failed: 'red',
  expired: 'gray',
  cancelled: 'gray'
} as const

export const CHANNEL_ICONS = {
  email: 'mail',
  slack: 'slack',
  teams: 'teams',
  webhook: 'api',
  sms: 'message',
  push: 'notification',
  'in-app': 'bell',
  desktop: 'desktop'
} as const

export const DEFAULT_RETRY_POLICY: RetryPolicy = {
  maxRetries: 3,
  backoffStrategy: 'exponential',
  initialDelay: 1000,
  maxDelay: 30000,
  multiplier: 2
}

export const DEFAULT_RATE_LIMIT: RateLimit = {
  requests: 100,
  period: 60000,
  burst: 10
}

export const DEFAULT_QUIET_HOURS: QuietHours = {
  enabled: false,
  start: '22:00',
  end: '08:00',
  timezone: 'UTC',
  days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
  exceptions: []
}