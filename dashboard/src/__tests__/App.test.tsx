import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import App from '../App'

// Mock the store
jest.mock('../store', () => ({
  useDashboardStore: () => ({
    isConnected: true,
    setConnectionStatus: jest.fn(),
  }),
}))

// Mock the API service
jest.mock('../services/api', () => ({
  __esModule: true,
  default: {
    getTests: jest.fn(() => Promise.resolve({
      tests: [],
      total: 0
    })),
    getExecutionPlans: jest.fn(() => Promise.resolve({
      execution_plans: [],
      total: 0
    })),
  }
}))

// Mock the websocket service
jest.mock('../services/websocket', () => ({
  __esModule: true,
  default: {
    connect: jest.fn(),
    disconnect: jest.fn(),
  },
}))

const renderWithRouter = (initialEntries: string[] = ['/']) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('App Routing', () => {
  beforeEach(() => {
    // Mock fetch for health check
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      })
    ) as jest.Mock
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('renders Dashboard component on root route', () => {
    renderWithRouter(['/'])
    
    // Should render the dashboard page
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('renders TestCases component on /test-cases route', () => {
    renderWithRouter(['/test-cases'])
    
    // Should render the test cases page
    expect(screen.getByText('Test Cases')).toBeInTheDocument()
    // Should show the test cases specific content
    expect(screen.getByText('Total Test Cases')).toBeInTheDocument()
  })

  it('renders TestExecution component on /tests route', () => {
    renderWithRouter(['/tests'])
    
    // Should render the test execution page
    expect(screen.getByText('Test Execution')).toBeInTheDocument()
  })

  it('renders TestResults component on /results route', () => {
    renderWithRouter(['/results'])
    
    // Should render the test results page
    expect(screen.getByText('Test Results')).toBeInTheDocument()
  })

  it('renders Coverage component on /coverage route', () => {
    renderWithRouter(['/coverage'])
    
    // Should render the coverage page
    expect(screen.getByText('Coverage Analysis')).toBeInTheDocument()
  })

  it('renders Performance component on /performance route', () => {
    renderWithRouter(['/performance'])
    
    // Should render the performance page
    expect(screen.getByText('Performance')).toBeInTheDocument()
  })

  it('renders Settings component on /settings route', () => {
    renderWithRouter(['/settings'])
    
    // Should render the settings page
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('redirects to dashboard on unknown route', () => {
    renderWithRouter(['/unknown-route'])
    
    // Should redirect to dashboard
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('renders login placeholder on /login route', () => {
    renderWithRouter(['/login'])
    
    // Should render the login placeholder
    expect(screen.getByText('Demo Mode - No Authentication Required')).toBeInTheDocument()
    expect(screen.getByText('Return to Dashboard')).toBeInTheDocument()
  })

  it('maintains navigation menu on all routes', () => {
    renderWithRouter(['/test-cases'])
    
    // Navigation should be present
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Test Cases')).toBeInTheDocument()
    expect(screen.getByText('Test Execution')).toBeInTheDocument()
    expect(screen.getByText('Test Results')).toBeInTheDocument()
    expect(screen.getByText('Coverage Analysis')).toBeInTheDocument()
    expect(screen.getByText('Performance')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('handles URL parameters for test cases route', () => {
    renderWithRouter(['/test-cases?search=test&type=unit&page=2'])
    
    // Should render the test cases page with URL parameters
    expect(screen.getByText('Test Cases')).toBeInTheDocument()
    
    // The TestCases component should handle the URL parameters
    // (This is tested more thoroughly in the TestCases component tests)
  })
})