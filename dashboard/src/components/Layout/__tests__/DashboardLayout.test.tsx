import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import DashboardLayout from '../DashboardLayout'

// Mock the store
jest.mock('../../../store', () => ({
  useDashboardStore: () => ({
    isConnected: true,
    setConnectionStatus: jest.fn(),
  }),
}))

// Mock the websocket service
jest.mock('../../../services/websocket', () => ({
  __esModule: true,
  default: {
    connect: jest.fn(),
    disconnect: jest.fn(),
  },
}))

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('DashboardLayout', () => {
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

  it('renders the navigation menu with Test Cases item', () => {
    renderWithProviders(
      <DashboardLayout>
        <div>Test Content</div>
      </DashboardLayout>
    )

    // Check if the Test Cases menu item is present
    expect(screen.getByText('Test Cases')).toBeInTheDocument()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Test Execution')).toBeInTheDocument()
  })

  it('displays Test Cases menu item in correct position', () => {
    renderWithProviders(
      <DashboardLayout>
        <div>Test Content</div>
      </DashboardLayout>
    )

    const menuItems = screen.getAllByRole('menuitem')
    const testCasesItem = menuItems.find(item => 
      item.textContent?.includes('Test Cases')
    )
    const dashboardItem = menuItems.find(item => 
      item.textContent?.includes('Dashboard')
    )
    const testExecutionItem = menuItems.find(item => 
      item.textContent?.includes('Test Execution')
    )

    expect(testCasesItem).toBeInTheDocument()
    expect(dashboardItem).toBeInTheDocument()
    expect(testExecutionItem).toBeInTheDocument()

    // Test Cases should come after Dashboard but before Test Execution
    const allItems = screen.getAllByRole('menuitem')
    const dashboardIndex = allItems.findIndex(item => 
      item.textContent?.includes('Dashboard')
    )
    const testCasesIndex = allItems.findIndex(item => 
      item.textContent?.includes('Test Cases')
    )
    const testExecutionIndex = allItems.findIndex(item => 
      item.textContent?.includes('Test Execution')
    )

    expect(dashboardIndex).toBeLessThan(testCasesIndex)
    expect(testCasesIndex).toBeLessThan(testExecutionIndex)
  })

  it('shows active state for Test Cases when on test-cases route', () => {
    // Mock the location to be on test-cases route
    const mockLocation = {
      pathname: '/test-cases',
      search: '',
      hash: '',
      state: null,
      key: 'test',
    }

    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useLocation: () => mockLocation,
    }))

    renderWithProviders(
      <DashboardLayout>
        <div>Test Content</div>
      </DashboardLayout>
    )

    // The menu should highlight the Test Cases item
    const testCasesItem = screen.getByText('Test Cases').closest('.ant-menu-item')
    expect(testCasesItem).toHaveClass('ant-menu-item-selected')
  })

  it('renders the application title', () => {
    renderWithProviders(
      <DashboardLayout>
        <div>Test Content</div>
      </DashboardLayout>
    )

    expect(screen.getByText('Agentic Testing System')).toBeInTheDocument()
    expect(screen.getByText('Agentic AI Testing System')).toBeInTheDocument()
  })

  it('shows connection status indicator', () => {
    renderWithProviders(
      <DashboardLayout>
        <div>Test Content</div>
      </DashboardLayout>
    )

    expect(screen.getByText('Connected')).toBeInTheDocument()
  })

  it('renders children content', () => {
    renderWithProviders(
      <DashboardLayout>
        <div data-testid="test-content">Test Content</div>
      </DashboardLayout>
    )

    expect(screen.getByTestId('test-content')).toBeInTheDocument()
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('handles sidebar collapse functionality', () => {
    renderWithProviders(
      <DashboardLayout>
        <div>Test Content</div>
      </DashboardLayout>
    )

    // Find the collapse button (usually an arrow or hamburger icon)
    const collapseButton = screen.getByRole('button', { name: /collapse/i })
    expect(collapseButton).toBeInTheDocument()

    // Click to collapse
    fireEvent.click(collapseButton)

    // The sidebar should show collapsed state (ATS instead of full name)
    expect(screen.getByText('ATS')).toBeInTheDocument()
  })

  it('displays user menu with admin user', () => {
    renderWithProviders(
      <DashboardLayout>
        <div>Test Content</div>
      </DashboardLayout>
    )

    expect(screen.getByText('Admin User')).toBeInTheDocument()
  })
})