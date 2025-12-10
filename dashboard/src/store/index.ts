import { create } from 'zustand'
import { TestResult, SystemMetrics, ExecutionPlanStatus, CoverageData } from '../services/api'

interface DashboardState {
  // System status
  systemMetrics: SystemMetrics | null
  isConnected: boolean
  lastUpdate: string | null

  // Test execution
  activeExecutions: ExecutionPlanStatus[]
  recentResults: TestResult[]
  
  // Coverage data
  coverageData: CoverageData | null
  coverageTrends: any[]
  
  // Performance data
  performanceMetrics: any[]
  performanceTrends: any[]
  
  // UI state
  selectedTimeRange: string
  filters: {
    status?: string
    testType?: string
    subsystem?: string
  }
  
  // Actions
  setSystemMetrics: (metrics: SystemMetrics) => void
  setConnectionStatus: (connected: boolean) => void
  updateActiveExecutions: (executions: ExecutionPlanStatus[]) => void
  addTestResult: (result: TestResult) => void
  updateTestResult: (testId: string, updates: Partial<TestResult>) => void
  setCoverageData: (data: CoverageData) => void
  setCoverageTrends: (trends: any[]) => void
  setPerformanceMetrics: (metrics: any[]) => void
  setPerformanceTrends: (trends: any[]) => void
  setTimeRange: (range: string) => void
  setFilters: (filters: any) => void
  reset: () => void
}

const initialState = {
  systemMetrics: null,
  isConnected: false,
  lastUpdate: null,
  activeExecutions: [],
  recentResults: [],
  coverageData: null,
  coverageTrends: [],
  performanceMetrics: [],
  performanceTrends: [],
  selectedTimeRange: '24h',
  filters: {},
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  ...initialState,

  setSystemMetrics: (metrics) => set({ 
    systemMetrics: metrics, 
    lastUpdate: new Date().toISOString() 
  }),

  setConnectionStatus: (connected) => set({ isConnected: connected }),

  updateActiveExecutions: (executions) => set({ activeExecutions: executions }),

  addTestResult: (result) => set((state) => ({
    recentResults: [result, ...state.recentResults].slice(0, 50) // Keep last 50 results
  })),

  updateTestResult: (testId, updates) => set((state) => ({
    recentResults: state.recentResults.map(result => 
      result.test_id === testId ? { ...result, ...updates } : result
    )
  })),

  setCoverageData: (data) => set({ coverageData: data }),

  setCoverageTrends: (trends) => set({ coverageTrends: trends }),

  setPerformanceMetrics: (metrics) => set({ performanceMetrics: metrics }),

  setPerformanceTrends: (trends) => set({ performanceTrends: trends }),

  setTimeRange: (range) => set({ selectedTimeRange: range }),

  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters }
  })),

  reset: () => set(initialState),
}))

export default useDashboardStore