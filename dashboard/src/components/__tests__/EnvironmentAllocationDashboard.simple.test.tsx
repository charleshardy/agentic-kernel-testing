/**
 * Simple test to verify Environment Allocation components can be imported and rendered
 */

import React from 'react'
import { render } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import '@testing-library/jest-dom'

import EnvironmentManagementDashboard from '../EnvironmentManagementDashboard'
import EnvironmentTable from '../EnvironmentTable'
import { EnvironmentType, EnvironmentStatus, EnvironmentHealth } from '../../types/environment'

// Mock the API service
jest.mock('../../services/api', () => ({
  getEnvironmentAllocation: jest.fn(() => Promise.resolve({
    environments: [],
    queue: [],
    resourceUtilization: [],
    history: []
  })),
  performEnvironmentAction: jest.fn(() => Promise.resolve())
}))

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

describe('Environment Allocation Components', () => {
  test('EnvironmentManagementDashboard renders without crashing', () => {
    render(
      <TestWrapper>
        <EnvironmentManagementDashboard />
      </TestWrapper>
    )
  })

  test('EnvironmentTable renders with empty data', () => {
    const mockHandlers = {
      onEnvironmentSelect: jest.fn(),
      onEnvironmentAction: jest.fn()
    }

    render(
      <TestWrapper>
        <EnvironmentTable
          environments={[]}
          onEnvironmentSelect={mockHandlers.onEnvironmentSelect}
          onEnvironmentAction={mockHandlers.onEnvironmentAction}
          showResourceUsage={true}
          filterOptions={{}}
        />
      </TestWrapper>
    )
  })

  test('EnvironmentTable renders with sample data', () => {
    const sampleEnvironment = {
      id: 'env-test-001',
      type: EnvironmentType.QEMU_X86,
      status: EnvironmentStatus.READY,
      architecture: 'x86_64',
      assignedTests: ['test-001', 'test-002'],
      resources: {
        cpu: 45,
        memory: 60,
        disk: 30,
        network: {
          bytesIn: 1000,
          bytesOut: 2000,
          packetsIn: 100,
          packetsOut: 200
        }
      },
      health: EnvironmentHealth.HEALTHY,
      metadata: {
        kernelVersion: '5.15.0',
        ipAddress: '192.168.1.100',
        sshCredentials: undefined,
        provisionedAt: '2024-01-01T00:00:00Z',
        lastHealthCheck: '2024-01-01T01:00:00Z'
      },
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T01:00:00Z'
    }

    const mockHandlers = {
      onEnvironmentSelect: jest.fn(),
      onEnvironmentAction: jest.fn()
    }

    render(
      <TestWrapper>
        <EnvironmentTable
          environments={[sampleEnvironment]}
          onEnvironmentSelect={mockHandlers.onEnvironmentSelect}
          onEnvironmentAction={mockHandlers.onEnvironmentAction}
          showResourceUsage={true}
          filterOptions={{}}
        />
      </TestWrapper>
    )
  })
})