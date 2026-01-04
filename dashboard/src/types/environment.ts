/**
 * TypeScript interfaces for Environment Allocation UI
 */

export interface EnvironmentAllocationDashboardProps {
  planId?: string
  autoRefresh?: boolean
  refreshInterval?: number
}

export interface EnvironmentAllocationState {
  environments: Environment[]
  allocationQueue: AllocationRequest[]
  resourceUtilization: ResourceMetrics[]
  allocationHistory: AllocationEvent[]
  selectedEnvironment?: string
  capacityMetrics?: CapacityMetrics
}

export interface Environment {
  id: string
  type: EnvironmentType
  status: EnvironmentStatus
  architecture: string
  assignedTests: string[]
  resources: ResourceUsage
  health: EnvironmentHealth
  metadata?: EnvironmentMetadata
  createdAt?: Date
  lastUpdated?: Date
}

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

export interface ResourceUsage {
  cpu: number        // Percentage 0-100
  memory: number     // Percentage 0-100
  disk: number       // Percentage 0-100
  network?: NetworkMetrics
}

export interface NetworkMetrics {
  bytesIn: number
  bytesOut: number
  packetsIn: number
  packetsOut: number
}

export interface EnvironmentMetadata {
  [key: string]: any
}

export interface AllocationRequest {
  id: string
  testId: string
  requirements: HardwareRequirements
  priority: number
  submittedAt: Date
  estimatedStartTime?: Date
  status: AllocationStatus
}

export enum AllocationStatus {
  PENDING = 'pending',
  ALLOCATED = 'allocated',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export interface HardwareRequirements {
  architecture: string
  minMemoryMB: number
  minCpuCores: number
  requiredFeatures: string[]
  preferredEnvironmentType?: EnvironmentType
  isolationLevel: 'none' | 'process' | 'container' | 'vm'
}

export interface AllocationPreferences {
  environmentType?: EnvironmentType
  architecture?: string
  maxWaitTime?: number
  allowSharedEnvironment: boolean
  requireDedicatedResources: boolean
}

export interface AllocationEvent {
  id: string
  type: 'allocated' | 'deallocated' | 'failed' | 'queued'
  environmentId: string
  testId?: string
  timestamp: Date
  metadata: Record<string, any>
}

export interface ResourceMetrics {
  timestamp: Date
  environmentId: string
  cpu: {
    usage: number
    cores: number
    frequency: number
  }
  memory: {
    used: number
    total: number
    available: number
  }
  disk: {
    used: number
    total: number
    iops: number
  }
  network: {
    bytesIn: number
    bytesOut: number
    packetsIn: number
    packetsOut: number
  }
}

export interface CapacityMetrics {
  totalCapacity: number
  usedCapacity: number
  availableCapacity: number
  utilizationRate?: number
  queueLength?: number
}

export interface EnvironmentAction {
  type: 'reset' | 'maintenance' | 'offline' | 'cleanup' | 'priority'
  parameters?: Record<string, any>
}

export interface EnvironmentFilter {
  status?: EnvironmentStatus[]
  type?: EnvironmentType[]
  architecture?: string[]
  health?: EnvironmentHealth[]
  assignedTests?: string[]
}

export interface TimeRange {
  start: Date
  end: Date
}

export interface ResourceMetric {
  name: string
  type: 'cpu' | 'memory' | 'disk' | 'network'
  unit: string
}

// API Response Types
export interface EnvironmentAllocationResponse {
  environments: Environment[]
  queue: AllocationRequest[]
  resourceUtilization: ResourceMetrics[]
  history: AllocationEvent[]
  capacityMetrics: CapacityMetrics
}

export interface AllocationMetrics {
  totalAllocations: number
  successfulAllocations: number
  failedAllocations: number
  averageAllocationTime: number
  queueLength: number
  utilizationRate: number
}