// Analytics & Insights Type Definitions

export interface AnalyticsMetrics {
  overview: OverviewMetrics
  testing: TestingMetrics
  performance: PerformanceMetrics
  quality: QualityMetrics
  productivity: ProductivityMetrics
  trends: TrendAnalysis
  insights: AIInsight[]
  forecasts: AnalyticsForecast[]
  benchmarks: BenchmarkComparison[]
  lastUpdated: string
}

export interface OverviewMetrics {
  totalTests: number
  testExecutions: number
  passRate: number
  failureRate: number
  coverage: CoverageMetrics
  defects: DefectMetrics
  environments: EnvironmentMetrics
  resources: ResourceUtilization
  timeSpan: TimeSpan
}

export interface CoverageMetrics {
  overall: number
  line: number
  branch: number
  function: number
  statement: number
  byComponent: ComponentCoverage[]
  trends: CoverageTrend[]
  targets: CoverageTarget[]
}

export interface ComponentCoverage {
  component: string
  coverage: number
  lines: number
  branches: number
  functions: number
  statements: number
  trend: TrendDirection
}

export interface CoverageTrend {
  date: string
  overall: number
  line: number
  branch: number
  function: number
  statement: number
}

export interface CoverageTarget {
  type: CoverageType
  target: number
  current: number
  achieved: boolean
  gap: number
}

export interface DefectMetrics {
  total: number
  open: number
  resolved: number
  critical: number
  high: number
  medium: number
  low: number
  byCategory: DefectCategory[]
  byComponent: ComponentDefects[]
  resolution: DefectResolution
  trends: DefectTrend[]
}

export interface DefectCategory {
  category: string
  count: number
  percentage: number
  severity: DefectSeverityDistribution
}

export interface DefectSeverityDistribution {
  critical: number
  high: number
  medium: number
  low: number
}

export interface ComponentDefects {
  component: string
  total: number
  open: number
  resolved: number
  density: number
  trend: TrendDirection
}

export interface DefectResolution {
  averageTime: number
  medianTime: number
  byPriority: ResolutionTime[]
  byCategory: ResolutionTime[]
  efficiency: number
}

export interface ResolutionTime {
  category: string
  averageTime: number
  medianTime: number
  count: number
}

export interface DefectTrend {
  date: string
  discovered: number
  resolved: number
  open: number
  backlog: number
}

export interface EnvironmentMetrics {
  total: number
  active: number
  idle: number
  maintenance: number
  utilization: number
  availability: number
  performance: EnvironmentPerformance[]
  costs: EnvironmentCost[]
}

export interface EnvironmentPerformance {
  environment: string
  utilization: number
  availability: number
  throughput: number
  responseTime: number
  errorRate: number
}

export interface EnvironmentCost {
  environment: string
  cost: number
  usage: number
  efficiency: number
  trend: TrendDirection
}

export interface ResourceUtilization {
  cpu: UtilizationMetric
  memory: UtilizationMetric
  storage: UtilizationMetric
  network: UtilizationMetric
  overall: number
  efficiency: number
  bottlenecks: ResourceBottleneck[]
}

export interface UtilizationMetric {
  current: number
  average: number
  peak: number
  trend: TrendDirection
  threshold: number
  alerts: number
}

export interface ResourceBottleneck {
  resource: string
  severity: BottleneckSeverity
  impact: string
  recommendation: string
  frequency: number
}

export interface TestingMetrics {
  execution: ExecutionMetrics
  automation: AutomationMetrics
  reliability: ReliabilityMetrics
  efficiency: EfficiencyMetrics
  quality: TestQualityMetrics
}

export interface ExecutionMetrics {
  totalRuns: number
  successfulRuns: number
  failedRuns: number
  cancelledRuns: number
  averageDuration: number
  medianDuration: number
  throughput: number
  parallelization: number
  queueTime: number
  trends: ExecutionTrend[]
}

export interface ExecutionTrend {
  date: string
  runs: number
  success: number
  failure: number
  duration: number
  throughput: number
}

export interface AutomationMetrics {
  automationRate: number
  manualTests: number
  automatedTests: number
  automationCoverage: number
  maintenanceEffort: number
  roi: AutomationROI
  trends: AutomationTrend[]
}

export interface AutomationROI {
  investment: number
  savings: number
  roi: number
  paybackPeriod: number
  efficiency: number
}

export interface AutomationTrend {
  date: string
  automationRate: number
  coverage: number
  maintenance: number
  efficiency: number
}

export interface ReliabilityMetrics {
  stability: number
  consistency: number
  flakiness: number
  repeatability: number
  flakyTests: FlakyTest[]
  stabilityTrends: StabilityTrend[]
}

export interface FlakyTest {
  testId: string
  testName: string
  flakinessRate: number
  occurrences: number
  lastFlaky: string
  impact: FlakinessImpact
}

export interface FlakinessImpact {
  severity: FlakinessSeverity
  blockedRuns: number
  timeWasted: number
  confidence: number
}

export interface StabilityTrend {
  date: string
  stability: number
  flakiness: number
  consistency: number
  reliability: number
}

export interface EfficiencyMetrics {
  testDesign: number
  execution: number
  maintenance: number
  reporting: number
  overall: number
  bottlenecks: EfficiencyBottleneck[]
  improvements: EfficiencyImprovement[]
}

export interface EfficiencyBottleneck {
  area: string
  impact: number
  frequency: number
  recommendation: string
  effort: string
}

export interface EfficiencyImprovement {
  area: string
  potential: number
  effort: string
  priority: ImprovementPriority
  timeline: string
}

export interface TestQualityMetrics {
  coverage: number
  depth: number
  breadth: number
  maintainability: number
  readability: number
  reusability: number
  documentation: number
  standards: StandardsCompliance[]
}

export interface StandardsCompliance {
  standard: string
  compliance: number
  violations: number
  score: number
}

export interface PerformanceMetrics {
  response: ResponseMetrics
  throughput: ThroughputMetrics
  scalability: ScalabilityMetrics
  reliability: PerformanceReliability
  optimization: OptimizationMetrics
  benchmarks: PerformanceBenchmark[]
}

export interface ResponseMetrics {
  average: number
  median: number
  p95: number
  p99: number
  minimum: number
  maximum: number
  distribution: ResponseDistribution
  trends: ResponseTrend[]
}

export interface ResponseDistribution {
  fast: number
  acceptable: number
  slow: number
  timeout: number
}

export interface ResponseTrend {
  date: string
  average: number
  median: number
  p95: number
  p99: number
}

export interface ThroughputMetrics {
  current: number
  average: number
  peak: number
  capacity: number
  utilization: number
  trends: ThroughputTrend[]
}

export interface ThroughputTrend {
  date: string
  throughput: number
  capacity: number
  utilization: number
}

export interface ScalabilityMetrics {
  horizontal: ScalabilityMeasure
  vertical: ScalabilityMeasure
  elasticity: number
  efficiency: number
  limits: ScalabilityLimit[]
}

export interface ScalabilityMeasure {
  factor: number
  efficiency: number
  breakpoint: number
  cost: number
}

export interface ScalabilityLimit {
  resource: string
  limit: number
  current: number
  utilization: number
  recommendation: string
}

export interface PerformanceReliability {
  availability: number
  consistency: number
  predictability: number
  degradation: DegradationMetrics
}

export interface DegradationMetrics {
  frequency: number
  severity: number
  duration: number
  recovery: number
}

export interface OptimizationMetrics {
  opportunities: OptimizationOpportunity[]
  implemented: OptimizationResult[]
  potential: number
  achieved: number
}

export interface OptimizationOpportunity {
  area: string
  type: OptimizationType
  impact: number
  effort: string
  priority: OptimizationPriority
  description: string
  recommendation: string
}

export interface OptimizationResult {
  area: string
  improvement: number
  effort: string
  cost: number
  roi: number
  implementedAt: string
}

export interface PerformanceBenchmark {
  name: string
  category: string
  baseline: number
  current: number
  target: number
  improvement: number
  trend: TrendDirection
}

export interface QualityMetrics {
  overall: number
  code: CodeQualityMetrics
  test: TestQualityMetrics
  process: ProcessQualityMetrics
  delivery: DeliveryQualityMetrics
  trends: QualityTrend[]
}

export interface CodeQualityMetrics {
  maintainability: number
  reliability: number
  security: number
  performance: number
  coverage: number
  complexity: ComplexityMetrics
  duplication: number
  violations: QualityViolation[]
}

export interface ComplexityMetrics {
  cyclomatic: number
  cognitive: number
  halstead: number
  maintainability: number
}

export interface QualityViolation {
  type: ViolationType
  severity: ViolationSeverity
  count: number
  trend: TrendDirection
  impact: string
}

export interface ProcessQualityMetrics {
  adherence: number
  consistency: number
  efficiency: number
  automation: number
  documentation: number
  compliance: ComplianceMetrics[]
}

export interface ComplianceMetrics {
  framework: string
  score: number
  violations: number
  trend: TrendDirection
}

export interface DeliveryQualityMetrics {
  defectRate: number
  escapeRate: number
  customerSatisfaction: number
  timeToMarket: number
  reliability: number
  performance: number
}

export interface QualityTrend {
  date: string
  overall: number
  code: number
  test: number
  process: number
  delivery: number
}

export interface ProductivityMetrics {
  team: TeamProductivity
  individual: IndividualProductivity[]
  velocity: VelocityMetrics
  efficiency: ProductivityEfficiency
  collaboration: CollaborationMetrics
  trends: ProductivityTrend[]
}

export interface TeamProductivity {
  throughput: number
  velocity: number
  efficiency: number
  quality: number
  collaboration: number
  satisfaction: number
}

export interface IndividualProductivity {
  userId: string
  userName: string
  throughput: number
  quality: number
  efficiency: number
  collaboration: number
  growth: number
  contributions: ContributionMetrics
}

export interface ContributionMetrics {
  testsCreated: number
  testsExecuted: number
  defectsFound: number
  defectsResolved: number
  codeReviews: number
  documentation: number
}

export interface VelocityMetrics {
  current: number
  average: number
  trend: TrendDirection
  predictability: number
  capacity: number
  burndown: BurndownMetrics
}

export interface BurndownMetrics {
  planned: number
  completed: number
  remaining: number
  onTrack: boolean
  projectedCompletion: string
}

export interface ProductivityEfficiency {
  planning: number
  execution: number
  review: number
  deployment: number
  overall: number
  bottlenecks: ProductivityBottleneck[]
}

export interface ProductivityBottleneck {
  phase: string
  impact: number
  frequency: number
  cause: string
  recommendation: string
}

export interface CollaborationMetrics {
  communication: number
  knowledge: number
  coordination: number
  support: number
  feedback: number
  networkMetrics: NetworkMetrics
}

export interface NetworkMetrics {
  connections: number
  centrality: number
  clustering: number
  influence: number
}

export interface ProductivityTrend {
  date: string
  throughput: number
  velocity: number
  efficiency: number
  quality: number
  satisfaction: number
}

export interface TrendAnalysis {
  patterns: TrendPattern[]
  seasonality: SeasonalPattern[]
  anomalies: TrendAnomaly[]
  correlations: TrendCorrelation[]
  forecasts: TrendForecast[]
}

export interface TrendPattern {
  metric: string
  pattern: PatternType
  strength: number
  duration: string
  confidence: number
  description: string
}

export interface SeasonalPattern {
  metric: string
  period: SeasonalPeriod
  amplitude: number
  phase: number
  confidence: number
  description: string
}

export interface TrendAnomaly {
  metric: string
  timestamp: string
  value: number
  expected: number
  deviation: number
  severity: AnomalySeverity
  type: AnomalyType
  explanation: string
}

export interface TrendCorrelation {
  metric1: string
  metric2: string
  correlation: number
  strength: CorrelationStrength
  direction: CorrelationDirection
  significance: number
  explanation: string
}

export interface TrendForecast {
  metric: string
  horizon: ForecastHorizon
  predictions: ForecastPrediction[]
  confidence: number
  methodology: string
  assumptions: string[]
}

export interface ForecastPrediction {
  timestamp: string
  value: number
  lower: number
  upper: number
  confidence: number
}

export interface AIInsight {
  id: string
  type: InsightType
  category: InsightCategory
  priority: InsightPriority
  confidence: number
  title: string
  description: string
  impact: InsightImpact
  recommendations: InsightRecommendation[]
  evidence: InsightEvidence[]
  metadata: InsightMetadata
  createdAt: string
  validUntil?: string
}

export interface InsightImpact {
  area: ImpactArea
  magnitude: ImpactMagnitude
  timeframe: ImpactTimeframe
  affected: string[]
  metrics: ImpactMetric[]
}

export interface ImpactMetric {
  metric: string
  currentValue: number
  projectedValue: number
  improvement: number
  confidence: number
}

export interface InsightRecommendation {
  id: string
  title: string
  description: string
  priority: RecommendationPriority
  effort: EffortLevel
  impact: ImpactLevel
  timeline: string
  steps: RecommendationStep[]
  resources: string[]
  risks: string[]
  dependencies: string[]
}

export interface RecommendationStep {
  order: number
  title: string
  description: string
  duration: string
  resources: string[]
  deliverables: string[]
}

export interface InsightEvidence {
  type: EvidenceType
  source: string
  data: any
  confidence: number
  timestamp: string
  description: string
}

export interface InsightMetadata {
  algorithm: string
  version: string
  parameters: Record<string, any>
  dataSource: string[]
  processingTime: number
  accuracy: number
}

export interface AnalyticsForecast {
  id: string
  metric: string
  type: ForecastType
  horizon: ForecastHorizon
  methodology: ForecastMethodology
  predictions: ForecastPrediction[]
  accuracy: ForecastAccuracy
  assumptions: ForecastAssumption[]
  scenarios: ForecastScenario[]
  confidence: number
  createdAt: string
  validUntil: string
}

export interface ForecastAccuracy {
  historical: number
  crossValidation: number
  mae: number
  rmse: number
  mape: number
}

export interface ForecastAssumption {
  category: string
  description: string
  impact: AssumptionImpact
  probability: number
}

export interface AssumptionImpact {
  direction: ImpactDirection
  magnitude: number
  confidence: number
}

export interface ForecastScenario {
  name: string
  description: string
  probability: number
  predictions: ForecastPrediction[]
  assumptions: string[]
}

export interface BenchmarkComparison {
  category: string
  metric: string
  current: number
  benchmark: number
  percentile: number
  industry: string
  comparison: ComparisonResult
  gap: number
  recommendations: BenchmarkRecommendation[]
}

export interface BenchmarkRecommendation {
  area: string
  improvement: number
  effort: string
  timeline: string
  priority: RecommendationPriority
}

export interface CustomReport {
  id: string
  name: string
  description: string
  type: ReportType
  category: ReportCategory
  metrics: ReportMetric[]
  filters: ReportFilter[]
  grouping: ReportGrouping[]
  visualization: ReportVisualization
  schedule: ReportSchedule
  recipients: string[]
  format: ReportFormat
  template: string
  status: ReportStatus
  createdAt: string
  updatedAt: string
  createdBy: string
}

export interface ReportMetric {
  name: string
  aggregation: AggregationType
  calculation: string
  format: MetricFormat
  threshold?: MetricThreshold
}

export interface MetricThreshold {
  warning: number
  critical: number
  direction: ThresholdDirection
}

export interface ReportFilter {
  field: string
  operator: FilterOperator
  value: any
  enabled: boolean
}

export interface ReportGrouping {
  field: string
  order: GroupingOrder
  limit?: number
}

export interface ReportVisualization {
  type: VisualizationType
  configuration: VisualizationConfig
  layout: LayoutConfig
}

export interface VisualizationConfig {
  colors: string[]
  axes: AxisConfig[]
  legend: LegendConfig
  annotations: AnnotationConfig[]
}

export interface AxisConfig {
  axis: AxisType
  label: string
  scale: ScaleType
  range?: [number, number]
  format?: string
}

export interface LegendConfig {
  position: LegendPosition
  visible: boolean
  interactive: boolean
}

export interface AnnotationConfig {
  type: AnnotationType
  value: any
  label: string
  style: AnnotationStyle
}

export interface AnnotationStyle {
  color: string
  style: LineStyle
  width: number
}

export interface LayoutConfig {
  width: number
  height: number
  margin: MarginConfig
  responsive: boolean
}

export interface MarginConfig {
  top: number
  right: number
  bottom: number
  left: number
}

export interface ReportSchedule {
  enabled: boolean
  frequency: ScheduleFrequency
  time: string
  timezone: string
  days?: string[]
  endDate?: string
}

export interface TimeSpan {
  start: string
  end: string
  duration: string
  periods: TimePeriod[]
}

export interface TimePeriod {
  name: string
  start: string
  end: string
  duration: string
}

// Enums and Union Types
export type CoverageType = 'line' | 'branch' | 'function' | 'statement'
export type TrendDirection = 'up' | 'down' | 'stable' | 'volatile'
export type BottleneckSeverity = 'low' | 'medium' | 'high' | 'critical'
export type FlakinessSeverity = 'low' | 'medium' | 'high' | 'critical'
export type ImprovementPriority = 'low' | 'medium' | 'high' | 'critical'
export type OptimizationType = 'performance' | 'cost' | 'quality' | 'efficiency'
export type OptimizationPriority = 'low' | 'medium' | 'high' | 'critical'
export type ViolationType = 'code-smell' | 'bug' | 'vulnerability' | 'duplication' | 'complexity'
export type ViolationSeverity = 'info' | 'minor' | 'major' | 'critical' | 'blocker'
export type PatternType = 'linear' | 'exponential' | 'logarithmic' | 'cyclical' | 'random'
export type SeasonalPeriod = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'
export type AnomalySeverity = 'low' | 'medium' | 'high' | 'critical'
export type AnomalyType = 'spike' | 'drop' | 'shift' | 'outlier' | 'pattern-break'
export type CorrelationStrength = 'weak' | 'moderate' | 'strong' | 'very-strong'
export type CorrelationDirection = 'positive' | 'negative'
export type ForecastHorizon = 'short' | 'medium' | 'long'
export type InsightType = 'trend' | 'anomaly' | 'pattern' | 'correlation' | 'prediction' | 'recommendation'
export type InsightCategory = 'performance' | 'quality' | 'productivity' | 'cost' | 'risk' | 'opportunity'
export type InsightPriority = 'low' | 'medium' | 'high' | 'critical'
export type ImpactArea = 'testing' | 'development' | 'deployment' | 'operations' | 'business'
export type ImpactMagnitude = 'low' | 'medium' | 'high' | 'very-high'
export type ImpactTimeframe = 'immediate' | 'short-term' | 'medium-term' | 'long-term'
export type RecommendationPriority = 'low' | 'medium' | 'high' | 'critical'
export type EffortLevel = 'low' | 'medium' | 'high' | 'very-high'
export type ImpactLevel = 'low' | 'medium' | 'high' | 'very-high'
export type EvidenceType = 'metric' | 'trend' | 'correlation' | 'anomaly' | 'pattern' | 'benchmark'
export type ForecastType = 'trend' | 'seasonal' | 'regression' | 'ml' | 'ensemble'
export type ForecastMethodology = 'arima' | 'exponential-smoothing' | 'linear-regression' | 'neural-network' | 'ensemble'
export type ImpactDirection = 'positive' | 'negative' | 'neutral'
export type ComparisonResult = 'above' | 'at' | 'below' | 'significantly-above' | 'significantly-below'
export type ReportType = 'dashboard' | 'summary' | 'detailed' | 'trend' | 'comparison' | 'custom'
export type ReportCategory = 'executive' | 'operational' | 'technical' | 'compliance' | 'performance'
export type AggregationType = 'sum' | 'average' | 'count' | 'min' | 'max' | 'median' | 'percentile'
export type MetricFormat = 'number' | 'percentage' | 'currency' | 'duration' | 'bytes'
export type ThresholdDirection = 'above' | 'below'
export type FilterOperator = 'equals' | 'not-equals' | 'greater' | 'less' | 'contains' | 'in' | 'between'
export type GroupingOrder = 'asc' | 'desc'
export type VisualizationType = 'line' | 'bar' | 'pie' | 'scatter' | 'heatmap' | 'gauge' | 'table'
export type AxisType = 'x' | 'y' | 'z'
export type ScaleType = 'linear' | 'logarithmic' | 'time' | 'categorical'
export type LegendPosition = 'top' | 'bottom' | 'left' | 'right' | 'none'
export type AnnotationType = 'line' | 'band' | 'point' | 'text'
export type LineStyle = 'solid' | 'dashed' | 'dotted'
export type ScheduleFrequency = 'hourly' | 'daily' | 'weekly' | 'monthly' | 'quarterly'
export type ReportFormat = 'pdf' | 'html' | 'csv' | 'excel' | 'json'
export type ReportStatus = 'active' | 'inactive' | 'draft' | 'archived'

// Service Interfaces
export interface AnalyticsService {
  getAnalyticsMetrics(filters?: AnalyticsFilters): Promise<AnalyticsMetrics>
  getOverviewMetrics(period?: string): Promise<OverviewMetrics>
  getTestingMetrics(filters?: TestingFilters): Promise<TestingMetrics>
  getPerformanceMetrics(filters?: PerformanceFilters): Promise<PerformanceMetrics>
  getQualityMetrics(filters?: QualityFilters): Promise<QualityMetrics>
  getProductivityMetrics(filters?: ProductivityFilters): Promise<ProductivityMetrics>
  getTrendAnalysis(metric: string, period: string): Promise<TrendAnalysis>
  getAIInsights(filters?: InsightFilters): Promise<AIInsight[]>
  generateInsight(type: InsightType, parameters: any): Promise<AIInsight>
  getForecasts(metric?: string, horizon?: ForecastHorizon): Promise<AnalyticsForecast[]>
  generateForecast(metric: string, horizon: ForecastHorizon, methodology?: ForecastMethodology): Promise<AnalyticsForecast>
  getBenchmarkComparisons(category?: string): Promise<BenchmarkComparison[]>
  getCustomReports(): Promise<CustomReport[]>
  createCustomReport(report: Omit<CustomReport, 'id' | 'createdAt' | 'updatedAt'>): Promise<CustomReport>
  updateCustomReport(reportId: string, updates: Partial<CustomReport>): Promise<CustomReport>
  deleteCustomReport(reportId: string): Promise<void>
  generateReport(reportId: string): Promise<ReportResult>
  scheduleReport(reportId: string, schedule: ReportSchedule): Promise<void>
  exportData(query: DataQuery, format: ExportFormat): Promise<string>
  getDataSources(): Promise<DataSource[]>
  validateQuery(query: DataQuery): Promise<QueryValidationResult>
  executeQuery(query: DataQuery): Promise<QueryResult>
  getMetricDefinitions(): Promise<MetricDefinition[]>
  createMetricDefinition(metric: Omit<MetricDefinition, 'id' | 'createdAt'>): Promise<MetricDefinition>
  updateMetricDefinition(metricId: string, updates: Partial<MetricDefinition>): Promise<MetricDefinition>
  deleteMetricDefinition(metricId: string): Promise<void>
  getAlerts(filters?: AlertFilters): Promise<AnalyticsAlert[]>
  createAlert(alert: Omit<AnalyticsAlert, 'id' | 'createdAt'>): Promise<AnalyticsAlert>
  updateAlert(alertId: string, updates: Partial<AnalyticsAlert>): Promise<AnalyticsAlert>
  deleteAlert(alertId: string): Promise<void>
}

export interface AnalyticsFilters {
  dateRange?: {
    start: string
    end: string
  }
  metrics?: string[]
  components?: string[]
  environments?: string[]
  teams?: string[]
  users?: string[]
  tags?: string[]
}

export interface TestingFilters extends AnalyticsFilters {
  testTypes?: string[]
  testSuites?: string[]
  status?: string[]
}

export interface PerformanceFilters extends AnalyticsFilters {
  operations?: string[]
  thresholds?: {
    responseTime?: number
    throughput?: number
    errorRate?: number
  }
}

export interface QualityFilters extends AnalyticsFilters {
  qualityGates?: string[]
  violations?: ViolationType[]
  severity?: ViolationSeverity[]
}

export interface ProductivityFilters extends AnalyticsFilters {
  roles?: string[]
  skills?: string[]
  experience?: string[]
}

export interface InsightFilters {
  type?: InsightType[]
  category?: InsightCategory[]
  priority?: InsightPriority[]
  confidence?: number
  dateRange?: {
    start: string
    end: string
  }
}

export interface ReportResult {
  id: string
  reportId: string
  data: any
  format: ReportFormat
  url?: string
  size: number
  generatedAt: string
  expiresAt?: string
}

export interface DataQuery {
  metrics: string[]
  dimensions: string[]
  filters: QueryFilter[]
  groupBy: string[]
  orderBy: QuerySort[]
  limit?: number
  offset?: number
  dateRange?: {
    start: string
    end: string
  }
}

export interface QueryFilter {
  field: string
  operator: FilterOperator
  value: any
}

export interface QuerySort {
  field: string
  direction: 'asc' | 'desc'
}

export interface QueryValidationResult {
  valid: boolean
  errors: QueryError[]
  warnings: string[]
  estimatedRows: number
  estimatedCost: number
}

export interface QueryError {
  field: string
  message: string
  code: string
}

export interface QueryResult {
  data: any[]
  metadata: QueryMetadata
  executionTime: number
  rowCount: number
}

export interface QueryMetadata {
  columns: ColumnMetadata[]
  totalRows: number
  cached: boolean
  cacheHit: boolean
}

export interface ColumnMetadata {
  name: string
  type: string
  nullable: boolean
  description?: string
}

export interface DataSource {
  id: string
  name: string
  type: DataSourceType
  connection: ConnectionConfig
  schema: SchemaInfo
  status: DataSourceStatus
  lastSync?: string
  metrics: DataSourceMetrics
}

export interface ConnectionConfig {
  host?: string
  port?: number
  database?: string
  username?: string
  password?: string
  ssl?: boolean
  timeout?: number
  poolSize?: number
}

export interface SchemaInfo {
  tables: TableInfo[]
  views: ViewInfo[]
  lastUpdated: string
}

export interface TableInfo {
  name: string
  columns: ColumnInfo[]
  rowCount: number
  size: number
}

export interface ColumnInfo {
  name: string
  type: string
  nullable: boolean
  primaryKey: boolean
  foreignKey?: string
}

export interface ViewInfo {
  name: string
  definition: string
  columns: ColumnInfo[]
}

export interface DataSourceMetrics {
  queries: number
  errors: number
  averageResponseTime: number
  dataVolume: number
  uptime: number
}

export interface MetricDefinition {
  id: string
  name: string
  displayName: string
  description: string
  category: string
  type: MetricType
  unit: string
  calculation: string
  aggregation: AggregationType
  dimensions: string[]
  filters: MetricFilter[]
  format: MetricFormat
  thresholds: MetricThreshold[]
  tags: string[]
  createdAt: string
  updatedAt: string
  createdBy: string
}

export interface MetricFilter {
  field: string
  operator: FilterOperator
  value: any
  required: boolean
}

export interface AnalyticsAlert {
  id: string
  name: string
  description: string
  metric: string
  condition: AlertCondition
  threshold: number
  severity: AlertSeverity
  enabled: boolean
  recipients: string[]
  channels: string[]
  frequency: AlertFrequency
  suppressionRules: SuppressionRule[]
  escalation: AlertEscalation
  lastTriggered?: string
  status: AlertStatus
  createdAt: string
  updatedAt: string
  createdBy: string
}

export interface AlertCondition {
  operator: ComparisonOperator
  value: number
  duration?: number
  aggregation?: AggregationType
}

export interface AlertEscalation {
  enabled: boolean
  levels: EscalationLevel[]
  timeout: number
}

export interface EscalationLevel {
  level: number
  delay: number
  recipients: string[]
  channels: string[]
}

export interface SuppressionRule {
  condition: string
  duration: number
  enabled: boolean
}

export type DataSourceType = 'database' | 'api' | 'file' | 'stream' | 'webhook'
export type DataSourceStatus = 'connected' | 'disconnected' | 'error' | 'syncing'
export type MetricType = 'counter' | 'gauge' | 'histogram' | 'summary' | 'rate'
export type ExportFormat = 'csv' | 'json' | 'excel' | 'pdf'
export type ComparisonOperator = 'greater' | 'less' | 'equal' | 'not-equal' | 'greater-equal' | 'less-equal'
export type AlertSeverity = 'info' | 'warning' | 'critical'
export type AlertFrequency = 'immediate' | 'hourly' | 'daily' | 'weekly'
export type AlertStatus = 'active' | 'suppressed' | 'resolved' | 'disabled'

// Constants
export const INSIGHT_TYPES: InsightType[] = ['trend', 'anomaly', 'pattern', 'correlation', 'prediction', 'recommendation']
export const INSIGHT_CATEGORIES: InsightCategory[] = ['performance', 'quality', 'productivity', 'cost', 'risk', 'opportunity']
export const FORECAST_HORIZONS: ForecastHorizon[] = ['short', 'medium', 'long']
export const VISUALIZATION_TYPES: VisualizationType[] = ['line', 'bar', 'pie', 'scatter', 'heatmap', 'gauge', 'table']

export const PRIORITY_COLORS = {
  low: '#52c41a',
  medium: '#faad14',
  high: '#fa8c16',
  critical: '#f5222d'
} as const

export const TREND_COLORS = {
  up: '#52c41a',
  down: '#f5222d',
  stable: '#1890ff',
  volatile: '#fa8c16'
} as const

export const INSIGHT_ICONS = {
  trend: 'trending-up',
  anomaly: 'alert-circle',
  pattern: 'activity',
  correlation: 'link',
  prediction: 'zap',
  recommendation: 'lightbulb'
} as const

export const DEFAULT_ANALYTICS_FILTERS: AnalyticsFilters = {
  dateRange: {
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    end: new Date().toISOString()
  }
}

export const DEFAULT_FORECAST_ACCURACY: ForecastAccuracy = {
  historical: 0,
  crossValidation: 0,
  mae: 0,
  rmse: 0,
  mape: 0
}