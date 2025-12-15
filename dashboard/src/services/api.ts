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
    // Use direct backend URL since proxy might not be working on different ports
    const baseURL = window.location.hostname === 'localhost' && window.location.port !== '3000' 
      ? 'http://localhost:8000/api/v1'  // Direct connection for non-standard ports
      : '/api/v1'  // Use proxy for standard setup
      
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

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
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token')
          window.location.href = '/login'
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
    const response: AxiosResponse<APIResponse<SystemMetrics>> = await this.client.get('/status/metrics')
    return response.data.data!
  }

  // Test management
  async getTests(params?: {
    page?: number
    page_size?: number
    status?: string
    test_type?: string
  }): Promise<{ tests: TestCase[], total: number }> {
    const response: AxiosResponse<APIResponse> = await this.client.get('/tests', { params })
    return response.data.data!
  }

  async getTestById(testId: string): Promise<TestCase> {
    const response: AxiosResponse<APIResponse<TestCase>> = await this.client.get(`/tests/${testId}`)
    return response.data.data!
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
}

export const apiService = new APIService()
export default apiService