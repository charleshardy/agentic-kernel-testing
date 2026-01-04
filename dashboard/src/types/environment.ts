/**
 * TypeScript interfaces for Environment Allocation UI data models
 * Based on the design document specifications
 */

export enum EnvironmentType {
  QEMU_X86 = 'qemu-x86',
  QEMU_ARM = 'qemu-arm',
  DOCKER = 'docker',
  PHYSICAL = 'physical',
  CONTAINER = 'container'
}

export enum EnvironmentStatus {
  ALLOCATING = 'allocating',
  READY = 'ready',
  RUNNING = 'running',
  CLEANUP = 'cleanup',
  MAINTENANCE = 'maintenance',
  ERROR = 'error',
  OFFLINE = 'offline'
}

export enum EnvironmentHealth {
  HEALTHY = 'healthy',
  DEGRADED = 'degraded',
  UNHEALTHY = 'unhealthy',
  UNKNOWN = 'unknown'
}

export enum AllocationStatus {
  QUEUED = 'queued',
  ALLOCATING = 'allocating',
  ALLOCATED = 'allocated',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export enum ProvisioningStage {
  INITIALIZING = 'initializing',
  ALLOCATING_RESOURCES = 'allocating_resources',
  CREATING_ENVIRONMENT = 'creating_environment',
  CONFIGURING_NETWORK = 'configuring_network',
  INSTALLING_SOFTWARE = 'installing_software',
  RUNNING_HEALTH_CHECKS = 'running_health_checks',
  FINALIZING = 'finalizing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export interface ResourceUsage {
  cpu: number;        // Percentage 0-100
  memory: number;     // Percentage 0-100
  disk: number;       // Percentage 0-100
  network: NetworkMetrics;
}

export interface NetworkMetrics {
  bytesIn: number;
  bytesOut: number;
  packetsIn: number;
  packetsOut: number;
}

export interface EnvironmentMetadata {
  kernelVersion?: string;
  ipAddress?: string;
  sshCredentials?: Record<string, any>;
  provisionedAt?: string;
  lastHealthCheck?: string;
  [key: string]: any;
}

export interface Environment {
  id: string;
  type: EnvironmentType;
  status: EnvironmentStatus;
  architecture: string;
  assignedTests: string[];
  resources: ResourceUsage;
  health: EnvironmentHealth;
  metadata: EnvironmentMetadata;
  createdAt: string;
  updatedAt: string;
  provisioningProgress?: ProvisioningProgress;
}

export interface HardwareRequirements {
  architecture: string;
  minMemoryMB: number;
  minCpuCores: number;
  requiredFeatures: string[];
  preferredEnvironmentType?: EnvironmentType;
  isolationLevel: 'none' | 'process' | 'container' | 'vm';
}

export interface AllocationPreferences {
  environmentType?: EnvironmentType;
  architecture?: string;
  maxWaitTime?: number;
  allowSharedEnvironment: boolean;
  requireDedicatedResources: boolean;
}

export interface AllocationRequest {
  id: string;
  testId: string;
  requirements: HardwareRequirements;
  preferences?: AllocationPreferences;
  priority: number;
  submittedAt: Date;
  estimatedStartTime?: Date;
  status: AllocationStatus;
}

export interface AllocationEvent {
  id: string;
  type: 'allocated' | 'deallocated' | 'failed' | 'queued';
  environmentId: string;
  testId?: string;
  timestamp: Date;
  metadata: Record<string, any>;
}

export interface AllocationMetrics {
  totalAllocations: number;
  successfulAllocations: number;
  failedAllocations: number;
  averageAllocationTime: number;
  queueLength: number;
  utilizationRate: number;
}

export interface ProvisioningProgress {
  currentStage: ProvisioningStage;
  progressPercentage: number;
  estimatedCompletion?: Date;
  remainingTimeSeconds?: number;
  stageDetails: {
    stageName: string;
    stageDescription: string;
    stageIndex: number;
    totalStages: number;
  };
  startedAt: Date;
  lastUpdated: Date;
}

export interface CapacityMetrics {
  totalEnvironments: number;
  readyEnvironments: number;
  idleEnvironments: number;
  runningEnvironments: number;
  offlineEnvironments: number;
  errorEnvironments: number;
  averageCpuUtilization: number;
  averageMemoryUtilization: number;
  averageDiskUtilization: number;
  pendingRequestsCount: number;
  allocationLikelihood: Record<string, number>;
  capacityPercentage: number;
  utilizationPercentage: number;
}

export interface AllocationLikelihood {
  requestId: string;
  likelihood: number;
  reasoning: string[];
  compatibleEnvironments: number;
  estimatedWaitTime: number;
}

export interface ResourceMetrics {
  timestamp: Date;
  environmentId: string;
  cpu: {
    usage: number;
    cores: number;
    frequency: number;
  };
  memory: {
    used: number;
    total: number;
    available: number;
  };
  disk: {
    used: number;
    total: number;
    iops: number;
  };
  network: {
    bytesIn: number;
    bytesOut: number;
    packetsIn: number;
    packetsOut: number;
  };
}

// Component Props Interfaces
export interface EnvironmentAllocationDashboardProps {
  planId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export interface EnvironmentAllocationState {
  environments: Environment[];
  allocationQueue: AllocationRequest[];
  resourceUtilization: ResourceMetrics[];
  allocationHistory: AllocationEvent[];
  selectedEnvironment?: string;
  capacityMetrics?: CapacityMetrics;
}

export interface EnvironmentTableProps {
  environments: Environment[];
  onEnvironmentSelect: (envId: string) => void;
  onEnvironmentAction: (envId: string, action: EnvironmentAction) => void;
  showResourceUsage: boolean;
  filterOptions: EnvironmentFilter;
}

export interface EnvironmentAction {
  type: 'reset' | 'maintenance' | 'offline' | 'cleanup';
  parameters?: Record<string, any>;
}

export interface EnvironmentFilter {
  status?: EnvironmentStatus[];
  type?: EnvironmentType[];
  architecture?: string[];
  health?: EnvironmentHealth[];
}

export interface ResourceUtilizationChartsProps {
  environments: Environment[];
  timeRange: TimeRange;
  chartType: 'realtime' | 'historical';
  metrics: ResourceMetric[];
}

export interface TimeRange {
  start: Date;
  end: Date;
}

export interface ResourceMetric {
  name: string;
  type: 'cpu' | 'memory' | 'disk' | 'network';
  unit: string;
}

export interface AllocationQueueViewerProps {
  queue: AllocationRequest[];
  estimatedWaitTimes: Map<string, number>;
  onPriorityChange: (requestId: string, priority: number) => void;
}

// API Response Types
export interface EnvironmentAllocationResponse {
  environments: Environment[];
  queue: AllocationRequest[];
  metrics: AllocationMetrics;
  history: AllocationEvent[];
  capacityMetrics: CapacityMetrics;
}

export interface AllocationQueueResponse {
  queue: AllocationRequest[];
  estimatedWaitTimes: Record<string, number>;
  totalWaitTime: number;
}

export interface AllocationHistoryResponse {
  events: AllocationEvent[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}