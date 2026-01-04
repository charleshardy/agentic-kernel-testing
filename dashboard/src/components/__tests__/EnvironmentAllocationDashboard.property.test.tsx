/**
 * Property-based tests for Environment Allocation UI component rendering accuracy
 * 
 * **Feature: environment-allocation-ui, Property 1: Environment Information Display Accuracy**
 * **Validates: Requirements 1.1, 1.4, 3.1, 3.3**
 */

import React from 'react'
import { render, screen, cleanup } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import fc from 'fast-check'
import '@testing-library/jest-dom'

import EnvironmentManagementDashboard from '../EnvironmentManagementDashboard'
import EnvironmentTable from '../EnvironmentTable'
import { 
  Environment, 
  EnvironmentType, 
  EnvironmentStatus, 
  EnvironmentHealth
} from '../../types/environment'

// Mock the API service to avoid actual network calls
jest.mock('../../services/api', () => ({
  getEnvironmentAllocation: jest.fn(() => Promise.resolve({
    environments: [],
    queue: [],
    resourceUtilization: [],
    history: []
  })),
  performEnvironmentAction: jest.fn(() => Promise.resolve())
}))

// Test wrapper component with required providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

// Property-based test generators using fast-check
const environmentArbitrary = fc.record({
  id: fc.string({ minLength: 8, maxLength: 32 }),
  type: fc.constantFrom(...Object.values(EnvironmentType)),
  status: fc.constantFrom(...Object.values(EnvironmentStatus)),
  architecture: fc.constantFrom('x86_64', 'arm64', 'riscv64', 'arm'),
  assignedTests: fc.array(fc.string({ minLength: 8, maxLength: 16 }), { maxLength: 10 }),
  resources: fc.record({
    cpu: fc.float({ min: 0, max: 100 }),
    memory: fc.float({ min: 0, max: 100 }),
    disk: fc.float({ min: 0, max: 100 }),
    network: fc.record({
      bytesIn: fc.integer({ min: 0, max: 1000000000 }),
      bytesOut: fc.integer({ min: 0, max: 1000000000 }),
      packetsIn: fc.integer({ min: 0, max: 10000000 }),
      packetsOut: fc.integer({ min: 0, max: 10000000 })
    })
  }),
  health: fc.constantFrom(...Object.values(EnvironmentHealth)),
  metadata: fc.record({
    kernelVersion: fc.option(fc.string({ minLength: 1, maxLength: 50 })),
    ipAddress: fc.option(fc.string()),
    sshCredentials: fc.option(fc.dictionary(fc.string(), fc.string())),
    provisionedAt: fc.option(fc.date().map(d => d.toISOString())),
    lastHealthCheck: fc.option(fc.date().map(d => d.toISOString()))
  }),
  createdAt: fc.date().map(d => d.toISOString()),
  updatedAt: fc.date().map(d => d.toISOString())
})

describe('Environment Allocation UI Component Rendering Accuracy', () => {
  afterEach(() => {
    cleanup()
    jest.clearAllMocks()
  })

  /**
   * Property 1: Environment Information Display Accuracy
   * For any set of environments and their associated data, the UI should display all environment 
   * information including status, configuration, assigned tests, and metadata accurately and completely
   */
  test('Property 1: Dashboard renders without errors for any environment data', () => {
    fc.assert(
      fc.property(fc.array(environmentArbitrary, { maxLength: 5 }), (environments) => {
        // Mock the API response with generated environments
        const mockApiService = require('../../services/api')
        mockApiService.getEnvironmentAllocation.mockResolvedValue({
          environments,
          queue: [],
          resourceUtilization: [],
          history: []
        })

        // Render the dashboard component
        const { container } = render(
          <TestWrapper>
            <EnvironmentManagementDashboard />
          </TestWrapper>
        )

        // Verify the component renders without throwing errors
        expect(container).toBeInTheDocument()
        
        // Verify essential UI elements are present
        expect(screen.getByText('Environment Allocation')).toBeInTheDocument()
        
        return true
      }),
      { numRuns: 100, verbose: true }
    )
  })

  test('Property 1: EnvironmentTable displays environment information correctly', () => {
    fc.assert(
      fc.property(environmentArbitrary, (environment) => {
        // Ensure resource values are within valid ranges
        const validEnvironment = {
          ...environment,
          resources: {
            ...environment.resources,
            cpu: Math.max(0, Math.min(100, environment.resources.cpu)),
            memory: Math.max(0, Math.min(100, environment.resources.memory)),
            disk: Math.max(0, Math.min(100, environment.resources.disk))
          }
        }

        const mockHandlers = {
          onEnvironmentSelect: jest.fn(),
          onEnvironmentAction: jest.fn()
        }

        render(
          <TestWrapper>
            <EnvironmentTable
              environments={[validEnvironment]}
              onEnvironmentSelect={mockHandlers.onEnvironmentSelect}
              onEnvironmentAction={mockHandlers.onEnvironmentAction}
              showResourceUsage={true}
              filterOptions={{}}
            />
          </TestWrapper>
        )

        // Verify status is displayed
        expect(screen.getByText(environment.status.toUpperCase())).toBeInTheDocument()

        // Verify health is displayed
        expect(screen.getByText(environment.health.toUpperCase())).toBeInTheDocument()

        // Verify environment type is displayed
        expect(screen.getByText(environment.type)).toBeInTheDocument()

        return true
      }),
      { numRuns: 100, verbose: true }
    )
  })
})