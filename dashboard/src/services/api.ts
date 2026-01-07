import axios, { AxiosInstance, AxiosResponse } from 'axios'

export interface APIResponse<T = any> {
  success: boolean
  message: string
  data?: T
  errors?: string[]
  timestamp: string
}

export interface TestCase {
  id: string
  name: string
  description: string
  test_type: string
  target_subsystem: string
  code_paths: string[]
  execution_time_estimate: number
  required_hardware?: any
  test_script: string
  expected_outcome?: any
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

export interface EnhancedTestCase extends TestCase {
  generation_info?: {
    method: 'manual' | 'ai_diff' | 'ai_function' | 'ai_kernel_driver'
    source_data: any
    generated_at: string
    ai_model?: string
    generation_params?: Record<string, any>
    driver_files?: Record<string, string>
  }
  execution_status?: 'never_run' | 'running' | 'completed' | 'failed'
  last_execution_at?: string
  tags?: string[]
  is_favorite?: boolean
  requires_root?: boolean
  kernel_module?: boolean
  driver_files?: Record<string, string>
}

export interface TestCaseFilters {
  test_type?: string
  subsystem?: string
  status?: string
  generation_method?: 'manual' | 'ai_diff' | 'ai_function' | 'ai_kernel_driver'
  date_range?: [string, string]
  search?: string
}

export interface TestListResponse {
  tests: EnhancedTestCase[]
  pagination: {
    page: number
    page_size: number
    total_items: number
    total_pages: number
    has_next: boolean
    has_prev: boolean
  }
  filters_applied: TestCaseFilters
}

export interface BulkOperationRequest {
  operation: 'delete' | 'execute' | 'update' | 'tag'
  test_ids: string[]
  data?: Record<string, any>
}

export interface BulkOperationResponse {
  success: boolean
  results: Array<{
    test_id: string
    success: boolean
    message?: string
    error?: string
  }>
  summary: {
    total: number
    successful: number
    failed: number
  }
}

export interface TestResult {
  test_id: string
  status: 'passed' | 'failed' | 'running' | 'pending' | 'skipped' | 'timeout' | 'error'
  execution_time: number
  environment: Record<string, any>
  artifacts: Record<string, any>
  coverage_data?: CoverageData
  failure_info?: any
  timestamp: string
}

export interface CoverageData {
  line_coverage: number
  branch_coverage: number
  function_coverage: number
  covered_lines: string[]
  uncovered_lines: string[]
  coverage_gaps: any[]
  report_url?: string
}

export interface SystemMetrics {
  active_tests: number
  queued_tests: number
  available_environments: number
  total_environments: number
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  network_io: Record<string, number>
}

// Environment Allocation Interfaces
export interface EnvironmentAllocationData {
  environments: Environment[]
  queue: AllocationRequest[]
  metrics: AllocationMetrics
  history: AllocationEvent[]
}

export interface Environment {
  id: string
  type: string
  status: string
  architecture: string
  assigned_tests: string[]
  resources: ResourceUsage
  health: string
  metadata: EnvironmentMetadata
  created_at: string
  updated_at: string
}

export interface ResourceUsage {
  cpu: number
  memory: number
  disk: number
  network: NetworkMetrics
}

export interface NetworkMetrics {
  bytes_in: number
  bytes_out: number
  packets_in: number
  packets_out: number
}

export interface EnvironmentMetadata {
  kernel_version?: string
  ip_address?: string
  ssh_credentials?: Record<string, any>
  provisioned_at?: string
  last_health_check?: string
  additional_metadata: Record<string, any>
}

export interface AllocationRequest {
  id: string
  test_id: string
  requirements: HardwareRequirements
  preferences?: AllocationPreferences
  priority: number
  submitted_at: string
  estimated_start_time?: string
  status: string
}

export interface HardwareRequirements {
  architecture: string
  min_memory_mb: number
  min_cpu_cores: number
  required_features: string[]
  preferred_environment_type?: string
  isolation_level: string
}

export interface AllocationPreferences {
  environment_type?: string
  architecture?: string
  max_wait_time?: number
  allow_shared_environment: boolean
  require_dedicated_resources: boolean
}

export interface AllocationEvent {
  id: string
  type: string
  environment_id: string
  test_id?: string
  timestamp: string
  metadata: Record<string, any>
}

export interface AllocationMetrics {
  total_allocations: number
  successful_allocations: number
  failed_allocations: number
  average_allocation_time: number
  queue_length: number
  utilization_rate: number
}

export interface HealthStatus {
  status: string
  version: string
  uptime: number
  components: Record<string, any>
  metrics: Record<string, any>
  timestamp: string
}

export interface ExecutionPlanStatus {
  plan_id: string
  submission_id: string
  overall_status: string
  total_tests: number
  completed_tests: number
  failed_tests: number
  progress: number
  test_statuses: TestExecutionStatus[]
  started_at?: string
  completed_at?: string
  estimated_completion?: string
}

export interface TestExecutionStatus {
  test_id: string
  status: string
  progress: number
  environment_id?: string
  started_at?: string
  estimated_completion?: string
  message: string
}

class APIService {
  private client: AxiosInstance

  constructor() {
    // Determine the correct base URL based on environment
    let baseURL: string
    
    // Check if we're running in development (typical indicators)
    const isDevelopment = 
      process.env.NODE_ENV === 'development' ||
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1' ||
      window.location.port === '3000'
    
    if (isDevelopment) {
      // Use Vite proxy in development (now working correctly)
      baseURL = '/api/v1'  // Proxy URL
      console.log('🔧 API Service: Using Vite proxy for development:', baseURL)
    } else {
      // In production, use direct URL
      baseURL = 'http://localhost:8000/api/v1'
      console.log('🔧 API Service: Using direct URL for production:', baseURL)
    }
      
    this.client = axios.create({
      baseURL,
      timeout: 60000, // Increased to 60 seconds
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add a request interceptor to log API calls in development
    if (isDevelopment) {
      this.client.interceptors.request.use(
        (config) => {
          console.log('🌐 API Request:', config.method?.toUpperCase(), config.url, config.params)
          return config
        },
        (error) => {
          console.error('🚨 API Request Error:', error)
          return Promise.reject(error)
        }
      )
      
      this.client.interceptors.response.use(
        (response) => {
          console.log('✅ API Response:', response.status, response.config.url)
          return response
        },
        (error) => {
          console.error('❌ API Response Error:', error.response?.status, error.config?.url, error.message)
          return Promise.reject(error)
        }
      )
    }

    // Add authentication interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        
        if (isDevelopment) {
          console.log('🌐 API Request:', config.method?.toUpperCase(), config.url, config.params)
        }
        return config
      },
      (error) => {
        console.error('🚨 API Request Error:', error)
        return Promise.reject(error)
      }
    )

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        if (isDevelopment) {
          console.log('✅ API Response:', response.status, response.config.url)
        }
        return response
      },
      (error) => {
        console.error('❌ API Response Error:', {
          status: error.response?.status,
          url: error.config?.url,
          message: error.message,
          data: error.response?.data
        })
        
        // Handle authentication errors
        if (error.response?.status === 401) {
          console.log('🔑 Authentication required for:', error.config?.url)
          localStorage.removeItem('auth_token')
          // Let individual methods handle retry logic
        }
        
        return Promise.reject(error)
      }
    )

    // Initialize demo authentication
    this.initializeDemoAuth()
  }

  // Health and system status
  async getHealth(): Promise<HealthStatus> {
    const response: AxiosResponse<APIResponse<HealthStatus>> = await this.client.get('/health')
    return response.data.data!
  }

  async getSystemMetrics(): Promise<SystemMetrics> {
    const response: AxiosResponse<APIResponse<SystemMetrics>> = await this.client.get('/health/metrics')
    return response.data.data!
  }

  // Test management
  async getTests(params?: {
    page?: number
    page_size?: number
    status?: string
    test_type?: string
    subsystem?: string
    generation_method?: string
    date_range?: [string, string]
    search?: string
  }): Promise<TestListResponse> {
    const queryParams: Record<string, any> = { ...params }
    
    // Handle date range formatting
    if (params?.date_range) {
      queryParams.start_date = params.date_range[0]
      queryParams.end_date = params.date_range[1]
      delete queryParams.date_range
    }
    
    try {
      const response: AxiosResponse<APIResponse<TestListResponse>> = await this.client.get('/tests', { 
        params: queryParams 
      })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        // Try to get demo token and retry
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<TestListResponse>> = await this.client.get('/tests', { 
          params: queryParams 
        })
        return response.data.data!
      }
      throw error
    }
  }

  async getTestById(testId: string): Promise<EnhancedTestCase> {
    try {
      const response: AxiosResponse<APIResponse<EnhancedTestCase>> = await this.client.get(`/tests/${testId}`)
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        // Try to get demo token and retry
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<EnhancedTestCase>> = await this.client.get(`/tests/${testId}`)
        return response.data.data!
      }
      throw error
    }
  }

  async updateTest(testId: string, updates: Partial<TestCase>): Promise<EnhancedTestCase> {
    try {
      const response: AxiosResponse<APIResponse<EnhancedTestCase>> = await this.client.put(`/tests/${testId}`, updates)
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<EnhancedTestCase>> = await this.client.put(`/tests/${testId}`, updates)
        return response.data.data!
      }
      throw error
    }
  }

  async deleteTest(testId: string): Promise<{ success: boolean, message: string }> {
    try {
      const response: AxiosResponse<APIResponse<{ success: boolean, message: string }>> = await this.client.delete(`/tests/${testId}`)
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<{ success: boolean, message: string }>> = await this.client.delete(`/tests/${testId}`)
        return response.data.data!
      }
      throw error
    }
  }

  async executeTest(testId: string, options?: {
    environment_preference?: string
    priority?: number
  }): Promise<{ execution_plan_id: string, estimated_completion: string }> {
    try {
      const response: AxiosResponse<APIResponse<{ execution_plan_id: string, estimated_completion: string }>> = 
        await this.client.post(`/tests/${testId}/execute`, options || {})
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<{ execution_plan_id: string, estimated_completion: string }>> = 
          await this.client.post(`/tests/${testId}/execute`, options || {})
        return response.data.data!
      }
      throw error
    }
  }

  async bulkOperations(request: BulkOperationRequest): Promise<BulkOperationResponse> {
    try {
      const response: AxiosResponse<APIResponse<BulkOperationResponse>> = 
        await this.client.post('/tests/bulk-operations', request)
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<BulkOperationResponse>> = 
          await this.client.post('/tests/bulk-operations', request)
        return response.data.data!
      }
      throw error
    }
  }

  async submitTests(tests: any[]): Promise<{ submission_id: string, test_case_ids: string[] }> {
    const response: AxiosResponse<APIResponse> = await this.client.post('/tests/submit', {
      test_cases: tests,
      priority: 5
    })
    return response.data.data!
  }

  // Test execution and status
  async getExecutionStatus(planId: string): Promise<ExecutionPlanStatus> {
    const response: AxiosResponse<APIResponse<ExecutionPlanStatus>> = await this.client.get(`/execution/${planId}/status`)
    return response.data.data!
  }

  async getActiveExecutions(): Promise<ExecutionPlanStatus[]> {
    try {
      console.log('🔍 Fetching active executions...')
      // Add cache-busting parameter to prevent stale data
      const cacheBuster = Date.now()
      const response: AxiosResponse<APIResponse<{executions: ExecutionPlanStatus[]}>> = await this.client.get(`/execution/active?_t=${cacheBuster}`)
      console.log('✅ Active executions response:', response.data)
      const executions = response.data.data?.executions || []
      console.log(`📊 Found ${executions.length} active executions:`, executions)
      return executions
    } catch (error: any) {
      console.error('❌ Error fetching active executions:', error)
      if (error.response?.status === 401) {
        console.log('🔑 Authentication error, trying to get new token...')
        await this.ensureDemoToken()
        const cacheBuster = Date.now()
        const response: AxiosResponse<APIResponse<{executions: ExecutionPlanStatus[]}>> = await this.client.get(`/execution/active?_t=${cacheBuster}`)
        console.log('✅ Retry successful:', response.data)
        return response.data.data?.executions || []
      }
      throw error
    }
  }

  async startTestExecution(testIds: string[], options?: {
    priority?: number
    environment_preference?: string
  }): Promise<{ execution_plan_id: string, submission_id: string, status: string }> {
    const response: AxiosResponse<APIResponse> = await this.client.post('/execution/start', {
      test_ids: testIds,
      priority: options?.priority || 5,
      environment_preference: options?.environment_preference
    })
    return response.data.data!
  }

  async cancelExecution(planId: string): Promise<{ success: boolean, message: string }> {
    const response: AxiosResponse<APIResponse> = await this.client.post(`/execution/${planId}/cancel`)
    return response.data.data!
  }

  async startExecution(planId: string): Promise<{ success: boolean, message: string }> {
    const response: AxiosResponse<APIResponse> = await this.client.post(`/execution/${planId}/start`)
    return response.data.data!
  }

  async getExecutionMetrics(): Promise<any> {
    const response: AxiosResponse<APIResponse> = await this.client.get('/execution/metrics')
    return response.data.data!
  }

  // Test results
  async getTestResults(params?: {
    page?: number
    page_size?: number
    status?: string
    start_date?: string
    end_date?: string
  }): Promise<{ results: TestResult[], total: number }> {
    const response: AxiosResponse<APIResponse> = await this.client.get('/results', { params })
    return response.data.data!
  }

  async getTestResult(testId: string): Promise<TestResult> {
    const response: AxiosResponse<APIResponse<TestResult>> = await this.client.get(`/results/${testId}`)
    return response.data.data!
  }

  // Coverage analysis
  async getCoverageReport(testId?: string): Promise<CoverageData> {
    const url = testId ? `/results/${testId}/coverage` : '/results/coverage/aggregate'
    const response: AxiosResponse<APIResponse<CoverageData>> = await this.client.get(url)
    return response.data.data!
  }

  async getCoverageTrends(days: number = 30): Promise<any[]> {
    const response: AxiosResponse<APIResponse<any[]>> = await this.client.get('/results/coverage/trends', {
      params: { days }
    })
    return response.data.data!
  }

  // Performance monitoring
  async getPerformanceMetrics(params?: {
    start_date?: string
    end_date?: string
    metric_type?: string
  }): Promise<any[]> {
    const response: AxiosResponse<APIResponse<any[]>> = await this.client.get('/results/performance', { params })
    return response.data.data!
  }

  async getPerformanceTrends(days: number = 30): Promise<any[]> {
    const response: AxiosResponse<APIResponse<any[]>> = await this.client.get('/results/performance/trends', {
      params: { days }
    })
    return response.data.data!
  }

  // Environments
  async getEnvironments(): Promise<any[]> {
    try {
      const response: AxiosResponse<APIResponse<any[]>> = await this.client.get('/environments')
      console.log('🔍 getEnvironments API response:', response.data)
      
      // Ensure we always return an array
      const data = response.data.data
      if (Array.isArray(data)) {
        return data
      } else {
        console.log('⚠️ API returned non-array data, using mock data instead')
        return this.getMockEnvironments()
      }
    } catch (error: any) {
      console.log('❌ getEnvironments API error:', error.message)
      
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any[]>> = await this.client.get('/environments')
        const data = response.data.data
        if (Array.isArray(data)) {
          return data
        }
      }
      
      // Return mock data for development
      console.log('🔧 Returning mock environments data')
      return this.getMockEnvironments()
    }
  }

  private getMockEnvironments(): any[] {
    return [
      {
        id: 'qemu-vm-x86-001',
        name: 'QEMU x86_64 VM #1',
        type: 'qemu-x86',
        status: 'ready',
        config: {
          architecture: 'x86_64',
          cpu_model: 'Intel Core i7',
          memory_mb: 4096,
          disk_gb: 20
        }
      },
      {
        id: 'qemu-vm-arm64-002',
        name: 'QEMU ARM64 VM #2',
        type: 'qemu-arm',
        status: 'busy',
        config: {
          architecture: 'ARM64',
          cpu_model: 'ARM Cortex-A78',
          memory_mb: 8192,
          disk_gb: 40
        }
      },
      {
        id: 'physical-board-001',
        name: 'Physical ARM Board #1',
        type: 'physical',
        status: 'ready',
        config: {
          architecture: 'ARM64',
          cpu_model: 'Raspberry Pi 4',
          memory_mb: 4096,
          disk_gb: 32
        }
      }
    ]
  }

  async getEnvironmentStatus(envId: string): Promise<any> {
    const response: AxiosResponse<APIResponse> = await this.client.get(`/environments/${envId}/status`)
    return response.data.data!
  }

  // Environment Management API endpoints
  async getEnvironmentManagement(): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get('/environments/allocation')
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get('/environments/allocation')
        return response.data.data!
      }
      
      // Return mock data with capacity metrics for development
      console.log('🔧 Returning mock environment allocation data with capacity metrics')
      return this.generateMockEnvironmentAllocationData()
    }
  }

  private generateMockEnvironmentAllocationData(): any {
    const now = new Date()
    
    // Generate mock environments with provisioning progress
    const environments = [
      {
        id: 'env-001-qemu-x86',
        type: 'qemu-x86',
        status: 'ready',
        architecture: 'x86_64',
        assignedTests: [],
        resources: { cpu: 15, memory: 25, disk: 30, network: { bytesIn: 1024, bytesOut: 2048, packetsIn: 100, packetsOut: 150 } },
        health: 'healthy',
        metadata: { kernelVersion: '6.1.0', ipAddress: '192.168.1.10', lastHealthCheck: now.toISOString() },
        createdAt: new Date(now.getTime() - 3600000).toISOString(),
        updatedAt: now.toISOString()
      },
      {
        id: 'env-002-qemu-arm',
        type: 'qemu-arm',
        status: 'running',
        architecture: 'arm64',
        assignedTests: ['test-001', 'test-002'],
        resources: { cpu: 75, memory: 80, disk: 45, network: { bytesIn: 5120, bytesOut: 8192, packetsIn: 500, packetsOut: 750 } },
        health: 'healthy',
        metadata: { kernelVersion: '6.1.0', ipAddress: '192.168.1.11', lastHealthCheck: now.toISOString() },
        createdAt: new Date(now.getTime() - 7200000).toISOString(),
        updatedAt: now.toISOString()
      },
      {
        id: 'env-003-docker',
        type: 'docker',
        status: 'allocating',
        architecture: 'x86_64',
        assignedTests: [],
        resources: { cpu: 5, memory: 10, disk: 15, network: { bytesIn: 512, bytesOut: 1024, packetsIn: 50, packetsOut: 75 } },
        health: 'unknown',
        metadata: { kernelVersion: null, ipAddress: null, lastHealthCheck: null },
        createdAt: new Date(now.getTime() - 300000).toISOString(),
        updatedAt: now.toISOString(),
        provisioningProgress: {
          currentStage: 'creating_environment',
          progressPercentage: 45,
          estimatedCompletion: new Date(now.getTime() + 600000),
          remainingTimeSeconds: 600,
          stageDetails: {
            stageName: 'Creating Environment',
            stageDescription: 'Currently creating environment',
            stageIndex: 2,
            totalStages: 8
          },
          startedAt: new Date(now.getTime() - 300000),
          lastUpdated: now
        }
      },
      {
        id: 'env-004-physical',
        type: 'physical',
        status: 'ready',
        architecture: 'x86_64',
        assignedTests: [],
        resources: { cpu: 20, memory: 35, disk: 50, network: { bytesIn: 2048, bytesOut: 4096, packetsIn: 200, packetsOut: 300 } },
        health: 'healthy',
        metadata: { kernelVersion: '6.1.0', ipAddress: '192.168.1.12', lastHealthCheck: now.toISOString() },
        createdAt: new Date(now.getTime() - 14400000).toISOString(),
        updatedAt: now.toISOString()
      },
      {
        id: 'env-005-qemu-x86',
        type: 'qemu-x86',
        status: 'error',
        architecture: 'x86_64',
        assignedTests: [],
        resources: { cpu: 0, memory: 0, disk: 0, network: { bytesIn: 0, bytesOut: 0, packetsIn: 0, packetsOut: 0 } },
        health: 'unhealthy',
        metadata: { kernelVersion: null, ipAddress: null, lastHealthCheck: new Date(now.getTime() - 1800000).toISOString() },
        createdAt: new Date(now.getTime() - 1800000).toISOString(),
        updatedAt: new Date(now.getTime() - 900000).toISOString()
      }
    ]

    // Generate mock allocation queue
    const queue = [
      {
        id: 'req-001',
        testId: 'test-003',
        requirements: { architecture: 'x86_64', minMemoryMB: 2048, minCpuCores: 2, requiredFeatures: [], isolationLevel: 'vm' },
        priority: 5,
        submittedAt: new Date(now.getTime() - 120000).toISOString(),
        estimatedStartTime: new Date(now.getTime() + 300000).toISOString(),
        status: 'queued'
      },
      {
        id: 'req-002',
        testId: 'test-004',
        requirements: { architecture: 'arm64', minMemoryMB: 1024, minCpuCores: 1, requiredFeatures: [], isolationLevel: 'container' },
        priority: 3,
        submittedAt: new Date(now.getTime() - 60000).toISOString(),
        estimatedStartTime: new Date(now.getTime() + 600000).toISOString(),
        status: 'queued'
      }
    ]

    // Calculate capacity metrics
    const totalEnvironments = environments.length
    const readyEnvironments = environments.filter(env => env.status === 'ready').length
    const idleEnvironments = environments.filter(env => env.status === 'ready' && env.assignedTests.length === 0).length
    const runningEnvironments = environments.filter(env => env.status === 'running').length
    const offlineEnvironments = environments.filter(env => env.status === 'offline').length
    const errorEnvironments = environments.filter(env => env.status === 'error').length

    const avgCpu = environments.reduce((sum, env) => sum + env.resources.cpu, 0) / totalEnvironments
    const avgMemory = environments.reduce((sum, env) => sum + env.resources.memory, 0) / totalEnvironments
    const avgDisk = environments.reduce((sum, env) => sum + env.resources.disk, 0) / totalEnvironments

    const capacityMetrics = {
      totalEnvironments,
      readyEnvironments,
      idleEnvironments,
      runningEnvironments,
      offlineEnvironments,
      errorEnvironments,
      averageCpuUtilization: Math.round(avgCpu),
      averageMemoryUtilization: Math.round(avgMemory),
      averageDiskUtilization: Math.round(avgDisk),
      pendingRequestsCount: queue.length,
      allocationLikelihood: {
        'req-001': 85,
        'req-002': 60
      },
      capacityPercentage: Math.round((readyEnvironments / totalEnvironments) * 100),
      utilizationPercentage: Math.round((avgCpu + avgMemory + avgDisk) / 3)
    }

    return {
      environments,
      queue,
      resourceUtilization: [],
      history: [],
      capacityMetrics
    }
  }

  async getEnvironmentQueue(): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get('/environments/allocation/queue')
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get('/environments/allocation/queue')
        return response.data.data!
      }
      throw error
    }
  }

  async getAllocationHistory(params?: {
    planId?: string
    environmentId?: string
    testId?: string
    eventTypes?: string[]
    environmentIds?: string[]
    testIds?: string[]
    startDate?: string
    endDate?: string
    search?: string
    limit?: number
  }): Promise<{ events: AllocationEvent[] }> {
    try {
      // Convert the params to match the backend API format
      const queryParams: Record<string, any> = {}
      
      if (params?.planId) queryParams.plan_id = params.planId
      if (params?.environmentId) queryParams.environment_id = params.environmentId
      if (params?.testId) queryParams.test_id = params.testId
      if (params?.eventTypes?.length) queryParams.event_types = params.eventTypes.join(',')
      if (params?.environmentIds?.length) queryParams.environment_ids = params.environmentIds.join(',')
      if (params?.testIds?.length) queryParams.test_ids = params.testIds.join(',')
      if (params?.startDate) queryParams.start_time = params.startDate
      if (params?.endDate) queryParams.end_time = params.endDate
      if (params?.search) queryParams.search = params.search
      if (params?.limit) queryParams.limit = params.limit

      const response: AxiosResponse<APIResponse<{ events: AllocationEvent[] }>> = 
        await this.client.get('/environments/allocation/history', { params: queryParams })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<{ events: AllocationEvent[] }>> = 
          await this.client.get('/environments/allocation/history', { params: queryParams })
        return response.data.data!
      }
      
      // Return mock data for development
      console.log('🔧 Returning mock allocation history data')
      return this.generateMockAllocationHistory(params)
    }
  }

  private generateMockAllocationHistory(params?: any): { events: AllocationEvent[] } {
    const events: AllocationEvent[] = []
    const eventTypes = ['allocated', 'deallocated', 'failed', 'queued']
    const environments = ['env-001-qemu-x86', 'env-002-qemu-arm', 'env-003-docker', 'env-004-physical']
    const tests = ['test-kernel-boot', 'test-network-stack', 'test-filesystem', 'test-memory-mgmt']
    
    for (let i = 0; i < 50; i++) {
      const timestamp = new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000) // Last 7 days
      const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)]
      const envId = environments[Math.floor(Math.random() * environments.length)]
      const testIdValue = tests[Math.floor(Math.random() * tests.length)]
      
      events.push({
        id: `event-${i}`,
        type: eventType,
        environment_id: eventType === 'queued' ? '' : envId,
        test_id: testIdValue,
        timestamp: timestamp.toISOString(),
        metadata: {
          duration: eventType === 'allocated' ? Math.floor(Math.random() * 300) + 30 : undefined,
          priority: eventType === 'queued' ? Math.floor(Math.random() * 10) + 1 : undefined,
          reason: eventType === 'deallocated' ? ['completed', 'timeout', 'cancelled'][Math.floor(Math.random() * 3)] : undefined,
          error: eventType === 'failed' ? ['timeout', 'resource_exhausted', 'configuration_error'][Math.floor(Math.random() * 3)] : undefined,
          queuePosition: eventType === 'queued' ? Math.floor(Math.random() * 20) + 1 : undefined,
          resourceUsage: eventType === 'allocated' ? {
            cpu: Math.floor(Math.random() * 100),
            memory: Math.floor(Math.random() * 100),
            disk: Math.floor(Math.random() * 100)
          } : undefined
        }
      })
    }
    
    return { events: events.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()) }
  }

  async getEnvironmentHistory(params?: {
    page?: number
    page_size?: number
    event_type?: string
    environment_id?: string
    test_id?: string
    start_time?: string
    end_time?: string
    sort_order?: string
  }): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get('/environments/allocation/history', { params })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get('/environments/allocation/history', { params })
        return response.data.data!
      }
      throw error
    }
  }

  async getAllocationStatistics(params?: {
    start_time?: string
    end_time?: string
  }): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get('/environments/allocation/statistics', { params })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get('/environments/allocation/statistics', { params })
        return response.data.data!
      }
      throw error
    }
  }

  async getAllocationCorrelations(environmentId: string, params?: {
    start_time?: string
    end_time?: string
  }): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get(`/environments/allocation/correlations/${environmentId}`, { params })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get(`/environments/allocation/correlations/${environmentId}`, { params })
        return response.data.data!
      }
      throw error
    }
  }

  async exportAllocationData(params?: {
    format?: 'csv' | 'json'
    start_time?: string
    end_time?: string
    event_type?: string
  }): Promise<Blob> {
    try {
      const response: AxiosResponse<Blob> = await this.client.get('/environments/allocation/export', { 
        params,
        responseType: 'blob'
      })
      return response.data
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<Blob> = await this.client.get('/environments/allocation/export', { 
          params,
          responseType: 'blob'
        })
        return response.data
      }
      throw error
    }
  }

  async createAllocationRequest(request: {
    test_id: string
    requirements: any
    preferences?: any
    priority?: number
  }): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.post('/environments/allocation/request', request)
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.post('/environments/allocation/request', request)
        return response.data.data!
      }
      throw error
    }
  }

  async cancelAllocationRequest(requestId: string): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.delete(`/environments/allocation/request/${requestId}`)
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.delete(`/environments/allocation/request/${requestId}`)
        return response.data.data!
      }
      throw error
    }
  }

  async performEnvironmentAction(envId: string, action: {
    type: 'reset' | 'maintenance' | 'offline' | 'cleanup'
    parameters?: Record<string, any>
  }): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.post(`/environments/${envId}/actions/${action.type}`, action.parameters || {})
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.post(`/environments/${envId}/actions/${action.type}`, action.parameters || {})
        return response.data.data!
      }
      throw error
    }
  }

  async performBulkEnvironmentAction(envIds: string[], action: {
    type: 'reset' | 'maintenance' | 'offline' | 'cleanup'
    parameters?: Record<string, any>
  }): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.post(`/environments/bulk-actions/${action.type}`, {
        environment_ids: envIds,
        parameters: action.parameters || {}
      })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.post(`/environments/bulk-actions/${action.type}`, {
          environment_ids: envIds,
          parameters: action.parameters || {}
        })
        return response.data.data!
      }
      throw error
    }
  }

  async createEnvironment(config: {
    type: string
    architecture: string
    cpuCores: number
    memoryMB: number
    storageGB: number
    enableKVM?: boolean
    enableNestedVirtualization?: boolean
    customKernelVersion?: string
    additionalFeatures?: string[]
  }): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.post('/environments', {
        architecture: config.architecture,
        cpu_model: `${config.cpuCores} cores`,
        memory_mb: config.memoryMB,
        storage_type: 'ssd',
        is_virtual: config.type !== 'physical',
        emulator: config.type.startsWith('qemu') ? 'qemu' : config.type === 'docker' ? 'docker' : null,
        additional_config: {
          storage_gb: config.storageGB,
          enable_kvm: config.enableKVM,
          enable_nested_virtualization: config.enableNestedVirtualization,
          custom_kernel_version: config.customKernelVersion,
          additional_features: config.additionalFeatures
        }
      })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.post('/environments', {
          architecture: config.architecture,
          cpu_model: `${config.cpuCores} cores`,
          memory_mb: config.memoryMB,
          storage_type: 'ssd',
          is_virtual: config.type !== 'physical',
          emulator: config.type.startsWith('qemu') ? 'qemu' : config.type === 'docker' ? 'docker' : null,
          additional_config: {
            storage_gb: config.storageGB,
            enable_kvm: config.enableKVM,
            enable_nested_virtualization: config.enableNestedVirtualization,
            custom_kernel_version: config.customKernelVersion,
            additional_features: config.additionalFeatures
          }
        })
        return response.data.data!
      }
      throw error
    }
  }

  async updateAllocationRequestPriority(requestId: string, priority: number): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.patch(`/environments/allocation/request/${requestId}`, { priority })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.patch(`/environments/allocation/request/${requestId}`, { priority })
        return response.data.data!
      }
      throw error
    }
  }

  async bulkCancelAllocationRequests(requestIds: string[]): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.post('/environments/allocation/bulk-cancel', {
        request_ids: requestIds
      })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.post('/environments/allocation/bulk-cancel', {
          request_ids: requestIds
        })
        return response.data.data!
      }
      throw error
    }
  }

  // Real-time allocation events (Server-Sent Events)
  createAllocationEventStream(): EventSource {
    const baseURL = this.client.defaults.baseURL
    const token = localStorage.getItem('auth_token')
    const url = `${baseURL}/environments/allocation/events${token ? `?token=${token}` : ''}`
    return new EventSource(url)
  }

  // WebSocket connection for live environment updates
  createEnvironmentWebSocket(): WebSocket {
    const baseURL = this.client.defaults.baseURL?.replace('http', 'ws')
    const token = localStorage.getItem('auth_token')
    const url = `${baseURL}/ws/environments/allocation${token ? `?token=${token}` : ''}`
    return new WebSocket(url)
  }

  // Environment Preference Management
  async validateEnvironmentCompatibility(requirements: HardwareRequirements, preferences?: AllocationPreferences): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.post('/environments/validate-compatibility', {
        requirements,
        preferences
      })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.post('/environments/validate-compatibility', {
          requirements,
          preferences
        })
        return response.data.data!
      }
      throw error
    }
  }

  async getEnvironmentCapabilities(): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get('/environments/capabilities')
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get('/environments/capabilities')
        return response.data.data!
      }
      throw error
    }
  }

  async savePreferenceProfile(profile: {
    name: string
    description?: string
    requirements: HardwareRequirements
    preferences: AllocationPreferences
  }): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.post('/environments/preference-profiles', profile)
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.post('/environments/preference-profiles', profile)
        return response.data.data!
      }
      throw error
    }
  }

  async getPreferenceProfiles(): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get('/environments/preference-profiles')
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get('/environments/preference-profiles')
        return response.data.data!
      }
      throw error
    }
  }

  async deletePreferenceProfile(profileId: string): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.delete(`/environments/preference-profiles/${profileId}`)
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.delete(`/environments/preference-profiles/${profileId}`)
        return response.data.data!
      }
      throw error
    }
  }

  // AI Test Generation
  async generateTestsFromDiff(
    diff: string, 
    maxTests: number = 20, 
    testTypes: string[] = ['unit']
  ): Promise<APIResponse> {
    try {
      const response: AxiosResponse<APIResponse> = await this.client.post('/tests/generate-from-diff', null, {
        params: {
          diff_content: diff,
          max_tests: maxTests,
          test_types: testTypes
        }
      })
      return response.data
    } catch (error: any) {
      console.error('API generateTestsFromDiff error:', error)
      
      if (error.response?.status === 401) {
        // Try to get demo token and retry
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse> = await this.client.post('/tests/generate-from-diff', null, {
          params: {
            diff_content: diff,
            max_tests: maxTests,
            test_types: testTypes
          }
        })
        return response.data
      }
      
      // Enhance error with more context
      if (error.response?.data?.message) {
        const errorMsg = error.response.data.message
        if (errorMsg === 'Not implemented') {
          throw new Error('This AI generation method is not yet implemented on the backend. Please try a different generation method or contact support.')
        }
        throw new Error(errorMsg)
      } else if (error.response?.status) {
        throw new Error(`Server error: HTTP ${error.response.status}`)
      } else if (error.message) {
        throw new Error(error.message)
      } else {
        throw new Error('Network error: Unable to connect to server')
      }
    }
  }

  async submitTestGeneration(params: {
    code_change: string
    test_types: string[]
    priority: string
  }): Promise<{ submission_id: string }> {
    try {
      const response: AxiosResponse<APIResponse<{ submission_id: string }>> = await this.client.post('/tests/generate', {
        code_change: params.code_change,
        test_types: params.test_types,
        priority: params.priority,
      })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<{ submission_id: string }>> = await this.client.post('/tests/generate', {
          code_change: params.code_change,
          test_types: params.test_types,
          priority: params.priority,
        })
        return response.data.data!
      }
      throw error
    }
  }

  async generateTestsFromFunction(
    functionName: string,
    filePath: string,
    subsystem: string = 'unknown',
    maxTests: number = 10
  ): Promise<APIResponse> {
    console.log('🔧 generateTestsFromFunction called with:', { functionName, filePath, subsystem, maxTests })
    
    try {
      const response: AxiosResponse<APIResponse> = await this.client.post('/tests/generate-from-function', null, {
        params: {
          function_name: functionName,
          file_path: filePath,
          subsystem: subsystem,
          max_tests: maxTests
        }
      })
      
      console.log('✅ generateTestsFromFunction success:', response.data)
      return response.data
    } catch (error: any) {
      console.error('❌ generateTestsFromFunction error:', error)
      
      if (error.response?.status === 401) {
        // Try to get demo token and retry
        console.log('🔑 Retrying with fresh token...')
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse> = await this.client.post('/tests/generate-from-function', null, {
          params: {
            function_name: functionName,
            file_path: filePath,
            subsystem: subsystem,
            max_tests: maxTests
          }
        })
        console.log('✅ generateTestsFromFunction retry success:', response.data)
        return response.data
      }
      
      // Enhanced error with more context
      if (error.response?.data?.message) {
        const errorMsg = error.response.data.message
        if (errorMsg === 'Not implemented') {
          throw new Error('Function-based AI generation is not yet implemented on the backend. Please try "From Code Diff" or "Kernel Test Driver" instead.')
        }
        throw new Error(errorMsg)
      } else if (error.response?.status) {
        throw new Error(`Server error: HTTP ${error.response.status}`)
      } else if (error.message) {
        throw new Error(error.message)
      } else {
        throw new Error('Network error: Unable to connect to server')
      }
    }
  }

  async analyzeCode(diffContent: string): Promise<APIResponse> {
    const response: AxiosResponse<APIResponse> = await this.client.post('/tests/analyze-code', {
      diff_content: diffContent
    })
    return response.data
  }

  async generateKernelTestDriver(
    functionName: string,
    filePath: string,
    subsystem: string = 'unknown',
    testTypes: string[] = ['unit', 'integration']
  ): Promise<APIResponse> {
    console.log('🔧 generateKernelTestDriver called with:', { functionName, filePath, subsystem, testTypes })
    
    try {
      const response: AxiosResponse<APIResponse> = await this.client.post('/tests/generate-kernel-driver', null, {
        params: {
          function_name: functionName,
          file_path: filePath,
          subsystem: subsystem,
          test_types: testTypes
        }
      })
      
      console.log('✅ generateKernelTestDriver success:', response.data)
      return response.data
    } catch (error: any) {
      console.error('❌ generateKernelTestDriver error:', error)
      
      if (error.response?.status === 401) {
        // Try to get demo token and retry
        console.log('🔑 Retrying with fresh token...')
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse> = await this.client.post('/tests/generate-kernel-driver', null, {
          params: {
            function_name: functionName,
            file_path: filePath,
            subsystem: subsystem,
            test_types: testTypes
          }
        })
        console.log('✅ generateKernelTestDriver retry success:', response.data)
        return response.data
      }
      
      // Enhanced error with more context
      if (error.response?.data?.message) {
        const errorMsg = error.response.data.message
        if (errorMsg === 'Not implemented') {
          throw new Error('Kernel test driver generation is not yet implemented on the backend. Please try "From Code Diff" instead.')
        }
        throw new Error(errorMsg)
      } else if (error.response?.status) {
        throw new Error(`Server error: HTTP ${error.response.status}`)
      } else if (error.message) {
        throw new Error(error.message)
      } else {
        throw new Error('Network error: Unable to connect to server')
      }
    }
  }

  // Demo authentication
  private async initializeDemoAuth(): Promise<void> {
    try {
      // Check if we already have a token
      const existingToken = localStorage.getItem('auth_token')
      if (existingToken) {
        return
      }

      // Get demo token with admin credentials
      const response: AxiosResponse<APIResponse> = await this.client.post('/auth/login', {
        username: 'admin',
        password: 'admin123'
      })
      if (response.data.success && response.data.data?.access_token) {
        localStorage.setItem('auth_token', response.data.data.access_token)
      }
    } catch (error) {
      console.log('Demo auth initialization failed, continuing without auth:', error)
    }
  }

  async getDemoToken(): Promise<string | null> {
    try {
      const response: AxiosResponse<APIResponse> = await this.client.post('/auth/login', {
        username: 'admin',
        password: 'admin123'
      })
      if (response.data.success && response.data.data?.access_token) {
        const token = response.data.data.access_token
        localStorage.setItem('auth_token', token)
        return token
      }
    } catch (error) {
      console.error('Failed to get demo token:', error)
    }
    return null
  }

  private async ensureDemoToken(): Promise<void> {
    const token = await this.getDemoToken()
    if (!token) {
      throw new Error('Failed to obtain authentication token')
    }
  }

  // Test Plan Management
  async getTestPlans(): Promise<any[]> {
    try {
      const response: AxiosResponse<APIResponse<{plans: any[]}>> = await this.client.get('/test-plans')
      return response.data.data?.plans || []
    } catch (error: any) {
      console.error('Failed to fetch test plans:', error)
      // Return mock data for now
      return []
    }
  }

  async createTestPlan(planData: any): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse> = await this.client.post('/test-plans', planData)
      return response.data.data
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse> = await this.client.post('/test-plans', planData)
        return response.data.data
      }
      throw error
    }
  }

  async updateTestPlan(planId: string, planData: any): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse> = await this.client.put(`/test-plans/${planId}`, planData)
      return response.data.data
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse> = await this.client.put(`/test-plans/${planId}`, planData)
        return response.data.data
      }
      throw error
    }
  }

  async deleteTestPlan(planId: string): Promise<void> {
    try {
      await this.client.delete(`/test-plans/${planId}`)
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        await this.client.delete(`/test-plans/${planId}`)
      } else {
        throw error
      }
    }
  }

  async executeTestPlan(planId: string): Promise<{ execution_plan_id: string }> {
    try {
      const response: AxiosResponse<APIResponse<{ execution_plan_id: string }>> = 
        await this.client.post(`/test-plans/${planId}/execute`)
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<{ execution_plan_id: string }>> = 
          await this.client.post(`/test-plans/${planId}/execute`)
        return response.data.data!
      }
      throw error
    }
  }

  // Deployment Management API methods
  async getDeploymentOverview(): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get('/deployments/overview')
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get('/deployments/overview')
        return response.data.data!
      }
      
      // Return mock data for development
      console.log('🔧 Returning mock deployment overview data')
      return {
        active_deployments: 3,
        completed_today: 12,
        success_rate: 91.7,
        average_duration: '2m 15s',
        failed_deployments: 1,
        cancelled_deployments: 0,
        queue_size: 2,
        environments: {
          qemu_ready: 4,
          qemu_deploying: 2,
          qemu_failed: 1,
          physical_ready: 2,
          physical_deploying: 1,
          physical_failed: 0
        }
      }
    }
  }

  async getEnvironmentsStatus(): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get('/environments/status')
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get('/environments/status')
        return response.data.data!
      }
      
      // Return mock data for development
      console.log('🔧 Returning mock environment status data')
      return {
        environments: [
          {
            environment_id: 'qemu-vm-x86-001',
            environment_type: 'qemu-x86',
            status: 'ready',
            health: 'healthy',
            resource_usage: {
              cpu_percent: 15,
              memory_percent: 25,
              disk_percent: 30,
              network_io: { in: 1024, out: 2048 }
            },
            current_deployment: null,
            last_health_check: new Date().toISOString()
          },
          {
            environment_id: 'qemu-vm-arm64-002',
            environment_type: 'qemu-arm',
            status: 'deploying',
            health: 'healthy',
            resource_usage: {
              cpu_percent: 75,
              memory_percent: 80,
              disk_percent: 45,
              network_io: { in: 5120, out: 8192 }
            },
            current_deployment: 'kernel_security_test (67% - Installing Dependencies)',
            last_health_check: new Date().toISOString()
          },
          {
            environment_id: 'physical-board-001',
            environment_type: 'physical',
            status: 'ready',
            health: 'healthy',
            resource_usage: {
              cpu_percent: 20,
              memory_percent: 35,
              disk_percent: 50,
              network_io: { in: 2048, out: 4096 }
            },
            current_deployment: null,
            last_health_check: new Date().toISOString()
          },
          {
            environment_id: 'docker-container-001',
            environment_type: 'docker',
            status: 'allocating',
            health: 'unknown',
            resource_usage: {
              cpu_percent: 5,
              memory_percent: 10,
              disk_percent: 15,
              network_io: { in: 512, out: 1024 }
            },
            current_deployment: 'network_stack_test (25% - Environment Connection)',
            last_health_check: new Date(Date.now() - 60000).toISOString() // 1 minute ago
          }
        ]
      }
    }
  }

  async createDeployment(deploymentData: {
    plan_id: string
    environment_id: string
    artifacts: any[]
    priority?: string
    timeout_seconds?: number
  }): Promise<{ deployment_id: string, status: string, message: string }> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.post('/deployments/', deploymentData)
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.post('/deployments/', deploymentData)
        return response.data.data!
      }
      throw error
    }
  }

  async getDeploymentStatus(deploymentId: string): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get(`/deployments/${deploymentId}/status`)
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get(`/deployments/${deploymentId}/status`)
        return response.data.data!
      }
      throw error
    }
  }

  async cancelDeployment(deploymentId: string): Promise<{ success: boolean, message: string }> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.put(`/deployments/${deploymentId}/cancel`)
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.put(`/deployments/${deploymentId}/cancel`)
        return response.data.data!
      }
      throw error
    }
  }

  async retryDeployment(deploymentId: string): Promise<{ deployment_id: string, status: string, message: string }> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.post(`/deployments/${deploymentId}/retry`)
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.post(`/deployments/${deploymentId}/retry`)
        return response.data.data!
      }
      throw error
    }
  }

  async getDeploymentLogs(deploymentId: string, format: 'json' | 'text' = 'json'): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get(`/deployments/${deploymentId}/logs`, {
        params: { format }
      })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get(`/deployments/${deploymentId}/logs`, {
          params: { format }
        })
        return response.data.data!
      }
      throw error
    }
  }

  async getDeploymentMetrics(): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get('/deployments/metrics')
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get('/deployments/metrics')
        return response.data.data!
      }
      
      // Return mock data for development
      console.log('🔧 Returning mock deployment metrics data')
      return {
        total_deployments: 156,
        successful_deployments: 143,
        failed_deployments: 10,
        cancelled_deployments: 3,
        active_deployments: 3,
        queue_size: 2,
        average_duration_seconds: 135,
        retry_count: 7,
        environment_usage: {
          'qemu-x86': 45,
          'qemu-arm': 32,
          'physical': 23,
          'docker': 12
        }
      }
    }
  }

  async getDeploymentHistory(params?: {
    page?: number
    page_size?: number
    status?: string
    environment_id?: string
  }): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get('/deployments/history', { params })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get('/deployments/history', { params })
        return response.data.data!
      }
      throw error
    }
  }

  async getDeploymentAnalytics(params?: {
    start_date?: string
    end_date?: string
    environment_id?: string
  }): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get('/deployments/analytics', { params })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get('/deployments/analytics', { params })
        return response.data.data!
      }
      
      // Return mock analytics data for development
      console.log('🔧 Returning mock deployment analytics data')
      return {
        deployment_trends: [
          { date: '2026-01-01', successful: 12, failed: 1, cancelled: 0 },
          { date: '2026-01-02', successful: 15, failed: 2, cancelled: 1 },
          { date: '2026-01-03', successful: 18, failed: 0, cancelled: 0 },
          { date: '2026-01-04', successful: 14, failed: 1, cancelled: 0 },
          { date: '2026-01-05', successful: 16, failed: 2, cancelled: 1 },
          { date: '2026-01-06', successful: 20, failed: 1, cancelled: 0 },
          { date: '2026-01-07', successful: 12, failed: 1, cancelled: 0 }
        ],
        performance_metrics: {
          average_duration: 135,
          p95_duration: 280,
          p99_duration: 450,
          success_rate: 91.7
        },
        environment_breakdown: {
          'qemu-x86': { count: 45, success_rate: 95.6, avg_duration: 120 },
          'qemu-arm': { count: 32, success_rate: 87.5, avg_duration: 150 },
          'physical': { count: 23, success_rate: 95.7, avg_duration: 180 },
          'docker': { count: 12, success_rate: 100.0, avg_duration: 90 }
        }
      }
    }
  }

  async getPerformanceAnalytics(params?: {
    start_date?: string
    end_date?: string
    metric?: string
  }): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get('/deployments/analytics/performance', { params })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get('/deployments/analytics/performance', { params })
        return response.data.data!
      }
      throw error
    }
  }

  async getDeploymentTrends(params?: {
    start_date?: string
    end_date?: string
    metric?: string
  }): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get('/deployments/analytics/trends', { params })
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get('/deployments/analytics/trends', { params })
        return response.data.data!
      }
      throw error
    }
  }

  async getEnvironmentAnalytics(): Promise<any> {
    try {
      const response: AxiosResponse<APIResponse<any>> = await this.client.get('/deployments/analytics/environments')
      return response.data.data!
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse<any>> = await this.client.get('/deployments/analytics/environments')
        return response.data.data!
      }
      throw error
    }
  }

  async exportDeploymentAnalytics(params?: {
    format?: 'csv' | 'json'
    start_date?: string
    end_date?: string
  }): Promise<Blob> {
    try {
      const response: AxiosResponse<Blob> = await this.client.get('/deployments/analytics/export', {
        params,
        responseType: 'blob'
      })
      return response.data
    } catch (error: any) {
      if (error.response?.status === 401) {
        await this.ensureDemoToken()
        const response: AxiosResponse<Blob> = await this.client.get('/deployments/analytics/export', {
          params,
          responseType: 'blob'
        })
        return response.data
      }
      throw error
    }
  }

  // WebSocket connection for real-time deployment updates
  createDeploymentWebSocket(deploymentId?: string): WebSocket {
    const baseURL = this.client.defaults.baseURL?.replace('http', 'ws')
    const token = localStorage.getItem('auth_token')
    const url = deploymentId 
      ? `${baseURL}/deployments/${deploymentId}/status/live${token ? `?token=${token}` : ''}`
      : `${baseURL}/deployments/live${token ? `?token=${token}` : ''}`
    return new WebSocket(url)
  }
}

export const apiService = new APIService()
export default apiService