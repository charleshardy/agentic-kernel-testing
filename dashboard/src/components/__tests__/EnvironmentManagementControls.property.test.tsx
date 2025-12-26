/**
 * Property-based tests for Environment Management Controls functionality
 * **Feature: environment-allocation-ui, Property 4: Environment Management Controls Functionality**
 * **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import fc from 'fast-check'
import EnvironmentManagementControls, { EnvironmentCreationConfig } from '../EnvironmentManagementControls'
import { Environment, EnvironmentType, EnvironmentStatus, EnvironmentHealth, EnvironmentAction } from '../../types/environment'

// Mock antd components that have complex behaviors
jest.mock('antd', () => {
  const antd = jest.requireActual('antd')
  return {
    ...antd,
    notification: {
      success: jest.fn(),
      error: jest.fn(),
      warning: jest.fn(),
      info: jest.fn()
    }
  }
})

// Test configuration for property-based testing
const testConfig = {
  numRuns: 100,
  verbose: true,
  seed: 42
}

// Generators for test data
const environmentTypeGenerator = fc.constantFrom(
  EnvironmentType.QEMU_X86,
  EnvironmentType.QEMU_ARM,
  EnvironmentType.DOCKER,
  EnvironmentType.PHYSICAL,
  EnvironmentType.CONTAINER
)

const environmentStatusGenerator = fc.constantFrom(
  EnvironmentStatus.ALLOCATING,
  EnvironmentStatus.READY,
  EnvironmentStatus.RUNNING,
  EnvironmentStatus.CLEANUP,
  EnvironmentStatus.MAINTENANCE,
  EnvironmentStatus.ERROR,
  EnvironmentStatus.OFFLINE
)

const environmentHealthGenerator = fc.constantFrom(
  EnvironmentHealth.HEALTHY,
  EnvironmentHealth.DEGRADED,
  EnvironmentHealth.UNHEALTHY,
  EnvironmentHealth.UNKNOWN
)

const environmentGenerator = fc.record({
  id: fc.string({ minLength: 8, maxLength: 32 }),
  type: environmentTypeGenerator,
  status: environmentStatusGenerator,
  architecture: fc.constantFrom('x86_64', 'arm64', 'riscv64'),
  assignedTests: fc.array(fc.string({ minLength: 8, maxLength: 16 }), { maxLength: 5 }),
  resources: fc.record({
    cpu: fc.integer({ min: 0, max: 100 }),
    memory: fc.integer({ min: 0, max: 100 }),
    disk: fc.integer({ min: 0, max: 100 }),
    network: fc.record({
      bytesIn: fc.integer({ min: 0, max: 1000000 }),
      bytesOut: fc.integer({ min: 0, max: 1000000 }),
      packetsIn: fc.integer({ min: 0, max: 10000 }),
      packetsOut: fc.integer({ min: 0, max: 10000 })
    })
  }),
  health: environmentHealthGenerator,
  metadata: fc.record({
    kernelVersion: fc.option(fc.string(), { nil: undefined }),
    ipAddress: fc.option(fc.string(), { nil: undefined }),
    provisionedAt: fc.option(fc.string(), { nil: undefined }),
    lastHealthCheck: fc.option(fc.string(), { nil: undefined })
  }),
  createdAt: fc.date().map(d => d.toISOString()),
  updatedAt: fc.date().map(d => d.toISOString())
})

const environmentCreationConfigGenerator = fc.record({
  type: environmentTypeGenerator,
  architecture: fc.constantFrom('x86_64', 'arm64', 'riscv64'),
  cpuCores: fc.integer({ min: 1, max: 32 }),
  memoryMB: fc.integer({ min: 512, max: 32768 }),
  storageGB: fc.integer({ min: 10, max: 500 }),
  enableKVM: fc.option(fc.boolean(), { nil: undefined }),
  enableNestedVirtualization: fc.option(fc.boolean(), { nil: undefined }),
  customKernelVersion: fc.option(fc.string(), { nil: undefined }),
  additionalFeatures: fc.option(fc.array(fc.string()), { nil: undefined })
})

const actionTypeGenerator = fc.constantFrom('reset', 'maintenance', 'offline', 'cleanup')

describe('EnvironmentManagementControls Property Tests', () => {
  let mockOnEnvironmentAction: jest.Mock
  let mockOnCreateEnvironment: jest.Mock
  let mockOnBulkAction: jest.Mock

  beforeEach(() => {
    mockOnEnvironmentAction = jest.fn().mockResolvedValue(undefined)
    mockOnCreateEnvironment = jest.fn().mockResolvedValue(undefined)
    mockOnBulkAction = jest.fn().mockResolvedValue(undefined)
    jest.clearAllMocks()
  })

  /**
   * **Feature: environment-allocation-ui, Property 4: Environment Management Controls Functionality**
   * Property: For any environment management action (reset, maintenance, creation, cleanup), 
   * the UI should provide appropriate controls, confirm actions, and show immediate status updates
   * **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
   */
  describe('Property 4: Environment Management Controls Functionality', () => {
    it('should provide appropriate controls for all environment management actions', () => {
      fc.assert(fc.property(
        fc.array(environmentGenerator, { minLength: 0, maxLength: 10 }),
        (environments: Environment[]) => {
          const { container } = render(
            <EnvironmentManagementControls
              selectedEnvironments={environments}
              onEnvironmentAction={mockOnEnvironmentAction}
              onCreateEnvironment={mockOnCreateEnvironment}
              onBulkAction={mockOnBulkAction}
              isLoading={false}
            />
          )

          // Verify create environment button is always present
          const createButton = screen.getByText('Create Environment')
          expect(createButton).toBeInTheDocument()
          expect(createButton).toBeEnabled()

          // For single environment selection, verify individual action controls
          if (environments.length === 1) {
            const env = environments[0]
            
            // Check that action section is displayed
            expect(screen.getByText(/Actions for:/)).toBeInTheDocument()
            
            // Verify reset button exists and has correct state
            const resetButton = screen.getByText('Reset')
            expect(resetButton).toBeInTheDocument()
            
            // Reset should be disabled for running or allocating environments
            if (env.status === EnvironmentStatus.RUNNING || env.status === EnvironmentStatus.ALLOCATING) {
              expect(resetButton).toBeDisabled()
            }
            
            // Verify maintenance button exists and has correct state
            const maintenanceButton = screen.getByText('Maintenance')
            expect(maintenanceButton).toBeInTheDocument()
            
            // Maintenance should be disabled if already in maintenance
            if (env.status === EnvironmentStatus.MAINTENANCE) {
              expect(maintenanceButton).toBeDisabled()
            }
            
            // Verify offline button exists and has correct state
            const offlineButton = screen.getByText('Take Offline')
            expect(offlineButton).toBeInTheDocument()
            
            // Offline should be disabled if already offline
            if (env.status === EnvironmentStatus.OFFLINE) {
              expect(offlineButton).toBeDisabled()
            }
            
            // Verify cleanup button exists and has correct state
            const cleanupButton = screen.getByText('Force Cleanup')
            expect(cleanupButton).toBeInTheDocument()
            
            // Cleanup should be disabled if already in cleanup
            if (env.status === EnvironmentStatus.CLEANUP) {
              expect(cleanupButton).toBeDisabled()
            }
          }

          // For multiple environment selection, verify bulk action controls
          if (environments.length > 1) {
            expect(screen.getByText(/Bulk Actions/)).toBeInTheDocument()
            expect(screen.getByText('Bulk Reset')).toBeInTheDocument()
            expect(screen.getByText('Bulk Maintenance')).toBeInTheDocument()
            expect(screen.getByText('Bulk Offline')).toBeInTheDocument()
            expect(screen.getByText('Bulk Cleanup')).toBeInTheDocument()
          }

          return true
        }
      ), testConfig)
    })

    it('should confirm destructive actions before execution', async () => {
      await fc.assert(fc.asyncProperty(
        environmentGenerator,
        actionTypeGenerator,
        async (environment: Environment, actionType: string) => {
          const user = userEvent.setup()
          
          render(
            <EnvironmentManagementControls
              selectedEnvironments={[environment]}
              onEnvironmentAction={mockOnEnvironmentAction}
              onCreateEnvironment={mockOnCreateEnvironment}
              onBulkAction={mockOnBulkAction}
              isLoading={false}
            />
          )

          // Destructive actions (reset, offline) should show confirmation
          if (actionType === 'reset' || actionType === 'offline') {
            const buttonText = actionType === 'reset' ? 'Reset' : 'Take Offline'
            const button = screen.getByText(buttonText)
            
            // Skip if button is disabled due to environment status
            if (button.hasAttribute('disabled')) {
              return true
            }
            
            await user.click(button)
            
            // Should show confirmation dialog
            await waitFor(() => {
              expect(screen.getByText(/This will/)).toBeInTheDocument()
            })
            
            // Should have confirm and cancel buttons
            expect(screen.getByText('Cancel')).toBeInTheDocument()
            const confirmButton = actionType === 'reset' ? 
              screen.getByText('Reset') : 
              screen.getByText('Take Offline')
            expect(confirmButton).toBeInTheDocument()
            
            // Cancel should not trigger action
            await user.click(screen.getByText('Cancel'))
            expect(mockOnEnvironmentAction).not.toHaveBeenCalled()
          }

          return true
        }
      ), testConfig)
    })

    it('should show immediate status updates during action execution', async () => {
      await fc.assert(fc.asyncProperty(
        environmentGenerator,
        actionTypeGenerator,
        async (environment: Environment, actionType: string) => {
          // Mock action to simulate delay
          mockOnEnvironmentAction.mockImplementation(() => 
            new Promise(resolve => setTimeout(resolve, 100))
          )

          const user = userEvent.setup()
          
          render(
            <EnvironmentManagementControls
              selectedEnvironments={[environment]}
              onEnvironmentAction={mockOnEnvironmentAction}
              onCreateEnvironment={mockOnCreateEnvironment}
              onBulkAction={mockOnBulkAction}
              isLoading={false}
            />
          )

          // Find the appropriate button for the action
          let button: HTMLElement | null = null
          let shouldSkip = false

          switch (actionType) {
            case 'reset':
              button = screen.getByText('Reset')
              shouldSkip = environment.status === EnvironmentStatus.RUNNING || 
                          environment.status === EnvironmentStatus.ALLOCATING
              break
            case 'maintenance':
              button = screen.getByText('Maintenance')
              shouldSkip = environment.status === EnvironmentStatus.MAINTENANCE
              break
            case 'offline':
              button = screen.getByText('Take Offline')
              shouldSkip = environment.status === EnvironmentStatus.OFFLINE
              break
            case 'cleanup':
              button = screen.getByText('Force Cleanup')
              shouldSkip = environment.status === EnvironmentStatus.CLEANUP
              break
          }

          if (!button || shouldSkip || button.hasAttribute('disabled')) {
            return true
          }

          // For destructive actions, handle confirmation
          if (actionType === 'reset' || actionType === 'offline') {
            await user.click(button)
            
            await waitFor(() => {
              expect(screen.getByText(/This will/)).toBeInTheDocument()
            })
            
            const confirmButton = actionType === 'reset' ? 
              screen.getByText('Reset') : 
              screen.getByText('Take Offline')
            await user.click(confirmButton)
          } else {
            await user.click(button)
          }

          // Should show progress indicator during execution
          await waitFor(() => {
            expect(screen.getByText(/Starting/)).toBeInTheDocument()
          }, { timeout: 1000 })

          return true
        }
      ), testConfig)
    })

    it('should validate environment creation form inputs', async () => {
      await fc.assert(fc.asyncProperty(
        environmentCreationConfigGenerator,
        async (config: EnvironmentCreationConfig) => {
          const user = userEvent.setup()
          
          render(
            <EnvironmentManagementControls
              selectedEnvironments={[]}
              onEnvironmentAction={mockOnEnvironmentAction}
              onCreateEnvironment={mockOnCreateEnvironment}
              onBulkAction={mockOnBulkAction}
              isLoading={false}
            />
          )

          // Open create environment modal
          await user.click(screen.getByText('Create Environment'))
          
          await waitFor(() => {
            expect(screen.getByText('Create New Environment')).toBeInTheDocument()
          })

          // Form should have all required fields
          expect(screen.getByLabelText(/Environment Type/)).toBeInTheDocument()
          expect(screen.getByLabelText(/Architecture/)).toBeInTheDocument()
          expect(screen.getByLabelText(/CPU Cores/)).toBeInTheDocument()
          expect(screen.getByLabelText(/Memory \(MB\)/)).toBeInTheDocument()
          expect(screen.getByLabelText(/Storage \(GB\)/)).toBeInTheDocument()

          // Should have create and cancel buttons
          expect(screen.getByText('Create Environment')).toBeInTheDocument()
          expect(screen.getByText('Cancel')).toBeInTheDocument()

          // Should show informational alert about provisioning time
          expect(screen.getByText(/Creating a new environment may take/)).toBeInTheDocument()

          return true
        }
      ), testConfig)
    })

    it('should handle bulk actions correctly for multiple environments', async () => {
      await fc.assert(fc.asyncProperty(
        fc.array(environmentGenerator, { minLength: 2, maxLength: 5 }),
        actionTypeGenerator,
        async (environments: Environment[], actionType: string) => {
          const user = userEvent.setup()
          
          render(
            <EnvironmentManagementControls
              selectedEnvironments={environments}
              onEnvironmentAction={mockOnEnvironmentAction}
              onCreateEnvironment={mockOnCreateEnvironment}
              onBulkAction={mockOnBulkAction}
              isLoading={false}
            />
          )

          // Should show bulk actions section
          expect(screen.getByText(/Bulk Actions/)).toBeInTheDocument()
          expect(screen.getByText(`(${environments.length} environments selected)`)).toBeInTheDocument()

          // Find the appropriate bulk action button
          let button: HTMLElement | null = null
          switch (actionType) {
            case 'reset':
              button = screen.getByText('Bulk Reset')
              break
            case 'maintenance':
              button = screen.getByText('Bulk Maintenance')
              break
            case 'offline':
              button = screen.getByText('Bulk Offline')
              break
            case 'cleanup':
              button = screen.getByText('Bulk Cleanup')
              break
          }

          if (!button) {
            return true
          }

          // For destructive actions, handle confirmation
          if (actionType === 'reset' || actionType === 'offline') {
            await user.click(button)
            
            await waitFor(() => {
              expect(screen.getByText(new RegExp(`${actionType.charAt(0).toUpperCase() + actionType.slice(1)} ${environments.length} Environments`, 'i'))).toBeInTheDocument()
            })
            
            const confirmButton = actionType === 'reset' ? 
              screen.getByText('Reset All') : 
              screen.getByText('Take All Offline')
            await user.click(confirmButton)
          } else {
            await user.click(button)
          }

          // Should call bulk action handler with correct parameters
          await waitFor(() => {
            expect(mockOnBulkAction).toHaveBeenCalledWith(
              environments.map(env => env.id),
              { type: actionType }
            )
          })

          return true
        }
      ), testConfig)
    })

    it('should display selected environments summary correctly', () => {
      fc.assert(fc.property(
        fc.array(environmentGenerator, { minLength: 1, maxLength: 10 }),
        (environments: Environment[]) => {
          render(
            <EnvironmentManagementControls
              selectedEnvironments={environments}
              onEnvironmentAction={mockOnEnvironmentAction}
              onCreateEnvironment={mockOnCreateEnvironment}
              onBulkAction={mockOnBulkAction}
              isLoading={false}
            />
          )

          // Should show selected environments summary
          expect(screen.getByText(`Selected Environments (${environments.length})`)).toBeInTheDocument()

          // Should display each selected environment
          environments.forEach(env => {
            expect(screen.getByText(env.id.slice(0, 12) + '...')).toBeInTheDocument()
            expect(screen.getByText(`${env.type} - ${env.status}`)).toBeInTheDocument()
          })

          return true
        }
      ), testConfig)
    })
  })
})