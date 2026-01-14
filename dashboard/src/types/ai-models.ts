// AI/ML Model Management Type Definitions

export interface AIModel {
  id: string
  name: string
  displayName: string
  provider: AIProvider
  version: string
  status: ModelStatus
  type: ModelType
  capabilities: ModelCapability[]
  metrics: ModelMetrics
  configuration: ModelConfiguration
  fallbackModel?: string
  createdAt: string
  updatedAt: string
  createdBy: string
  tags: string[]
  metadata: Record<string, any>
}

export interface ModelMetrics {
  responseTime: number
  averageResponseTime: number
  accuracy: number
  tokenUsage: TokenUsage
  costPerRequest: number
  requestCount: number
  successRate: number
  errorRate: number
  availability: number
  throughput: number
  latency: LatencyMetrics
  performance: PerformanceMetrics
  lastUpdated: string
}

export interface TokenUsage {
  totalTokens: number
  inputTokens: number
  outputTokens: number
  averageTokensPerRequest: number
  tokenCostPerRequest: number
  dailyUsage: number
  monthlyUsage: number
  usageLimit?: number
}

export interface LatencyMetrics {
  p50: number
  p95: number
  p99: number
  min: number
  max: number
  average: number
}

export interface PerformanceMetrics {
  requestsPerSecond: number
  concurrentRequests: number
  queueLength: number
  processingTime: number
  networkLatency: number
  errorCount: number
  timeoutCount: number
}

export interface ModelConfiguration {
  endpoint: string
  apiKey: string
  maxTokens: number
  temperature: number
  topP?: number
  topK?: number
  frequencyPenalty?: number
  presencePenalty?: number
  rateLimit: RateLimit
  timeout: number
  retryPolicy: RetryPolicy
  headers?: Record<string, string>
  parameters: Record<string, any>
}

export interface RateLimit {
  requestsPerMinute: number
  requestsPerHour: number
  requestsPerDay: number
  tokensPerMinute: number
  tokensPerHour: number
  tokensPerDay: number
  concurrentRequests: number
}

export interface RetryPolicy {
  maxRetries: number
  backoffStrategy: BackoffStrategy
  retryableErrors: string[]
  timeout: number
}

export interface PromptTemplate {
  id: string
  name: string
  description: string
  category: PromptCategory
  template: string
  variables: TemplateVariable[]
  version: string
  status: TemplateStatus
  modelCompatibility: string[]
  examples: PromptExample[]
  metrics: TemplateMetrics
  createdBy: string
  createdAt: string
  updatedAt: string
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

export interface PromptExample {
  id: string
  name: string
  description: string
  input: Record<string, any>
  expectedOutput: string
  actualOutput?: string
  score?: number
  createdAt: string
}

export interface TemplateMetrics {
  usageCount: number
  successRate: number
  averageScore: number
  averageResponseTime: number
  lastUsed: string
  popularVariables: string[]
}

export interface ModelFallback {
  id: string
  primaryModelId: string
  fallbackModelId: string
  conditions: FallbackCondition[]
  enabled: boolean
  priority: number
  createdAt: string
  updatedAt: string
}

export interface FallbackCondition {
  type: FallbackTrigger
  threshold?: number
  duration?: number
  errorTypes?: string[]
  enabled: boolean
}

export interface ModelAlert {
  id: string
  modelId: string
  type: AlertType
  severity: AlertSeverity
  title: string
  description: string
  conditions: AlertCondition[]
  actions: AlertAction[]
  status: AlertStatus
  triggeredAt?: string
  resolvedAt?: string
  acknowledgedAt?: string
  metadata: Record<string, any>
}

export interface AlertCondition {
  metric: string
  operator: ComparisonOperator
  threshold: number
  duration: number
  enabled: boolean
}

export interface AlertAction {
  type: AlertActionType
  parameters: Record<string, any>
  enabled: boolean
  order: number
}

export interface ModelUsageReport {
  modelId: string
  period: ReportPeriod
  summary: UsageSummary
  trends: UsageTrend[]
  costs: CostBreakdown
  recommendations: ModelRecommendation[]
  generatedAt: string
}

export interface UsageSummary {
  totalRequests: number
  successfulRequests: number
  failedRequests: number
  averageResponseTime: number
  totalTokens: number
  totalCost: number
  peakUsage: number
  uniqueUsers: number
}

export interface UsageTrend {
  timestamp: string
  requests: number
  tokens: number
  cost: number
  responseTime: number
  errorRate: number
}

export interface CostBreakdown {
  totalCost: number
  inputTokenCost: number
  outputTokenCost: number
  requestCost: number
  infraCost: number
  costPerRequest: number
  costPerToken: number
  projectedMonthlyCost: number
}

export interface ModelRecommendation {
  id: string
  type: RecommendationType
  title: string
  description: string
  priority: RecommendationPriority
  impact: ImpactLevel
  effort: EffortLevel
  savings?: number
  implementation: string[]
  resources: string[]
}

// Enums and Union Types
export type AIProvider = 'openai' | 'anthropic' | 'google' | 'microsoft' | 'aws' | 'local' | 'custom'
export type ModelStatus = 'active' | 'inactive' | 'error' | 'maintenance' | 'deprecated' | 'testing'
export type ModelType = 'text-generation' | 'code-generation' | 'analysis' | 'classification' | 'embedding' | 'multimodal'
export type ModelCapability = 'text-generation' | 'code-analysis' | 'test-generation' | 'bug-detection' | 'performance-analysis' | 'security-analysis'
export type BackoffStrategy = 'linear' | 'exponential' | 'fixed' | 'random'
export type PromptCategory = 'analysis' | 'generation' | 'classification' | 'summarization' | 'translation' | 'custom'
export type TemplateStatus = 'active' | 'draft' | 'deprecated' | 'archived'
export type VariableType = 'string' | 'number' | 'boolean' | 'array' | 'object' | 'date'
export type FallbackTrigger = 'error-rate' | 'response-time' | 'availability' | 'cost' | 'manual'
export type AlertType = 'performance' | 'error' | 'cost' | 'usage' | 'availability'
export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type AlertStatus = 'active' | 'resolved' | 'acknowledged' | 'suppressed'
export type AlertActionType = 'email' | 'slack' | 'webhook' | 'fallback' | 'scale' | 'pause'
export type ComparisonOperator = 'greater-than' | 'less-than' | 'equals' | 'not-equals' | 'greater-equal' | 'less-equal'
export type ReportPeriod = 'hour' | 'day' | 'week' | 'month' | 'quarter' | 'year'
export type RecommendationType = 'cost-optimization' | 'performance-improvement' | 'reliability-enhancement' | 'security-hardening'
export type RecommendationPriority = 'critical' | 'high' | 'medium' | 'low'
export type ImpactLevel = 'high' | 'medium' | 'low'
export type EffortLevel = 'high' | 'medium' | 'low'

// Service Interfaces
export interface AIModelService {
  getModels(filters?: ModelFilters): Promise<AIModel[]>
  getModel(modelId: string): Promise<AIModel>
  createModel(model: Omit<AIModel, 'id' | 'createdAt' | 'updatedAt'>): Promise<AIModel>
  updateModel(modelId: string, updates: Partial<AIModel>): Promise<AIModel>
  deleteModel(modelId: string): Promise<void>
  testModel(modelId: string, testData: any): Promise<ModelTestResult>
  getModelMetrics(modelId: string, period?: ReportPeriod): Promise<ModelMetrics>
  getPromptTemplates(filters?: TemplateFilters): Promise<PromptTemplate[]>
  createPromptTemplate(template: Omit<PromptTemplate, 'id' | 'createdAt' | 'updatedAt'>): Promise<PromptTemplate>
  updatePromptTemplate(templateId: string, updates: Partial<PromptTemplate>): Promise<PromptTemplate>
  deletePromptTemplate(templateId: string): Promise<void>
  testPromptTemplate(templateId: string, variables: Record<string, any>): Promise<TemplateTestResult>
  getModelAlerts(modelId?: string): Promise<ModelAlert[]>
  createModelAlert(alert: Omit<ModelAlert, 'id' | 'triggeredAt'>): Promise<ModelAlert>
  acknowledgeAlert(alertId: string): Promise<void>
  resolveAlert(alertId: string): Promise<void>
  getUsageReport(modelId: string, period: ReportPeriod): Promise<ModelUsageReport>
  getFallbackConfiguration(modelId: string): Promise<ModelFallback[]>
  updateFallbackConfiguration(modelId: string, config: ModelFallback[]): Promise<void>
}

export interface ModelFilters {
  provider?: AIProvider[]
  status?: ModelStatus[]
  type?: ModelType[]
  capabilities?: ModelCapability[]
  search?: string
  tags?: string[]
  createdBy?: string
  dateRange?: {
    start: string
    end: string
  }
}

export interface TemplateFilters {
  category?: PromptCategory[]
  status?: TemplateStatus[]
  modelCompatibility?: string[]
  search?: string
  tags?: string[]
  createdBy?: string
  dateRange?: {
    start: string
    end: string
  }
}

// Additional filter interfaces for the service
export interface AIModelFilter {
  provider?: AIProvider[]
  status?: ModelStatus[]
  name?: string
  version?: string
}

export interface PromptTemplateFilter {
  category?: PromptCategory[]
  name?: string
  createdBy?: string
  version?: string
}

// Performance and reporting interfaces
export interface ModelPerformanceReport {
  modelId: string
  timeRange: {
    start: Date
    end: Date
  }
  metrics: {
    totalRequests: number
    averageResponseTime: number
    successRate: number
    errorRate: number
    totalCost: number
    tokenUsage: {
      total: number
      average: number
      peak: number
    }
  }
  trends: {
    responseTime: Array<{ timestamp: Date; value: number }>
    requestVolume: Array<{ timestamp: Date; value: number }>
    errorRate: Array<{ timestamp: Date; value: number }>
  }
  recommendations: string[]
}

// Model Registry interface
export interface ModelRegistry {
  models: AIModel[]
  templates: PromptTemplate[]
  configurations: ModelConfiguration[]
  metrics: ModelMetrics[]
}

// Error handling
export class AIModelError extends Error {
  public code: string
  public details?: Record<string, any>
  public timestamp: Date

  constructor(code: string, message: string, details?: Record<string, any>, timestamp?: Date) {
    super(message)
    this.name = 'AIModelError'
    this.code = code
    this.details = details
    this.timestamp = timestamp || new Date()
  }
}

export interface ModelTestResult {
  success: boolean
  responseTime: number
  output: any
  error?: string
  metrics: {
    tokenUsage: TokenUsage
    cost: number
    latency: number
  }
  timestamp: string
}

export interface TemplateTestResult {
  success: boolean
  output: string
  score?: number
  error?: string
  metrics: {
    responseTime: number
    tokenUsage: TokenUsage
    cost: number
  }
  timestamp: string
}

// Constants
export const AI_PROVIDERS: AIProvider[] = ['openai', 'anthropic', 'google', 'microsoft', 'aws', 'local', 'custom']
export const MODEL_STATUSES: ModelStatus[] = ['active', 'inactive', 'error', 'maintenance', 'deprecated', 'testing']
export const MODEL_TYPES: ModelType[] = ['text-generation', 'code-generation', 'analysis', 'classification', 'embedding', 'multimodal']

export const DEFAULT_MODEL_METRICS: ModelMetrics = {
  responseTime: 0,
  averageResponseTime: 0,
  accuracy: 0,
  tokenUsage: {
    totalTokens: 0,
    inputTokens: 0,
    outputTokens: 0,
    averageTokensPerRequest: 0,
    tokenCostPerRequest: 0,
    dailyUsage: 0,
    monthlyUsage: 0
  },
  costPerRequest: 0,
  requestCount: 0,
  successRate: 0,
  errorRate: 0,
  availability: 0,
  throughput: 0,
  latency: {
    p50: 0,
    p95: 0,
    p99: 0,
    min: 0,
    max: 0,
    average: 0
  },
  performance: {
    requestsPerSecond: 0,
    concurrentRequests: 0,
    queueLength: 0,
    processingTime: 0,
    networkLatency: 0,
    errorCount: 0,
    timeoutCount: 0
  },
  lastUpdated: ''
}

export const DEFAULT_RATE_LIMIT: RateLimit = {
  requestsPerMinute: 60,
  requestsPerHour: 3600,
  requestsPerDay: 86400,
  tokensPerMinute: 10000,
  tokensPerHour: 600000,
  tokensPerDay: 14400000,
  concurrentRequests: 10
}

export const DEFAULT_RETRY_POLICY: RetryPolicy = {
  maxRetries: 3,
  backoffStrategy: 'exponential',
  retryableErrors: ['timeout', 'rate_limit', 'server_error'],
  timeout: 30000
}