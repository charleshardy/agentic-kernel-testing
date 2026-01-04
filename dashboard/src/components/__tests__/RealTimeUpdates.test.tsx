/**
 * Tests for Real-Time Environment Status Updates
 * Validates the enhanced real-time functionality implementation
 */

import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import StatusChangeIndicator from '../StatusChangeIndicator'
import ConnectionStatus from '../ConnectionStatus'
import RealTimeStatusMonitor from '../RealTimeStatusMonitor'
import { EnvironmentStatus } from '../../types/environment'

// Mock notification
jest.mock('antd', () => ({
  ...jest.requireActual('antd'),
  notification: {
    success: jest.fn(),
    info: jest.fn(),
    warning: jest.fn(),
    error: jest.fn()
  }
}))

describe('Real-Time Environment Status Updates', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    })
    jest.clearAllMocks()
  })

  const renderWithQueryClient = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    )
  }

  describe('StatusChangeIndicator', () => {
    it('should display current status correctly', () => {
      renderWithQueryClient(
        <StatusChangeIndicator
          status={EnvironmentStatus.READY}
          showText={true}
        />
      )

      expect(screen.getByText('READY')).toBeInTheDocument()
    })

    it('should show animation when status changes', async () => {
      const { rerender } = renderWithQueryClient(
        <StatusChangeIndicator
          status={EnvironmentStatus.ALLOCATING}
          showAnimation={true}
          showText={true}
        />
      )

      expect(screen.getByText('ALLOCATING')).toBeInTheDocument()

      // Change status to trigger animation
      rerender(
        <QueryClientProvider client={queryClient}>
          <StatusChangeIndicator
            status={EnvironmentStatus.READY}
            previousStatus={EnvironmentStatus.ALLOCATING}
            showAnimation={true}
            showText={true}
          />
        </QueryClientProvider>
      )

      expect(screen.getByText('READY')).toBeInTheDocument()
    })

    it('should call onStatusChange callback when status changes', () => {
      const onStatusChange = jest.fn()
      
      const { rerender } = renderWithQueryClient(
        <StatusChangeIndicator
          status={EnvironmentStatus.ALLOCATING}
          onStatusChange={onStatusChange}
          environmentId="test-env-001"
        />
      )

      rerender(
        <QueryClientProvider client={queryClient}>
          <StatusChangeIndicator
            status={EnvironmentStatus.READY}
            previousStatus={EnvironmentStatus.ALLOCATING}
            onStatusChange={onStatusChange}
            environmentId="test-env-001"
          />
        </QueryClientProvider>
      )

      expect(onStatusChange).toHaveBeenCalledWith(
        EnvironmentStatus.READY,
        EnvironmentStatus.ALLOCATING
      )
    })

    it('should show updating state correctly', () => {
      renderWithQueryClient(
        <StatusChangeIndicator
          status={EnvironmentStatus.READY}
          isUpdating={true}
          showText={true}
        />
      )

      // Should still show the status even when updating
      expect(screen.getByText('READY')).toBeInTheDocument()
    })

    it('should display tooltip with environment information', async () => {
      const lastUpdated = new Date()
      
      renderWithQueryClient(
        <StatusChangeIndicator
          status={EnvironmentStatus.RUNNING}
          lastUpdated={lastUpdated}
          environmentId="test-env-001"
          showText={true}
        />
      )

      const indicator = screen.getByText('RUNNING')
      fireEvent.mouseEnter(indicator)

      await waitFor(() => {
        expect(screen.getByText(/Environment is currently running tests/)).toBeInTheDocument()
      })
    })
  })

  describe('ConnectionStatus', () => {
    const mockConnectionProps = {
      isConnected: true,
      connectionHealth: 'healthy' as const,
      lastUpdate: new Date(),
      updateCount: 42,
      errors: [],
      onReconnect: jest.fn(),
      showDetails: true
    }

    it('should display healthy connection status', () => {
      renderWithQueryClient(
        <ConnectionStatus {...mockConnectionProps} />
      )

      expect(screen.getByText('Connected')).toBeInTheDocument()
      expect(screen.getByText('Updates: 42')).toBeInTheDocument()
    })

    it('should display degraded connection status', () => {
      renderWithQueryClient(
        <ConnectionStatus
          {...mockConnectionProps}
          connectionHealth="degraded"
          isConnected={true}
        />
      )

      expect(screen.getByText('Degraded')).toBeInTheDocument()
      expect(screen.getByText('Reconnect')).toBeInTheDocument()
    })

    it('should display disconnected status', () => {
      renderWithQueryClient(
        <ConnectionStatus
          {...mockConnectionProps}
          connectionHealth="disconnected"
          isConnected={false}
        />
      )

      expect(screen.getByText('Disconnected')).toBeInTheDocument()
      expect(screen.getByText('Reconnect')).toBeInTheDocument()
    })

    it('should call onReconnect when reconnect button is clicked', () => {
      const onReconnect = jest.fn()
      
      renderWithQueryClient(
        <ConnectionStatus
          {...mockConnectionProps}
          connectionHealth="disconnected"
          onReconnect={onReconnect}
        />
      )

      fireEvent.click(screen.getByText('Reconnect'))
      expect(onReconnect).toHaveBeenCalled()
    })

    it('should show WebSocket and SSE status details', () => {
      const webSocketStatus = {
        isConnected: true,
        isConnecting: false,
        connectionAttempts: 0,
        lastError: null
      }

      const sseStatus = {
        isConnected: false,
        isConnecting: true,
        connectionAttempts: 2,
        lastError: 'Connection timeout'
      }

      renderWithQueryClient(
        <ConnectionStatus
          {...mockConnectionProps}
          webSocketStatus={webSocketStatus}
          sseStatus={sseStatus}
          connectionHealth="degraded"
        />
      )

      // Should show degraded status due to SSE being disconnected
      expect(screen.getByText('Degraded')).toBeInTheDocument()
    })

    it('should display connection quality indicator', () => {
      renderWithQueryClient(
        <ConnectionStatus
          {...mockConnectionProps}
          connectionQuality={75}
        />
      )

      // Connection quality should be visible in detailed view
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })
  })

  describe('RealTimeStatusMonitor', () => {
    const mockMonitorProps = {
      isConnected: true,
      connectionHealth: 'healthy' as const,
      lastUpdate: new Date(),
      updateCount: 100,
      errors: [],
      onReconnect: jest.fn()
    }

    it('should display connection statistics', () => {
      renderWithQueryClient(
        <RealTimeStatusMonitor {...mockMonitorProps} />
      )

      expect(screen.getByText('Updates Received')).toBeInTheDocument()
      expect(screen.getByText('100')).toBeInTheDocument()
      expect(screen.getByText('Last Update')).toBeInTheDocument()
    })

    it('should show alert for degraded connection', () => {
      renderWithQueryClient(
        <RealTimeStatusMonitor
          {...mockMonitorProps}
          connectionHealth="degraded"
        />
      )

      expect(screen.getByText('Connection Degraded')).toBeInTheDocument()
      expect(screen.getByText(/Some real-time features may be limited/)).toBeInTheDocument()
    })

    it('should show alert for disconnected state', () => {
      renderWithQueryClient(
        <RealTimeStatusMonitor
          {...mockMonitorProps}
          connectionHealth="disconnected"
          isConnected={false}
        />
      )

      expect(screen.getByText('Connection Lost')).toBeInTheDocument()
      expect(screen.getByText(/Real-time updates are unavailable/)).toBeInTheDocument()
    })

    it('should display WebSocket and SSE status', () => {
      const webSocketStatus = {
        isConnected: true,
        isConnecting: false,
        connectionAttempts: 0,
        lastError: null
      }

      const sseStatus = {
        isConnected: true,
        isConnecting: false,
        connectionAttempts: 0,
        lastError: null
      }

      renderWithQueryClient(
        <RealTimeStatusMonitor
          {...mockMonitorProps}
          webSocketStatus={webSocketStatus}
          sseStatus={sseStatus}
          showDetailedMetrics={true}
        />
      )

      expect(screen.getByText('Connection Details')).toBeInTheDocument()
      expect(screen.getByText('WebSocket:')).toBeInTheDocument()
      expect(screen.getByText('Server-Sent Events:')).toBeInTheDocument()
    })

    it('should handle manual reconnection', () => {
      const onReconnect = jest.fn()
      
      renderWithQueryClient(
        <RealTimeStatusMonitor
          {...mockMonitorProps}
          connectionHealth="disconnected"
          onReconnect={onReconnect}
        />
      )

      fireEvent.click(screen.getByText('Reconnect'))
      expect(onReconnect).toHaveBeenCalled()
    })

    it('should display recent errors', () => {
      const errors = [
        'WebSocket connection failed',
        'SSE connection timeout',
        'Network error'
      ]

      renderWithQueryClient(
        <RealTimeStatusMonitor
          {...mockMonitorProps}
          errors={errors}
        />
      )

      expect(screen.getByText('Recent Issues')).toBeInTheDocument()
      expect(screen.getByText(/WebSocket connection failed/)).toBeInTheDocument()
    })

    it('should show auto-recovery status', () => {
      renderWithQueryClient(
        <RealTimeStatusMonitor
          {...mockMonitorProps}
          enableAutoRecovery={true}
        />
      )

      expect(screen.getByText('Auto-Recovery:')).toBeInTheDocument()
      expect(screen.getByText('Enabled')).toBeInTheDocument()
    })
  })

  describe('Real-Time Integration', () => {
    it('should handle rapid status changes without performance issues', async () => {
      const onStatusChange = jest.fn()
      
      const { rerender } = renderWithQueryClient(
        <StatusChangeIndicator
          status={EnvironmentStatus.READY}
          onStatusChange={onStatusChange}
          environmentId="test-env-001"
        />
      )

      // Simulate rapid status changes
      const statuses = [
        EnvironmentStatus.ALLOCATING,
        EnvironmentStatus.RUNNING,
        EnvironmentStatus.CLEANUP,
        EnvironmentStatus.READY
      ]

      for (let i = 0; i < statuses.length; i++) {
        await act(async () => {
          rerender(
            <QueryClientProvider client={queryClient}>
              <StatusChangeIndicator
                status={statuses[i]}
                previousStatus={i > 0 ? statuses[i - 1] : EnvironmentStatus.READY}
                onStatusChange={onStatusChange}
                environmentId="test-env-001"
                animationDuration={100} // Faster animation for testing
              />
            </QueryClientProvider>
          )
        })

        // Small delay to allow animation to start
        await new Promise(resolve => setTimeout(resolve, 50))
      }

      expect(onStatusChange).toHaveBeenCalledTimes(statuses.length)
    })

    it('should maintain connection quality metrics', () => {
      const { rerender } = renderWithQueryClient(
        <ConnectionStatus
          isConnected={true}
          connectionHealth="healthy"
          lastUpdate={new Date()}
          updateCount={0}
          errors={[]}
          onReconnect={jest.fn()}
          showDetails={true}
          connectionQuality={100}
        />
      )

      expect(screen.getByText('Connected')).toBeInTheDocument()

      // Simulate connection degradation
      rerender(
        <QueryClientProvider client={queryClient}>
          <ConnectionStatus
            isConnected={true}
            connectionHealth="degraded"
            lastUpdate={new Date()}
            updateCount={50}
            errors={['Connection timeout']}
            onReconnect={jest.fn()}
            showDetails={true}
            connectionQuality={60}
          />
        </QueryClientProvider>
      )

      expect(screen.getByText('Degraded')).toBeInTheDocument()
    })
  })
})