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
    method: 'manual' | 'ai_diff' | 'ai_function'
    source_data: any
    generated_at: string
    ai_model?: string
    generation_params?: Record<string, any>
  }
  execution_status?: 'never_run' | 'running' | 'completed' | 'failed'
  last_execution_at?: string
  tags?: string[]
  is_favorite?: boolean
}

export interface TestCaseFilters {
  test_type?: string
  subsystem?: string
  status?: string
  generation_method?: 'manual' | 'ai_diff' | 'ai_function'
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
    // Always use direct backend URL for better reliability
    const baseURL = 'http://localhost:8000/api/v1'
      
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Initialize demo authentication
    this.initializeDemoAuth()

    // Add request interceptor for authentication
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        // Log authentication errors but don't auto-redirect in demo mode
        if (error.response?.status === 401) {
          console.log('Authentication required for:', error.config?.url)
          localStorage.removeItem('auth_token')
          // Let individual methods handle retry logic
        }
        return Promise.reject(error)
      }
    )
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
    const response: AxiosResponse<APIResponse<ExecutionPlanStatus>> = await this.client.get(`/status/execution/${planId}`)
    return response.data.data!
  }

  async getActiveExecutions(): Promise<ExecutionPlanStatus[]> {
    const response: AxiosResponse<APIResponse<ExecutionPlanStatus[]>> = await this.client.get('/status/active')
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
    const response: AxiosResponse<APIResponse<any[]>> = await this.client.get('/environments')
    return response.data.data!
  }

  async getEnvironmentStatus(envId: string): Promise<any> {
    const response: AxiosResponse<APIResponse> = await this.client.get(`/environments/${envId}/status`)
    return response.data.data!
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
      throw error
    }
  }

  async generateTestsFromFunction(
    functionName: string,
    filePath: string,
    subsystem: string = 'unknown',
    maxTests: number = 10
  ): Promise<APIResponse> {
    try {
      const response: AxiosResponse<APIResponse> = await this.client.post('/tests/generate-from-function', null, {
        params: {
          function_name: functionName,
          file_path: filePath,
          subsystem: subsystem,
          max_tests: maxTests
        }
      })
      return response.data
    } catch (error: any) {
      if (error.response?.status === 401) {
        // Try to get demo token and retry
        await this.ensureDemoToken()
        const response: AxiosResponse<APIResponse> = await this.client.post('/tests/generate-from-function', null, {
          params: {
            function_name: functionName,
            file_path: filePath,
            subsystem: subsystem,
            max_tests: maxTests
          }
        })
        return response.data
      }
      throw error
    }
  }

  async analyzeCode(diffContent: string): Promise<APIResponse> {
    const response: AxiosResponse<APIResponse> = await this.client.post('/tests/analyze-code', {
      diff_content: diffContent
    })
    return response.data
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
}

export const apiService = new APIService()
export default apiService