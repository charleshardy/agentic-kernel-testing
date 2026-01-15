import React from 'react'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import { SidebarProvider } from '../contexts/SidebarContext'
import EnhancedSidebar from '../components/Layout/EnhancedSidebar'
import SecurityDashboard from '../pages/SecurityDashboard'
import AIModelManagement from '../pages/AIModelManagement'
import UserTeamManagement from '../pages/UserTeamManagement'
import NotificationCenter from '../pages/NotificationCenter'
import SecurityService from '../services/SecurityService'
import AIModelService from '../services/AIModelService'
import UserManagementService from '../services/UserManagementService'
import NotificationService from '../services/NotificationService'

// Mock services
jest.mock('../services/SecurityService')
jest.mock('../services/AIModelService')
jest.mock('../services/UserManagementService')
jest.mock('../services/NotificationService')

const mockSecurityService = SecurityService as jest.Mocked<typeof SecurityService>
const mockAIModelService = AIModelService as jest.Mocked<typeof AIModelService>
const mockUserManagementService = UserManagementService as jest.Mocked<typeof UserManagementService>
const mockNotificationService = NotificationService as jest.Mocked<typeof NotificationService>

const renderWithProviders = (component: React.ReactElement, userPermissions: string[] = []) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <SidebarProvider>
          {component}
        </SidebarProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Sidebar Integration Tests - Feature: missing-sidebar-functionality', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Cross-Feature Navigation Integration', () => {
    /**
     * Feature: missing-sidebar-functionality, Property 11: Security Finding Navigation Links
     * Validates: Requirements 12.1
     */
    it('provides direct navigation from security findings to related test cases', async () => {
      const user = userEvent.setup()
      
      // Mock security finding with related test case
      const securityFinding = {
        id: 'vuln-001',
        severity: 'high' as const,
        type: 'vulnerability' as const,
        title: 'Buffer Overflow in Memory Allocation',
        description: 'Potential buffer overflow detected',
        affectedComponents: ['kernel/mm/memory.c'],
        discoveredAt: new Date('2024-01-15T10:00:00Z'),
        status: 'open' as const,
        relatedTestCases: ['test-123', 'test-456'],
        relatedResults: ['result-789']
      }

      mockSecurityService.getSecurityMetrics.mockResolvedValue({
        vulnerabilityCount: { critical: 0, high: 1, medium: 2, low: 5 },
        complianceScore: 85,
        activeFuzzingCampaigns: 3,
        recentFindings: [securityFinding],
        securityTrends: []
      })

      renderWithProviders(<SecurityDashboard />)

      // Wait for security findings to load
      await waitFor(() => {
        expect(screen.getByText('Buffer Overflow in Memory Allocation')).toBeInTheDocument()
      })

      // Click on the finding to view details
      const findingCard = screen.getByText('Buffer Overflow in Memory Allocation').closest('div')
      await user.click(findingCard!)

      // Should show related test cases with navigation links
      await waitFor(() => {
        expect(screen.getByText(/related test cases/i)).toBeInTheDocument()
        expect(screen.getByText('test-123')).toBeInTheDocument()
        expect(screen.getByText('test-456')).toBeInTheDocument()
      })

      // Click on related test case link
      const testCaseLink = screen.getByText('test-123')
      await user.click(testCaseLink)

      // Should navigate to test case details
      await waitFor(() => {
        expect(window.location.pathname).toContain('/test-cases/test-123')
      })
    })

    /**
     * Feature: missing-sidebar-functionality, Property 12: User and Team Association Display
     * Validates: Requirements 12.3
     */
    it('displays user and team associations with test plans and environments', async () => {
      const user = userEvent.setup()
      
      // Mock user with associations
      const mockUser = {
        id: 'user-001',
        username: 'john.doe',
        email: 'john.doe@example.com',
        firstName: 'John',
        lastName: 'Doe',
        roles: [{ id: 'role-1', name: 'Developer', description: 'Developer role', permissions: [], isSystem: true }],
        teams: [{ id: 'team-1', name: 'Kernel Team', description: 'Kernel development team', members: [], resources: [], permissions: [], createdBy: 'admin', createdAt: new Date() }],
        permissions: [],
        preferences: {},
        lastLogin: new Date(),
        status: 'active' as const,
        createdAt: new Date(),
        associatedTestPlans: ['plan-001', 'plan-002'],
        associatedEnvironments: ['env-qemu-1', 'env-board-2'],
        associatedResults: ['result-123']
      }

      mockUserManagementService.getUsers.mockResolvedValue({
        users: [mockUser],
        pagination: { page: 1, pageSize: 20, totalItems: 1, totalPages: 1 }
      })

      renderWithProviders(<UserTeamManagement />)

      // Wait for user list to load
      await waitFor(() => {
        expect(screen.getByText('john.doe')).toBeInTheDocument()
      })

      // Click on user to view details
      const userRow = screen.getByText('john.doe').closest('tr')
      const viewButton = within(userRow!).getByRole('button', { name: /view/i })
      await user.click(viewButton)

      // Should display associated test plans
      await waitFor(() => {
        expect(screen.getByText(/associated test plans/i)).toBeInTheDocument()
        expect(screen.getByText('plan-001')).toBeInTheDocument()
        expect(screen.getByText('plan-002')).toBeInTheDocument()
      })

      // Should display associated environments
      expect(screen.getByText(/associated environments/i)).toBeInTheDocument()
      expect(screen.getByText('env-qemu-1')).toBeInTheDocument()
      expect(screen.getByText('env-board-2')).toBeInTheDocument()

      // Should display associated results
      expect(screen.getByText(/associated results/i)).toBeInTheDocument()
      expect(screen.getByText('result-123')).toBeInTheDocument()
    })

    /**
     * Feature: missing-sidebar-functionality, Property 13: Notification Navigation Links
     * Validates: Requirements 12.4
     */
    it('provides direct navigation from notifications to relevant features', async () => {
      const user = userEvent.setup()
      
      // Mock notifications with navigation targets
      const notifications = [
        {
          id: 'notif-001',
          type: 'alert' as const,
          title: 'Security Vulnerability Detected',
          message: 'High severity vulnerability found in kernel/mm',
          priority: 'high' as const,
          category: 'security',
          recipients: [],
          channels: [],
          status: 'delivered' as const,
          metadata: {
            targetFeature: 'security',
            targetId: 'vuln-001',
            targetPath: '/security/vulnerabilities/vuln-001'
          },
          createdAt: new Date(),
          deliveredAt: new Date()
        },
        {
          id: 'notif-002',
          type: 'info' as const,
          title: 'AI Model Performance Degraded',
          message: 'GPT-4 response time increased',
          priority: 'medium' as const,
          category: 'ai-models',
          recipients: [],
          channels: [],
          status: 'delivered' as const,
          metadata: {
            targetFeature: 'ai-models',
            targetId: 'model-gpt4',
            targetPath: '/ai-models/model-gpt4'
          },
          createdAt: new Date(),
          deliveredAt: new Date()
        }
      ]

      mockNotificationService.getNotifications.mockResolvedValue({
        notifications,
        pagination: { page: 1, pageSize: 20, totalItems: 2, totalPages: 1 }
      })

      renderWithProviders(<NotificationCenter />)

      // Wait for notifications to load
      await waitFor(() => {
        expect(screen.getByText('Security Vulnerability Detected')).toBeInTheDocument()
        expect(screen.getByText('AI Model Performance Degraded')).toBeInTheDocument()
      })

      // Click on security notification
      const securityNotif = screen.getByText('Security Vulnerability Detected').closest('div')
      const viewSecurityButton = within(securityNotif!).getByRole('button', { name: /view/i })
      await user.click(viewSecurityButton)

      // Should navigate to security dashboard
      await waitFor(() => {
        expect(window.location.pathname).toContain('/security/vulnerabilities/vuln-001')
      })
    })
  })

  describe('Permission-Based Access Control', () => {
    /**
     * Feature: missing-sidebar-functionality, Property 10: Permission-Based Menu Filtering
     * Validates: Requirements 11.3
     */
    it('displays only menu items matching user permissions', async () => {
      // Test with limited permissions
      const limitedPermissions = ['view:test-cases', 'view:test-results']
      
      renderWithProviders(
        <EnhancedSidebar 
          collapsed={false}
          onCollapse={() => {}}
          userPermissions={limitedPermissions}
          notificationCounts={{}}
        />
      )

      // Should show core testing features
      await waitFor(() => {
        expect(screen.getByText('Test Cases')).toBeInTheDocument()
        expect(screen.getByText('Test Results')).toBeInTheDocument()
      })

      // Should NOT show security features (no permission)
      expect(screen.queryByText('Security Dashboard')).not.toBeInTheDocument()
      expect(screen.queryByText('Vulnerability Management')).not.toBeInTheDocument()

      // Should NOT show admin features (no permission)
      expect(screen.queryByText('User & Team Management')).not.toBeInTheDocument()
      expect(screen.queryByText('Audit & Compliance')).not.toBeInTheDocument()
    })

    it('displays all menu items for admin users', async () => {
      // Test with admin permissions
      const adminPermissions = [
        'view:*',
        'create:*',
        'update:*',
        'delete:*',
        'admin:*'
      ]
      
      renderWithProviders(
        <EnhancedSidebar 
          collapsed={false}
          onCollapse={() => {}}
          userPermissions={adminPermissions}
          notificationCounts={{}}
        />
      )

      // Should show all sections
      await waitFor(() => {
        expect(screen.getByText('Core Testing')).toBeInTheDocument()
        expect(screen.getByText('Security & Quality')).toBeInTheDocument()
        expect(screen.getByText('AI & Analytics')).toBeInTheDocument()
        expect(screen.getByText('Infrastructure')).toBeInTheDocument()
        expect(screen.getByText('Management')).toBeInTheDocument()
        expect(screen.getByText('Communication')).toBeInTheDocument()
      })

      // Should show security features
      expect(screen.getByText('Security Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Vulnerability Management')).toBeInTheDocument()

      // Should show admin features
      expect(screen.getByText('User & Team Management')).toBeInTheDocument()
      expect(screen.getByText('Audit & Compliance')).toBeInTheDocument()
      expect(screen.getByText('Backup & Recovery')).toBeInTheDocument()
    })

    /**
     * Feature: missing-sidebar-functionality, Property 19: Least Privilege Enforcement
     * Validates: Requirements 15.3
     */
    it('enforces least privilege across all new features', async () => {
      const user = userEvent.setup()
      
      // User with only read permissions
      const readOnlyPermissions = ['view:security', 'view:ai-models']
      
      // Mock AI model data
      mockAIModelService.getModels.mockResolvedValue({
        models: [{
          id: 'model-001',
          name: 'GPT-4',
          provider: 'openai' as const,
          version: '1.0',
          status: 'active' as const,
          metrics: {
            responseTime: 1200,
            accuracy: 0.95,
            tokenUsage: 50000,
            costPerRequest: 0.03,
            requestCount: 1000,
            errorRate: 0.01
          },
          configuration: {
            endpoint: 'https://api.openai.com',
            apiKey: '***',
            maxTokens: 4000,
            temperature: 0.7,
            rateLimit: 100,
            timeout: 30000
          }
        }],
        pagination: { page: 1, pageSize: 20, totalItems: 1, totalPages: 1 }
      })

      renderWithProviders(<AIModelManagement />, readOnlyPermissions)

      // Wait for models to load
      await waitFor(() => {
        expect(screen.getByText('GPT-4')).toBeInTheDocument()
      })

      // Should NOT show edit/delete buttons (no write permission)
      expect(screen.queryByRole('button', { name: /edit/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument()

      // Should NOT show create button
      expect(screen.queryByRole('button', { name: /add model/i })).not.toBeInTheDocument()

      // Should show view button (has read permission)
      expect(screen.getByRole('button', { name: /view/i })).toBeInTheDocument()
    })
  })

  describe('Sidebar Badge Display', () => {
    /**
     * Feature: missing-sidebar-functionality, Property 9: Sidebar Badge Display
     * Validates: Requirements 11.2
     */
    it('displays badge indicators for features with active alerts', async () => {
      const notificationCounts = {
        security: 5,
        'ai-models': 2,
        notifications: 10,
        audit: 3
      }
      
      renderWithProviders(
        <EnhancedSidebar 
          collapsed={false}
          onCollapse={() => {}}
          userPermissions={['view:*']}
          notificationCounts={notificationCounts}
        />
      )

      // Should display badges on relevant menu items
      await waitFor(() => {
        const securityItem = screen.getByText('Security Dashboard').closest('div')
        expect(within(securityItem!).getByText('5')).toBeInTheDocument()

        const aiModelsItem = screen.getByText('AI Model Management').closest('div')
        expect(within(aiModelsItem!).getByText('2')).toBeInTheDocument()

        const notificationsItem = screen.getByText('Notification Center').closest('div')
        expect(within(notificationsItem!).getByText('10')).toBeInTheDocument()

        const auditItem = screen.getByText('Audit & Compliance').closest('div')
        expect(within(auditItem!).getByText('3')).toBeInTheDocument()
      })
    })

    it('updates badge counts in real-time', async () => {
      const { rerender } = renderWithProviders(
        <EnhancedSidebar 
          collapsed={false}
          onCollapse={() => {}}
          userPermissions={['view:*']}
          notificationCounts={{ security: 5 }}
        />
      )

      // Initial badge count
      await waitFor(() => {
        const securityItem = screen.getByText('Security Dashboard').closest('div')
        expect(within(securityItem!).getByText('5')).toBeInTheDocument()
      })

      // Update notification counts
      rerender(
        <QueryClientProvider client={new QueryClient()}>
          <BrowserRouter>
            <SidebarProvider>
              <EnhancedSidebar 
                collapsed={false}
                onCollapse={() => {}}
                userPermissions={['view:*']}
                notificationCounts={{ security: 8 }}
              />
            </SidebarProvider>
          </BrowserRouter>
        </QueryClientProvider>
      )

      // Badge should update
      await waitFor(() => {
        const securityItem = screen.getByText('Security Dashboard').closest('div')
        expect(within(securityItem!).getByText('8')).toBeInTheDocument()
      })
    })
  })

  describe('Responsive Design and Mobile Compatibility', () => {
    it('collapses sidebar appropriately on mobile devices', async () => {
      const user = userEvent.setup()
      
      // Mock mobile viewport
      global.innerWidth = 375
      global.dispatchEvent(new Event('resize'))

      const onCollapse = jest.fn()
      
      renderWithProviders(
        <EnhancedSidebar 
          collapsed={false}
          onCollapse={onCollapse}
          userPermissions={['view:*']}
          notificationCounts={{}}
        />
      )

      // Find collapse button
      const collapseButton = screen.getByRole('button', { name: /collapse/i })
      await user.click(collapseButton)

      // Should call onCollapse
      expect(onCollapse).toHaveBeenCalledWith(true)
    })

    it('maintains functionality in collapsed state', async () => {
      renderWithProviders(
        <EnhancedSidebar 
          collapsed={true}
          onCollapse={() => {}}
          userPermissions={['view:*']}
          notificationCounts={{ security: 5 }}
        />
      )

      // Should still show icons and badges in collapsed state
      await waitFor(() => {
        // Icons should be visible
        expect(screen.getByTestId('security-icon')).toBeInTheDocument()
        
        // Badges should still be visible
        expect(screen.getByText('5')).toBeInTheDocument()
      })
    })
  })

  describe('Performance and Load Time Compliance', () => {
    /**
     * Feature: missing-sidebar-functionality, Property 15: Performance Load Time Compliance
     * Validates: Requirements 14.1
     */
    it('maintains sidebar load times under 2 seconds', async () => {
      const startTime = performance.now()
      
      renderWithProviders(
        <EnhancedSidebar 
          collapsed={false}
          onCollapse={() => {}}
          userPermissions={['view:*']}
          notificationCounts={{}}
        />
      )

      // Wait for sidebar to fully render
      await waitFor(() => {
        expect(screen.getByText('Core Testing')).toBeInTheDocument()
        expect(screen.getByText('Security & Quality')).toBeInTheDocument()
        expect(screen.getByText('AI & Analytics')).toBeInTheDocument()
      })

      const endTime = performance.now()
      const loadTime = endTime - startTime

      // Should load in under 2 seconds (2000ms)
      expect(loadTime).toBeLessThan(2000)
    })

    it('handles large notification counts efficiently', async () => {
      const largeNotificationCounts = {
        security: 999,
        'ai-models': 500,
        notifications: 1500,
        audit: 750,
        integrations: 300,
        resources: 200
      }
      
      const startTime = performance.now()
      
      renderWithProviders(
        <EnhancedSidebar 
          collapsed={false}
          onCollapse={() => {}}
          userPermissions={['view:*']}
          notificationCounts={largeNotificationCounts}
        />
      )

      // Should render all badges efficiently
      await waitFor(() => {
        expect(screen.getByText('999')).toBeInTheDocument()
        expect(screen.getByText('500')).toBeInTheDocument()
        expect(screen.getByText('1500')).toBeInTheDocument()
      })

      const endTime = performance.now()
      const renderTime = endTime - startTime

      // Should render efficiently even with large counts
      expect(renderTime).toBeLessThan(1000)
    })
  })

  describe('Search Functionality', () => {
    it('filters sidebar items based on search query', async () => {
      const user = userEvent.setup()
      
      renderWithProviders(
        <EnhancedSidebar 
          collapsed={false}
          onCollapse={() => {}}
          userPermissions={['view:*']}
          notificationCounts={{}}
        />
      )

      // Find search input
      const searchInput = screen.getByPlaceholderText(/search features/i)
      
      // Search for "security"
      await user.type(searchInput, 'security')

      // Should show only security-related items
      await waitFor(() => {
        expect(screen.getByText('Security Dashboard')).toBeInTheDocument()
        expect(screen.getByText('Vulnerability Management')).toBeInTheDocument()
        
        // Should hide non-matching items
        expect(screen.queryByText('AI Model Management')).not.toBeInTheDocument()
        expect(screen.queryByText('User & Team Management')).not.toBeInTheDocument()
      })
    })

    it('clears search and shows all items', async () => {
      const user = userEvent.setup()
      
      renderWithProviders(
        <EnhancedSidebar 
          collapsed={false}
          onCollapse={() => {}}
          userPermissions={['view:*']}
          notificationCounts={{}}
        />
      )

      const searchInput = screen.getByPlaceholderText(/search features/i)
      
      // Search
      await user.type(searchInput, 'security')
      
      await waitFor(() => {
        expect(screen.queryByText('AI Model Management')).not.toBeInTheDocument()
      })

      // Clear search
      await user.clear(searchInput)

      // Should show all items again
      await waitFor(() => {
        expect(screen.getByText('Security Dashboard')).toBeInTheDocument()
        expect(screen.getByText('AI Model Management')).toBeInTheDocument()
        expect(screen.getByText('User & Team Management')).toBeInTheDocument()
      })
    })
  })

  describe('Section Collapsing', () => {
    it('collapses and expands sidebar sections', async () => {
      const user = userEvent.setup()
      
      renderWithProviders(
        <EnhancedSidebar 
          collapsed={false}
          onCollapse={() => {}}
          userPermissions={['view:*']}
          notificationCounts={{}}
        />
      )

      // Find Security & Quality section
      const securitySection = screen.getByText('Security & Quality').closest('div')
      const collapseButton = within(securitySection!).getByRole('button', { name: /collapse section/i })

      // Initially expanded - items should be visible
      expect(screen.getByText('Security Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Vulnerability Management')).toBeInTheDocument()

      // Collapse section
      await user.click(collapseButton)

      // Items should be hidden
      await waitFor(() => {
        expect(screen.queryByText('Security Dashboard')).not.toBeInTheDocument()
        expect(screen.queryByText('Vulnerability Management')).not.toBeInTheDocument()
      })

      // Expand section again
      await user.click(collapseButton)

      // Items should be visible again
      await waitFor(() => {
        expect(screen.getByText('Security Dashboard')).toBeInTheDocument()
        expect(screen.getByText('Vulnerability Management')).toBeInTheDocument()
      })
    })

    it('persists section collapse state', async () => {
      const user = userEvent.setup()
      
      const { rerender } = renderWithProviders(
        <EnhancedSidebar 
          collapsed={false}
          onCollapse={() => {}}
          userPermissions={['view:*']}
          notificationCounts={{}}
        />
      )

      // Collapse a section
      const securitySection = screen.getByText('Security & Quality').closest('div')
      const collapseButton = within(securitySection!).getByRole('button', { name: /collapse section/i })
      await user.click(collapseButton)

      await waitFor(() => {
        expect(screen.queryByText('Security Dashboard')).not.toBeInTheDocument()
      })

      // Rerender component (simulating navigation or refresh)
      rerender(
        <QueryClientProvider client={new QueryClient()}>
          <BrowserRouter>
            <SidebarProvider>
              <EnhancedSidebar 
                collapsed={false}
                onCollapse={() => {}}
                userPermissions={['view:*']}
                notificationCounts={{}}
              />
            </SidebarProvider>
          </BrowserRouter>
        </QueryClientProvider>
      )

      // Section should remain collapsed
      await waitFor(() => {
        expect(screen.queryByText('Security Dashboard')).not.toBeInTheDocument()
      })
    })
  })
})
