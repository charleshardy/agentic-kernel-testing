/**
 * Simple tests for Environment Preference Management components
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import EnvironmentPreferenceForm from '../EnvironmentPreferenceForm'
import { Environment, EnvironmentType, EnvironmentStatus, EnvironmentHealth } from '../../types/environment'

// Mock antd components
jest.mock('antd', () => {
  const antd = jest.requireActual('antd')
  return {
    ...antd,
    notification: {
      success: jest.fn(),
      error: jest.fn(),
      warning: jest.fn(),
      info: jest.fn()
    },
    message: {
      success: jest.fn(),
      error: jest.fn(),
      warning: jest.fn(),
      info: jest.fn()
    }
  }
})

// Mock API service
jest.mock('../../services/api', () => ({
  apiService: {
    validateEnvironmentCompatibility: jest.fn(),
    getEnvironmentCapabilities: jest.fn(),
    savePreferenceProfile: jest.fn(),
    getPreferenceProfiles: jest.fn(),
    deletePreferenceProfile: jest.fn()
  }
}))

const createTestWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

const mockEnvironments: Environment[] = [
  {
    id: 'env-1',
    type: EnvironmentType.QEMU_X86,
    status: EnvironmentStatus.READY,
    architecture: 'x86_64',
    assignedTests: [],
    resources: {
      cpu: 10,
      memory: 20,
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
      memoryMB: 4096,
      cpuCores: 2
    },
    createdAt: '2023-01-01T00:00:00Z',
    updatedAt: '2023-01-01T00:00:00Z'
  }
]

describe('Environment Preference Management Simple Tests', () => {
  beforeEach(() => {
    // Mock localStorage
    const mockLocalStorage = {}
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn((key: string) => null),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn()
      },
      writable: true
    })

    jest.clearAllMocks()
  })

  test('renders preference form without crashing', () => {
    const TestWrapper = createTestWrapper()
    
    render(
      <TestWrapper>
        <EnvironmentPreferenceForm
          availableEnvironments={mockEnvironments}
          onSubmit={jest.fn()}
        />
      </TestWrapper>
    )

    expect(screen.getByText('Hardware Requirements')).toBeInTheDocument()
    expect(screen.getByText('Allocation Preferences')).toBeInTheDocument()
  })

  test('displays architecture options', () => {
    const TestWrapper = createTestWrapper()
    
    render(
      <TestWrapper>
        <EnvironmentPreferenceForm
          availableEnvironments={mockEnvironments}
          onSubmit={jest.fn()}
        />
      </TestWrapper>
    )

    expect(screen.getByText('Architecture')).toBeInTheDocument()
  })

  test('shows apply preferences button', () => {
    const TestWrapper = createTestWrapper()
    
    render(
      <TestWrapper>
        <EnvironmentPreferenceForm
          availableEnvironments={mockEnvironments}
          onSubmit={jest.fn()}
        />
      </TestWrapper>
    )

    expect(screen.getByText('Apply Preferences')).toBeInTheDocument()
  })
})