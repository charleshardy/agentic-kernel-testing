import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { vi, describe, it, expect, beforeEach } from 'vitest'

import {
  InfrastructureDashboard,
  BuildServerPanel,
  BuildJobDashboard,
  ArtifactBrowser,
  HostManagementPanel,
  BoardManagementPanel,
  PipelineDashboard,
  ResourceGroupPanel,
  InfrastructureSettings
} from '../index'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('Infrastructure Dashboard', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('renders dashboard with resource counts', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        build_servers: { total: 5, online: 4, offline: 1 },
        hosts: { total: 10, online: 8, maintenance: 2 },
        boards: { total: 15, available: 10, in_use: 5 },
        pipelines: { active: 3, completed_today: 12 }
      })
    })

    render(<InfrastructureDashboard />, { wrapper: createWrapper() })
    expect(screen.getByText(/Infrastructure Overview/i)).toBeInTheDocument()
  })
})

describe('Build Server Panel', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('renders build server list', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([
        { id: '1', hostname: 'build-01', ip_address: '192.168.1.10', status: 'online', architecture: 'x86_64' }
      ])
    })

    render(<BuildServerPanel />, { wrapper: createWrapper() })
    expect(screen.getByText(/Build Servers/i)).toBeInTheDocument()
  })

  it('opens registration modal on button click', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve([]) })

    render(<BuildServerPanel />, { wrapper: createWrapper() })
    fireEvent.click(screen.getByText(/Register Server/i))
    await waitFor(() => {
      expect(screen.getByText(/Register Build Server/i)).toBeInTheDocument()
    })
  })
})

describe('Build Job Dashboard', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('renders build job list with tabs', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([
        { id: 'job-1', repository_url: 'https://github.com/test/repo', branch: 'main', status: 'building', progress_percent: 50, architecture: 'x86_64' }
      ])
    })

    render(<BuildJobDashboard />, { wrapper: createWrapper() })
    expect(screen.getByText(/Build Jobs/i)).toBeInTheDocument()
    expect(screen.getByText(/All Jobs/i)).toBeInTheDocument()
  })
})

describe('Artifact Browser', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('renders artifact list with search', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([
        { id: 'art-1', build_id: 'build-1', artifact_type: 'kernel_image', filename: 'vmlinuz', file_size_bytes: 1024000, architecture: 'x86_64', branch: 'main' }
      ])
    })

    render(<ArtifactBrowser />, { wrapper: createWrapper() })
    expect(screen.getByText(/Build Artifacts/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Search by build ID/i)).toBeInTheDocument()
  })
})

describe('Host Management Panel', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('renders host list with capacity stats', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([
        { id: '1', hostname: 'qemu-host-01', ip_address: '192.168.1.20', status: 'online', architecture: 'x86_64', total_cpu_cores: 32, total_memory_mb: 65536, running_vm_count: 5, max_vms: 10, kvm_enabled: true }
      ])
    })

    render(<HostManagementPanel />, { wrapper: createWrapper() })
    expect(screen.getByText(/QEMU Hosts/i)).toBeInTheDocument()
  })
})

describe('Board Management Panel', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('renders board list with power control', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([
        { id: '1', name: 'rpi4-01', board_type: 'raspberry_pi_4', status: 'available', architecture: 'arm64', power_control: { method: 'usb_hub' }, peripherals: ['gpio', 'i2c'] }
      ])
    })

    render(<BoardManagementPanel />, { wrapper: createWrapper() })
    expect(screen.getByText(/Physical Boards/i)).toBeInTheDocument()
  })
})

describe('Pipeline Dashboard', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('renders pipeline list with stages', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([
        { id: 'pipe-1', name: 'kernel-test', status: 'running', current_stage: 'build', stages: ['build', 'deploy', 'test'] }
      ])
    })

    render(<PipelineDashboard />, { wrapper: createWrapper() })
    expect(screen.getByText(/Pipelines/i)).toBeInTheDocument()
  })
})

describe('Resource Group Panel', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('renders resource groups with tabs', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([
        { id: 'grp-1', name: 'production-x86', resource_type: 'build_server', member_count: 3, total_capacity: 10, used_capacity: 5, labels: { env: 'prod' } }
      ])
    })

    render(<ResourceGroupPanel />, { wrapper: createWrapper() })
    expect(screen.getByText(/Resource Groups/i)).toBeInTheDocument()
    expect(screen.getByText(/All Groups/i)).toBeInTheDocument()
  })
})

describe('Infrastructure Settings', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('renders settings form with all sections', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        health_check_interval_seconds: 30,
        alert_thresholds: { build_server_disk_warning_percent: 80, host_cpu_warning_percent: 85, host_memory_warning_percent: 85, board_temperature_warning_celsius: 70 },
        notifications: { email_enabled: true, email_recipients: ['admin@test.com'], webhook_enabled: false, webhook_url: '' },
        artifact_retention: { max_age_days: 30, max_total_size_gb: 500, keep_latest_per_branch: 5 },
        selection_strategy: { default_build_server: 'load_balanced', default_host: 'load_balanced', default_board: 'round_robin' }
      })
    })

    render(<InfrastructureSettings />, { wrapper: createWrapper() })
    expect(screen.getByText(/Infrastructure Settings/i)).toBeInTheDocument()
    expect(screen.getByText(/Health Monitoring/i)).toBeInTheDocument()
    expect(screen.getByText(/Alert Thresholds/i)).toBeInTheDocument()
    expect(screen.getByText(/Notifications/i)).toBeInTheDocument()
  })
})
