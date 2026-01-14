// Resource Monitoring & Capacity Planning Type Definitions

export interface ResourceMetrics {
  infrastructure: InfrastructureMetrics
  capacity: CapacityMetrics
  performance: PerformanceMetrics
  alerts: ResourceAlert[]
  trends: ResourceTrend[]
  forecasts: CapacityForecast[]
  lastUpdated: string
}

export interface InfrastructureMetrics {
  buildServers: ResourceNode[]
  qemuHosts: ResourceNode[]
  physicalBoards: BoardStatus[]
  networkDevices: NetworkDevice[]
  storageDevices: StorageDevice[]
  totalCapacity: CapacityInfo
  utilization: UtilizationSummary
  availability: AvailabilityMetrics
}

export interface ResourceNode {
  id: string
  name: string
  type: NodeType
  status: NodeStatus
  location: string
  specifications: NodeSpecifications
  usage: ResourceUsage
  health: HealthMetrics
  alerts: ResourceAlert[]
  maintenance: MaintenanceInfo
  tags: string[]
  metadata: Record<string, any>
}

export interface NodeSpecifications {
  cpu: CPUSpecification
  memory: MemorySpecification
  storage: StorageSpecification
  network: NetworkSpecification
  os: OSSpecification
  virtualization?: VirtualizationInfo
}

export interface CPUSpecification {
  model: string
  architecture: string
  cores: number
  threads: number
  frequency: number
  cache: CacheInfo
  features: string[]
}

export interface CacheInfo {
  l1: number
  l2: number
  l3: number
}

export interface MemorySpecification {
  total: number
  type: string
  speed: number
  channels: number
  ecc: boolean
}

export interface StorageSpecification {
  devices: StorageDevice[]
  totalCapacity: number
  totalUsed: number
  totalFree: number
  raid?: RAIDInfo
}

export interface StorageDevice {
  id: string
  name: string
  type: StorageType
  capacity: number
  used: number
  free: number
  health: StorageHealth
  temperature?: number
  readSpeed: number
  writeSpeed: number
  iops: IOPSMetrics
}

export interface IOPSMetrics {
  read: number
  write: number
  random: number
  sequential: number
}

export interface RAIDInfo {
  level: string
  status: string
  devices: string[]
  capacity: number
  redundancy: number
}

export interface NetworkSpecification {
  interfaces: NetworkInterface[]
  bandwidth: number
  latency: number
  protocols: string[]
}

export interface NetworkInterface {
  id: string
  name: string
  type: string
  speed: number
  status: string
  mac: string
  ip?: string
  usage: NetworkUsage
}

export interface NetworkUsage {
  bytesIn: number
  bytesOut: number
  packetsIn: number
  packetsOut: number
  errors: number
  drops: number
}

export interface OSSpecification {
  name: string
  version: string
  kernel: string
  architecture: string
  distribution?: string
  packages: PackageInfo[]
}

export interface PackageInfo {
  name: string
  version: string
  type: string
  size: number
}

export interface VirtualizationInfo {
  hypervisor: string
  version: string
  features: string[]
  maxVMs: number
  currentVMs: number
}

export interface ResourceUsage {
  cpu: CPUUsage
  memory: MemoryUsage
  storage: StorageUsage
  network: NetworkUsage
  processes: ProcessInfo[]
  timestamp: string
}

export interface CPUUsage {
  overall: number
  perCore: number[]
  user: number
  system: number
  idle: number
  iowait: number
  steal?: number
  loadAverage: LoadAverage
}

export interface LoadAverage {
  oneMinute: number
  fiveMinute: number
  fifteenMinute: number
}

export interface MemoryUsage {
  total: number
  used: number
  free: number
  available: number
  cached: number
  buffers: number
  swap: SwapUsage
  utilization: number
}

export interface SwapUsage {
  total: number
  used: number
  free: number
  utilization: number
}

export interface StorageUsage {
  total: number
  used: number
  free: number
  utilization: number
  inodes: InodeUsage
  io: IOMetrics
}

export interface InodeUsage {
  total: number
  used: number
  free: number
  utilization: number
}

export interface IOMetrics {
  readBytes: number
  writeBytes: number
  readOps: number
  writeOps: number
  readLatency: number
  writeLatency: number
  queueDepth: number
}

export interface ProcessInfo {
  pid: number
  name: string
  user: string
  cpu: number
  memory: number
  status: string
  startTime: string
  command: string
}

export interface HealthMetrics {
  overall: HealthStatus
  components: ComponentHealth[]
  score: number
  issues: HealthIssue[]
  lastCheck: string
}

export interface ComponentHealth {
  component: string
  status: HealthStatus
  score: number
  metrics: Record<string, number>
  issues: string[]
}

export interface HealthIssue {
  id: string
  component: string
  severity: IssueSeverity
  type: IssueType
  description: string
  impact: string
  recommendation: string
  detectedAt: string
  resolvedAt?: string
}

export interface MaintenanceInfo {
  scheduled: MaintenanceWindow[]
  history: MaintenanceRecord[]
  nextWindow?: MaintenanceWindow
  inMaintenance: boolean
}

export interface MaintenanceWindow {
  id: string
  title: string
  description: string
  type: MaintenanceType
  startTime: string
  endTime: string
  impact: MaintenanceImpact
  approver: string
  contacts: string[]
  procedures: string[]
  rollback: string[]
}

export interface MaintenanceRecord {
  id: string
  windowId: string
  actualStart: string
  actualEnd: string
  status: MaintenanceStatus
  issues: string[]
  notes: string
  performedBy: string
}

export interface BoardStatus {
  id: string
  name: string
  model: string
  architecture: string
  status: BoardStatusType
  connection: ConnectionInfo
  specifications: BoardSpecifications
  usage: ResourceUsage
  tests: TestExecution[]
  location: string
  owner: string
  tags: string[]
}

export interface ConnectionInfo {
  type: ConnectionType
  address: string
  port?: number
  protocol: string
  status: ConnectionStatus
  lastConnected: string
  latency: number
  reliability: number
}

export interface BoardSpecifications {
  cpu: string
  memory: string
  storage: string
  interfaces: string[]
  power: PowerInfo
  environmental: EnvironmentalInfo
}

export interface PowerInfo {
  consumption: number
  voltage: number
  current: number
  efficiency: number
}

export interface EnvironmentalInfo {
  temperature: number
  humidity: number
  pressure?: number
  location: string
}

export interface TestExecution {
  id: string
  name: string
  status: TestStatus
  startTime: string
  endTime?: string
  duration?: number
  results: TestResults
}

export interface TestResults {
  passed: number
  failed: number
  skipped: number
  errors: number
  coverage: number
  logs: string[]
}

export interface NetworkDevice {
  id: string
  name: string
  type: NetworkDeviceType
  model: string
  status: DeviceStatus
  location: string
  interfaces: NetworkInterface[]
  routing: RoutingInfo
  security: SecurityInfo
  performance: NetworkPerformance
}

export interface RoutingInfo {
  routes: RouteEntry[]
  protocols: string[]
  neighbors: NeighborInfo[]
}

export interface RouteEntry {
  destination: string
  gateway: string
  interface: string
  metric: number
  protocol: string
}

export interface NeighborInfo {
  address: string
  interface: string
  protocol: string
  state: string
  lastSeen: string
}

export interface SecurityInfo {
  firewall: FirewallStatus
  acls: ACLRule[]
  authentication: AuthenticationInfo
  encryption: EncryptionInfo
}

export interface FirewallStatus {
  enabled: boolean
  rules: FirewallRule[]
  defaultPolicy: string
  logging: boolean
}

export interface FirewallRule {
  id: string
  action: string
  source: string
  destination: string
  port: string
  protocol: string
  enabled: boolean
}

export interface ACLRule {
  id: string
  name: string
  action: string
  conditions: string[]
  enabled: boolean
}

export interface AuthenticationInfo {
  methods: string[]
  users: number
  sessions: number
  failures: number
}

export interface EncryptionInfo {
  protocols: string[]
  ciphers: string[]
  keyStrength: number
  certificates: CertificateInfo[]
}

export interface CertificateInfo {
  subject: string
  issuer: string
  validFrom: string
  validTo: string
  algorithm: string
  keySize: number
  status: string
}

export interface NetworkPerformance {
  throughput: ThroughputMetrics
  latency: LatencyMetrics
  packetLoss: number
  jitter: number
  errors: ErrorMetrics
}

export interface ThroughputMetrics {
  current: number
  average: number
  peak: number
  utilization: number
}

export interface LatencyMetrics {
  current: number
  average: number
  minimum: number
  maximum: number
  jitter: number
}

export interface ErrorMetrics {
  crc: number
  frame: number
  collision: number
  dropped: number
  total: number
}

export interface CapacityMetrics {
  current: CapacitySnapshot
  trends: CapacityTrend[]
  forecasts: CapacityForecast[]
  recommendations: CapacityRecommendation[]
  thresholds: CapacityThreshold[]
}

export interface CapacitySnapshot {
  timestamp: string
  resources: ResourceCapacity[]
  utilization: UtilizationSummary
  bottlenecks: Bottleneck[]
}

export interface ResourceCapacity {
  type: ResourceType
  total: number
  used: number
  available: number
  reserved: number
  utilization: number
  growth: GrowthMetrics
}

export interface GrowthMetrics {
  rate: number
  trend: TrendDirection
  seasonality: SeasonalPattern[]
  volatility: number
}

export interface SeasonalPattern {
  period: string
  factor: number
  confidence: number
}

export interface UtilizationSummary {
  overall: number
  byType: Record<ResourceType, number>
  peak: PeakUsage
  average: number
  distribution: UtilizationDistribution
}

export interface PeakUsage {
  value: number
  timestamp: string
  duration: number
  frequency: number
}

export interface UtilizationDistribution {
  low: number
  medium: number
  high: number
  critical: number
}

export interface Bottleneck {
  id: string
  resource: string
  type: BottleneckType
  severity: BottleneckSeverity
  impact: BottleneckImpact
  description: string
  causes: string[]
  recommendations: string[]
  detectedAt: string
}

export interface BottleneckImpact {
  performance: number
  availability: number
  cost: number
  users: number
  services: string[]
}

export interface CapacityTrend {
  timestamp: string
  resource: string
  value: number
  change: number
  trend: TrendDirection
  factors: TrendFactor[]
}

export interface TrendFactor {
  name: string
  impact: number
  confidence: number
  description: string
}

export interface CapacityForecast {
  resource: string
  horizon: ForecastHorizon
  predictions: ForecastPrediction[]
  confidence: number
  methodology: string
  assumptions: string[]
  risks: string[]
}

export interface ForecastPrediction {
  timestamp: string
  value: number
  lower: number
  upper: number
  confidence: number
}

export interface CapacityRecommendation {
  id: string
  type: RecommendationType
  priority: RecommendationPriority
  resource: string
  title: string
  description: string
  rationale: string
  impact: RecommendationImpact
  implementation: ImplementationPlan
  cost: CostEstimate
  timeline: string
  risks: string[]
  dependencies: string[]
}

export interface RecommendationImpact {
  performance: number
  availability: number
  cost: number
  capacity: number
  efficiency: number
}

export interface ImplementationPlan {
  phases: ImplementationPhase[]
  resources: string[]
  timeline: string
  milestones: string[]
  rollback: string[]
}

export interface ImplementationPhase {
  name: string
  description: string
  duration: string
  dependencies: string[]
  deliverables: string[]
  risks: string[]
}

export interface CostEstimate {
  initial: number
  recurring: number
  savings: number
  roi: number
  payback: string
  assumptions: string[]
}

export interface CapacityThreshold {
  id: string
  resource: string
  metric: string
  warning: number
  critical: number
  action: ThresholdAction
  enabled: boolean
  notifications: string[]
}

export interface ThresholdAction {
  type: ActionType
  parameters: Record<string, any>
  enabled: boolean
  cooldown: number
}

export interface PerformanceMetrics {
  response: ResponseMetrics
  throughput: ThroughputMetrics
  availability: AvailabilityMetrics
  reliability: ReliabilityMetrics
  efficiency: EfficiencyMetrics
  baselines: PerformanceBaseline[]
}

export interface ResponseMetrics {
  average: number
  median: number
  p95: number
  p99: number
  minimum: number
  maximum: number
  distribution: ResponseDistribution
}

export interface ResponseDistribution {
  fast: number
  acceptable: number
  slow: number
  timeout: number
}

export interface AvailabilityMetrics {
  uptime: number
  downtime: number
  availability: number
  mtbf: number
  mttr: number
  incidents: IncidentSummary[]
}

export interface IncidentSummary {
  id: string
  type: string
  severity: string
  startTime: string
  endTime?: string
  duration?: number
  impact: string
  cause: string
  resolution: string
}

export interface ReliabilityMetrics {
  errorRate: number
  successRate: number
  failureRate: number
  recovery: RecoveryMetrics
  stability: StabilityMetrics
}

export interface RecoveryMetrics {
  time: number
  success: number
  automatic: number
  manual: number
}

export interface StabilityMetrics {
  variance: number
  consistency: number
  predictability: number
  resilience: number
}

export interface EfficiencyMetrics {
  resourceUtilization: number
  throughputPerResource: number
  costEfficiency: number
  energyEfficiency: number
  optimization: OptimizationMetrics
}

export interface OptimizationMetrics {
  potential: number
  achieved: number
  opportunities: OptimizationOpportunity[]
}

export interface OptimizationOpportunity {
  area: string
  potential: number
  effort: string
  impact: string
  recommendation: string
}

export interface PerformanceBaseline {
  id: string
  name: string
  description: string
  metrics: BaselineMetrics
  established: string
  lastUpdated: string
  valid: boolean
}

export interface BaselineMetrics {
  response: number
  throughput: number
  utilization: number
  availability: number
  errorRate: number
}

export interface ResourceAlert {
  id: string
  resource: string
  type: AlertType
  severity: AlertSeverity
  status: AlertStatus
  title: string
  description: string
  metric: string
  threshold: number
  currentValue: number
  triggeredAt: string
  acknowledgedAt?: string
  resolvedAt?: string
  assignee?: string
  actions: AlertAction[]
  escalation: EscalationRule[]
  metadata: Record<string, any>
}

export interface AlertAction {
  type: ActionType
  description: string
  executed: boolean
  executedAt?: string
  result?: string
  error?: string
}

export interface EscalationRule {
  level: number
  delay: number
  recipients: string[]
  actions: ActionType[]
  conditions: string[]
}

export interface ResourceTrend {
  resource: string
  metric: string
  period: string
  values: TrendValue[]
  direction: TrendDirection
  strength: number
  seasonality: boolean
  anomalies: Anomaly[]
}

export interface TrendValue {
  timestamp: string
  value: number
  predicted?: number
  anomaly?: boolean
}

export interface Anomaly {
  timestamp: string
  value: number
  expected: number
  deviation: number
  severity: AnomalySeverity
  type: AnomalyType
  description: string
}

// Enums and Union Types
export type NodeType = 'build-server' | 'qemu-host' | 'physical-board' | 'network-device' | 'storage-device' | 'compute-node'
export type NodeStatus = 'online' | 'offline' | 'maintenance' | 'error' | 'unknown'
export type StorageType = 'hdd' | 'ssd' | 'nvme' | 'network' | 'tape' | 'optical'
export type StorageHealth = 'healthy' | 'warning' | 'critical' | 'failed' | 'unknown'
export type HealthStatus = 'healthy' | 'warning' | 'critical' | 'unknown'
export type IssueSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type IssueType = 'hardware' | 'software' | 'network' | 'performance' | 'security' | 'configuration'
export type MaintenanceType = 'scheduled' | 'emergency' | 'preventive' | 'corrective'
export type MaintenanceImpact = 'none' | 'low' | 'medium' | 'high' | 'critical'
export type MaintenanceStatus = 'scheduled' | 'in-progress' | 'completed' | 'cancelled' | 'failed'
export type BoardStatusType = 'available' | 'in-use' | 'maintenance' | 'offline' | 'error'
export type ConnectionType = 'ssh' | 'serial' | 'network' | 'usb' | 'jtag'
export type ConnectionStatus = 'connected' | 'disconnected' | 'error' | 'timeout'
export type TestStatus = 'running' | 'passed' | 'failed' | 'cancelled' | 'error'
export type NetworkDeviceType = 'switch' | 'router' | 'firewall' | 'load-balancer' | 'access-point'
export type DeviceStatus = 'up' | 'down' | 'warning' | 'critical' | 'maintenance'
export type ResourceType = 'cpu' | 'memory' | 'storage' | 'network' | 'gpu' | 'custom'
export type TrendDirection = 'increasing' | 'decreasing' | 'stable' | 'volatile'
export type BottleneckType = 'cpu' | 'memory' | 'storage' | 'network' | 'application' | 'database'
export type BottleneckSeverity = 'critical' | 'high' | 'medium' | 'low'
export type ForecastHorizon = 'short' | 'medium' | 'long'
export type RecommendationType = 'scale-up' | 'scale-out' | 'optimize' | 'replace' | 'migrate'
export type RecommendationPriority = 'critical' | 'high' | 'medium' | 'low'
export type ActionType = 'scale' | 'alert' | 'restart' | 'migrate' | 'optimize' | 'backup'
export type AlertType = 'threshold' | 'anomaly' | 'trend' | 'health' | 'performance'
export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'suppressed'
export type AnomalySeverity = 'critical' | 'high' | 'medium' | 'low'
export type AnomalyType = 'spike' | 'drop' | 'trend' | 'pattern' | 'outlier'

// Service Interfaces
export interface ResourceMonitoringService {
  getResourceMetrics(filters?: ResourceFilters): Promise<ResourceMetrics>
  getInfrastructureMetrics(): Promise<InfrastructureMetrics>
  getCapacityMetrics(): Promise<CapacityMetrics>
  getPerformanceMetrics(): Promise<PerformanceMetrics>
  getResourceAlerts(filters?: AlertFilters): Promise<ResourceAlert[]>
  createResourceAlert(alert: Omit<ResourceAlert, 'id' | 'triggeredAt'>): Promise<ResourceAlert>
  acknowledgeAlert(alertId: string): Promise<void>
  resolveAlert(alertId: string): Promise<void>
  getCapacityForecast(resource: string, horizon: ForecastHorizon): Promise<CapacityForecast>
  getCapacityRecommendations(): Promise<CapacityRecommendation[]>
  updateCapacityThresholds(thresholds: CapacityThreshold[]): Promise<void>
  getResourceTrends(resource: string, period: string): Promise<ResourceTrend[]>
  detectAnomalies(resource: string, period: string): Promise<Anomaly[]>
  getPerformanceBaselines(): Promise<PerformanceBaseline[]>
  createPerformanceBaseline(baseline: Omit<PerformanceBaseline, 'id' | 'established'>): Promise<PerformanceBaseline>
  updatePerformanceBaseline(baselineId: string, updates: Partial<PerformanceBaseline>): Promise<PerformanceBaseline>
}

export interface ResourceFilters {
  nodeType?: NodeType[]
  status?: NodeStatus[]
  location?: string[]
  tags?: string[]
  search?: string
  dateRange?: {
    start: string
    end: string
  }
}

export interface AlertFilters {
  resource?: string[]
  type?: AlertType[]
  severity?: AlertSeverity[]
  status?: AlertStatus[]
  assignee?: string
  dateRange?: {
    start: string
    end: string
  }
}

// Constants
export const NODE_TYPES: NodeType[] = ['build-server', 'qemu-host', 'physical-board', 'network-device', 'storage-device', 'compute-node']
export const NODE_STATUSES: NodeStatus[] = ['online', 'offline', 'maintenance', 'error', 'unknown']
export const RESOURCE_TYPES: ResourceType[] = ['cpu', 'memory', 'storage', 'network', 'gpu', 'custom']
export const ALERT_SEVERITIES: AlertSeverity[] = ['critical', 'high', 'medium', 'low', 'info']

export const DEFAULT_CAPACITY_THRESHOLDS = {
  cpu: { warning: 80, critical: 95 },
  memory: { warning: 85, critical: 95 },
  storage: { warning: 80, critical: 90 },
  network: { warning: 70, critical: 85 }
} as const

export const SEVERITY_COLORS = {
  critical: '#ff4d4f',
  high: '#ff7a45',
  medium: '#ffa940',
  low: '#52c41a',
  info: '#1890ff'
} as const

export const STATUS_COLORS = {
  online: 'green',
  offline: 'red',
  maintenance: 'orange',
  error: 'red',
  unknown: 'gray'
} as const