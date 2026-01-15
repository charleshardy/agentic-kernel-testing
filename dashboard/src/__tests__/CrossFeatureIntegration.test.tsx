import React from 'react'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import SecurityDashboard from '../pages/SecurityDashboard'
import AIModelManagement from '../pages/AIModelManagement'
import AuditCompliance from '../pages/AuditCompliance'
import ResourceMonitoring from '../pages/ResourceMonitoring'
import AnalyticsInsights from '../pages/AnalyticsInsights'
import SecurityService from '../services/SecurityService'
import AIModelService from '../services/AIModelService'
import AuditService from '../services/AuditService'
import ResourceMonitoringService from '../services/ResourceMonitoringService'
import AnalyticsService from '../services/AnalyticsService'

// Mock services
jest.mock('../services/SecurityService')
jest.mock('../services/AIModelService')
jest.mock('../services/AuditService')
jest.mock('../services/ResourceMonitoringService')
jest.mock('../services/AnalyticsService')

const mockSecurityService = SecurityService as jest.Mocked<typeof SecurityService>
const mockAIModelService = AIModelService as jest.Mocked<typeof AIModelService>
const mockAuditService = AuditService as jest.Mocked<typeof AuditService>
const mockResourceMonitoringService = ResourceMonitoringService as jest.Mocked<typeof ResourceMonitoringService>
const mockAnalyticsService = AnalyticsService as jest.Mocked<typeof AnalyticsService>

const renderWithProviders = (component: React.ReactElement) => {
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
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Cross-Feature Integration Tests - Feature: missing-sidebar-functionality', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Security Dashboard Integration with Test Results', () => {
    it('integrates security findings with test execution data', async () => {
      const user = userEvent.setup()
      
      // Mock security finding linked to test execution
      const securityFinding = {
        id: 'vuln-001',
        severity: 'critical' as const,
        type: 'vulnerability' as const,
        title: 'Memory Leak in Kernel Module',
        description: 'Detected memory leak during stress testing',
        affectedComponents: ['kernel/mm/slab.c'],
        discoveredAt: new Date('2024-01-15T10:00:00Z'),
        status: 'open' as const,
        relatedTestCases: ['test-stress-001'],
        relatedExecutions: ['exec-123'],
        discoveryMethod: 'fuzzing' as const
      }

      mockSecurityService.getSecurityMetrics.mockResolvedValue({
        vulnerabilityCount: { critical: 1, high: 0, medium: 0, low: 0 },
        complianceScore: 75,
        activeFuzzingCampaigns: 2,
        recentFindings: [securityFinding],
        securityTrends: []
      })

      renderWithProviders(<SecurityDashboard />)

      // Wait for security data to load
      await waitFor(() => {
        expect(screen.getByText('Memory Leak in Kernel Module')).toBeInTheDocument()
      })

      // View finding details
      const findingCard = screen.getByText('Memory Leak in Kernel Module').closest('div')
      await user.click(findingCard!)

      // Should show related test execution
      await waitFor(() => {
        expect(screen.getByText(/related test execution/i)).toBeInTheDocument()
        expect(screen.getByText('exec-123')).toBeInTheDocument()
      })

      // Should show discovery method
      expect(screen.getByText(/discovered by: fuzzing/i)).toBeInTheDocument()

      // Click on test execution link
      const executionLink = screen.getByText('exec-123')
      await user.click(executionLink)

      // Should navigate to test execution details
      await waitFor(() => {
        expect(window.location.pathname).toContain('/test-execution/exec-123')
      })
    })

    it('tracks security violations in audit trail', async () => {
      const user = userEvent.setup()
      
      // Mock security violation event
      const auditEvent = {
        id: 'audit-001',
        timestamp: new Date('2024-01-15T11:00:00Z'),
        user: 'system',
        action: 'security_violation_detected',
        resource: 'deployment-456',
        details: {
          violationType: 'critical_vulnerability',
          vulnerabilityId: 'vuln-002',
          action: 'deployment_blocked'
        },
        ipAddress: '10.0.0.1',
        userAgent: 'AgenticTestingSystem/1.0'
      }

      mockAuditService.getAuditEvents.mockResolvedValue({
        events: [auditEvent],
        pagination: { page: 1, pageSize: 20, totalItems: 1, totalPages: 1 }
      })

      renderWithProviders(<AuditCompliance />)

      // Wait for audit events to load
      await waitFor(() => {
        expect(screen.getByText('security_violation_detected')).toBeInTheDocument()
      })

      // View audit event details
      const eventRow = screen.getByText('security_violation_detected').closest('tr')
      const viewButton = within(eventRow!).getByRole('button', { name: /view/i })
      await user.click(viewButton)

      // Should show violation details
      await waitFor(() => {
        expect(screen.getByText(/violation type/i)).toBeInTheDocument()
        expect(screen.getByText('critical_vulnerability')).toBeInTheDocument()
        expect(screen.getByText('deployment_blocked')).toBeInTheDocument()
      })

      // Should link to vulnerability
      expect(screen.getByText('vuln-002')).toBeInTheDocument()
    })
  })

  describe('AI Model Management Integration', () => {
    /**
     * Feature: missing-sidebar-functionality, Property 4: Model Performance Metrics Display
     * Validates: Requirements 2.3
     */
    it('displays comprehensive model performance metrics', async () => {
      const aiModel = {
        id: 'model-gpt4',
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
      }

      mockAIModelService.getModels.mockResolvedValue({
        models: [aiModel],
        pagination: { page: 1, pageSize: 20, totalItems: 1, totalPages: 1 }
      })

      renderWithProviders(<AIModelManagement />)

      // Wait for model data to load
      await waitFor(() => {
        expect(screen.getByText('GPT-4')).toBeInTheDocument()
      })

      // Should display all performance metrics
      expect(screen.getByText(/response time.*1200.*ms/i)).toBeInTheDocument()
      expect(screen.getByText(/accuracy.*95%/i)).toBeInTheDocument()
      expect(screen.getByText(/token usage.*50,000/i)).toBeInTheDocument()
      expect(screen.getByText(/cost.*\$0\.03/i)).toBeInTheDocument()
      expect(screen.getByText(/requests.*1,000/i)).toBeInTheDocument()
      expect(screen.getByText(/error rate.*1%/i)).toBeInTheDocument()
    })

    /**
     * Feature: missing-sidebar-functionality, Property 5: AI Model Fallback Behavior
     * Validates: Requirements 2.5
     */
    it('automatically switches to fallback model on failure', async () => {
      const user = userEvent.setup()
      
      const primaryModel = {
        id: 'model-gpt4',
        name: 'GPT-4',
        provider: 'openai' as const,
        version: '1.0',
        status: 'error' as const,
        metrics: {
          responseTime: 5000,
          accuracy: 0.5,
          tokenUsage: 10000,
          costPerRequest: 0.03,
          requestCount: 100,
          errorRate: 0.8
        },
        configuration: {
          endpoint: 'https://api.openai.com',
          apiKey: '***',
          maxTokens: 4000,
          temperature: 0.7,
          rateLimit: 100,
          timeout: 30000
        },
        fallbackModel: 'model-gpt35'
      }

      const fallbackModel = {
        id: 'model-gpt35',
        name: 'GPT-3.5',
        provider: 'openai' as const,
        version: '1.0',
        status: 'active' as const,
        metrics: {
          responseTime: 800,
          accuracy: 0.90,
          tokenUsage: 30000,
          costPerRequest: 0.01,
          requestCount: 500,
          errorRate: 0.02
        },
        configuration: {
          endpoint: 'https://api.openai.com',
          apiKey: '***',
          maxTokens: 4000,
          temperature: 0.7,
          rateLimit: 100,
          timeout: 30000
        }
      }

      mockAIModelService.getModels.mockResolvedValue({
        models: [primaryModel, fallbackModel],
        pagination: { page: 1, pageSize: 20, totalItems: 2, totalPages: 1 }
      })

      mockAIModelService.triggerFallback.mockResolvedValue({
        success: true,
        message: 'Switched to fallback model',
        fallbackModelId: 'model-gpt35'
      })

      renderWithProviders(<AIModelManagement />)

      // Wait for models to load
      await waitFor(() => {
        expect(screen.getByText('GPT-4')).toBeInTheDocument()
        expect(screen.getByText('GPT-3.5')).toBeInTheDocument()
      })

      // Primary model should show error status
      const gpt4Card = screen.getByText('GPT-4').closest('div')
      expect(within(gpt4Card!).getByText(/status.*error/i)).toBeInTheDocument()

      // Should show fallback indicator
      expect(within(gpt4Card!).getByText(/fallback.*gpt-3\.5/i)).toBeInTheDocument()

      // Trigger manual fallback
      const fallbackButton = within(gpt4Card!).getByRole('button', { name: /switch to fallback/i })
      await user.click(fallbackButton)

      // Should call fallback API
      await waitFor(() => {
        expect(mockAIModelService.triggerFallback).toHaveBeenCalledWith('model-gpt4')
      })

      // Should show success message
      expect(screen.getByText(/switched to fallback model/i)).toBeInTheDocument()
    })

    it('logs AI model usage in audit trail', async () => {
      const auditEvents = [
        {
          id: 'audit-002',
          timestamp: new Date('2024-01-15T12:00:00Z'),
          user: 'john.doe',
          action: 'ai_model_configuration_changed',
          resource: 'model-gpt4',
          details: {
            changes: {
              temperature: { old: 0.7, new: 0.9 },
              maxTokens: { old: 4000, new: 8000 }
            }
          },
          ipAddress: '10.0.0.5',
          userAgent: 'Mozilla/5.0'
        },
        {
          id: 'audit-003',
          timestamp: new Date('2024-01-15T12:30:00Z'),
          user: 'system',
          action: 'ai_model_fallback_triggered',
          resource: 'model-gpt4',
          details: {
            reason: 'high_error_rate',
            fallbackModel: 'model-gpt35',
            errorRate: 0.8
          },
          ipAddress: '10.0.0.1',
          userAgent: 'AgenticTestingSystem/1.0'
        }
      ]

      mockAuditService.getAuditEvents.mockResolvedValue({
        events: auditEvents,
        pagination: { page: 1, pageSize: 20, totalItems: 2, totalPages: 1 }
      })

      renderWithProviders(<AuditCompliance />)

      // Wait for audit events to load
      await waitFor(() => {
        expect(screen.getByText('ai_model_configuration_changed')).toBeInTheDocument()
        expect(screen.getByText('ai_model_fallback_triggered')).toBeInTheDocument()
      })

      // Should show AI model related events
      expect(screen.getByText('model-gpt4')).toBeInTheDocument()
      expect(screen.getByText('john.doe')).toBeInTheDocument()
      expect(screen.getByText('system')).toBeInTheDocument()
    })
  })

  describe('Resource Monitoring Integration', () => {
    it('correlates resource usage with test execution', async () => {
      const resourceMetrics = {
        infrastructure: {
          buildServers: [
            {
              id: 'build-01',
              name: 'Build Server 1',
              cpu: 85,
              memory: 70,
              storage: 60,
              network: 40,
              status: 'warning' as const,
              activeTests: ['test-001', 'test-002']
            }
          ],
          qemuHosts: [],
          physicalBoards: [],
          totalCapacity: {
            cpu: 100,
            memory: 100,
            storage: 100,
            network: 100
          }
        },
        capacity: {
          currentUsage: 75,
          projectedUsage: 90,
          recommendations: ['Scale up build servers', 'Optimize test parallelization']
        },
        performance: {
          avgResponseTime: 1200,
          throughput: 50,
          errorRate: 0.02
        },
        alerts: [
          {
            id: 'alert-001',
            severity: 'warning' as const,
            message: 'High CPU usage on build-01',
            resource: 'build-01',
            threshold: 80,
            currentValue: 85,
            timestamp: new Date()
          }
        ]
      }

      mockResourceMonitoringService.getResourceMetrics.mockResolvedValue(resourceMetrics)

      renderWithProviders(<ResourceMonitoring />)

      // Wait for resource data to load
      await waitFor(() => {
        expect(screen.getByText('Build Server 1')).toBeInTheDocument()
      })

      // Should show active tests on the server
      expect(screen.getByText(/active tests/i)).toBeInTheDocument()
      expect(screen.getByText('test-001')).toBeInTheDocument()
      expect(screen.getByText('test-002')).toBeInTheDocument()

      // Should show resource alert
      expect(screen.getByText('High CPU usage on build-01')).toBeInTheDocument()
      expect(screen.getByText(/85%/)).toBeInTheDocument()
    })

    it('provides capacity planning recommendations based on trends', async () => {
      const analyticsData = {
        metrics: {
          testExecutionRate: 100,
          averageExecutionTime: 300,
          successRate: 0.95,
          resourceUtilization: 75
        },
        trends: [
          {
            metric: 'resource_usage',
            direction: 'increasing' as const,
            rate: 0.15,
            prediction: 'Will exceed capacity in 30 days'
          }
        ],
        insights: [
          {
            id: 'insight-001',
            type: 'capacity_warning' as const,
            title: 'Resource Capacity Approaching Limit',
            description: 'Current growth rate will exceed capacity',
            recommendation: 'Add 2 more build servers',
            priority: 'high' as const,
            affectedResources: ['build-01', 'build-02']
          }
        ],
        predictions: {
          nextWeek: { usage: 80, confidence: 0.9 },
          nextMonth: { usage: 95, confidence: 0.75 }
        }
      }

      mockAnalyticsService.getAnalytics.mockResolvedValue(analyticsData)

      renderWithProviders(<AnalyticsInsights />)

      // Wait for analytics to load
      await waitFor(() => {
        expect(screen.getByText('Resource Capacity Approaching Limit')).toBeInTheDocument()
      })

      // Should show capacity warning
      expect(screen.getByText(/current growth rate will exceed capacity/i)).toBeInTheDocument()
      expect(screen.getByText(/add 2 more build servers/i)).toBeInTheDocument()

      // Should show predictions
      expect(screen.getByText(/next week.*80%/i)).toBeInTheDocument()
      expect(screen.getByText(/next month.*95%/i)).toBeInTheDocument()
    })
  })

  describe('Analytics Integration with All Features', () => {
    it('aggregates data from security, AI models, and resources', async () => {
      const analyticsData = {
        metrics: {
          testExecutionRate: 100,
          averageExecutionTime: 300,
          successRate: 0.95,
          resourceUtilization: 75,
          securityScore: 85,
          aiModelAccuracy: 0.93,
          complianceScore: 90
        },
        trends: [
          {
            metric: 'security_score',
            direction: 'increasing' as const,
            rate: 0.05,
            prediction: 'Improving security posture'
          },
          {
            metric: 'ai_accuracy',
            direction: 'stable' as const,
            rate: 0.0,
            prediction: 'Consistent AI performance'
          }
        ],
        insights: [
          {
            id: 'insight-002',
            type: 'optimization' as const,
            title: 'AI Model Optimization Opportunity',
            description: 'GPT-3.5 provides 90% accuracy at 1/3 the cost',
            recommendation: 'Use GPT-3.5 for non-critical analysis',
            priority: 'medium' as const,
            affectedResources: ['model-gpt4', 'model-gpt35']
          }
        ],
        predictions: {
          nextWeek: { usage: 80, confidence: 0.9 },
          nextMonth: { usage: 95, confidence: 0.75 }
        }
      }

      mockAnalyticsService.getAnalytics.mockResolvedValue(analyticsData)

      renderWithProviders(<AnalyticsInsights />)

      // Wait for analytics to load
      await waitFor(() => {
        expect(screen.getByText(/security score.*85/i)).toBeInTheDocument()
        expect(screen.getByText(/ai model accuracy.*93%/i)).toBeInTheDocument()
        expect(screen.getByText(/compliance score.*90/i)).toBeInTheDocument()
      })

      // Should show cross-feature insights
      expect(screen.getByText('AI Model Optimization Opportunity')).toBeInTheDocument()
      expect(screen.getByText(/gpt-3\.5 provides 90% accuracy/i)).toBeInTheDocument()

      // Should show trends from multiple features
      expect(screen.getByText(/improving security posture/i)).toBeInTheDocument()
      expect(screen.getByText(/consistent ai performance/i)).toBeInTheDocument()
    })
  })

  describe('Audit Trail Completeness', () => {
    /**
     * Feature: missing-sidebar-functionality, Property 7: Audit Event Logging Completeness
     * Validates: Requirements 3.4
     */
    it('logs complete audit events with all required fields', async () => {
      const auditEvent = {
        id: 'audit-004',
        timestamp: new Date('2024-01-15T13:00:00Z'),
        user: 'admin',
        action: 'user_permission_changed',
        resource: 'user-john-doe',
        details: {
          permissionsBefore: ['view:test-cases'],
          permissionsAfter: ['view:test-cases', 'create:test-cases', 'delete:test-cases'],
          changedBy: 'admin',
          reason: 'Promoted to senior developer'
        },
        ipAddress: '10.0.0.10',
        userAgent: 'Mozilla/5.0',
        sessionId: 'session-123',
        affectedResources: ['user-john-doe', 'role-developer']
      }

      mockAuditService.getAuditEvents.mockResolvedValue({
        events: [auditEvent],
        pagination: { page: 1, pageSize: 20, totalItems: 1, totalPages: 1 }
      })

      renderWithProviders(<AuditCompliance />)

      // Wait for audit event to load
      await waitFor(() => {
        expect(screen.getByText('user_permission_changed')).toBeInTheDocument()
      })

      // View event details
      const eventRow = screen.getByText('user_permission_changed').closest('tr')
      const viewButton = within(eventRow!).getByRole('button', { name: /view/i })
      await userEvent.setup().click(viewButton)

      // Should display all required fields
      await waitFor(() => {
        expect(screen.getByText(/timestamp/i)).toBeInTheDocument()
        expect(screen.getByText('2024-01-15')).toBeInTheDocument()
        
        expect(screen.getByText(/user/i)).toBeInTheDocument()
        expect(screen.getByText('admin')).toBeInTheDocument()
        
        expect(screen.getByText(/action/i)).toBeInTheDocument()
        expect(screen.getByText('user_permission_changed')).toBeInTheDocument()
        
        expect(screen.getByText(/resource/i)).toBeInTheDocument()
        expect(screen.getByText('user-john-doe')).toBeInTheDocument()
        
        expect(screen.getByText(/ip address/i)).toBeInTheDocument()
        expect(screen.getByText('10.0.0.10')).toBeInTheDocument()
        
        expect(screen.getByText(/affected resources/i)).toBeInTheDocument()
        expect(screen.getByText('role-developer')).toBeInTheDocument()
      })
    })

    /**
     * Feature: missing-sidebar-functionality, Property 18: Audit Trail Data Masking
     * Validates: Requirements 15.2
     */
    it('masks sensitive data in audit trail display', async () => {
      const auditEvent = {
        id: 'audit-005',
        timestamp: new Date('2024-01-15T14:00:00Z'),
        user: 'admin',
        action: 'api_key_created',
        resource: 'integration-github',
        details: {
          apiKey: '***MASKED***',
          endpoint: 'https://api.github.com',
          permissions: ['read:repo', 'write:status']
        },
        ipAddress: '10.0.0.10',
        userAgent: 'Mozilla/5.0'
      }

      mockAuditService.getAuditEvents.mockResolvedValue({
        events: [auditEvent],
        pagination: { page: 1, pageSize: 20, totalItems: 1, totalPages: 1 }
      })

      renderWithProviders(<AuditCompliance />)

      // Wait for audit event to load
      await waitFor(() => {
        expect(screen.getByText('api_key_created')).toBeInTheDocument()
      })

      // View event details
      const eventRow = screen.getByText('api_key_created').closest('tr')
      const viewButton = within(eventRow!).getByRole('button', { name: /view/i })
      await userEvent.setup().click(viewButton)

      // Should show masked API key
      await waitFor(() => {
        expect(screen.getByText('***MASKED***')).toBeInTheDocument()
      })

      // Should NOT show actual API key
      expect(screen.queryByText(/sk-[a-zA-Z0-9]+/)).not.toBeInTheDocument()
      expect(screen.queryByText(/ghp_[a-zA-Z0-9]+/)).not.toBeInTheDocument()
    })
  })

  describe('Data Consistency Across Features', () => {
    it('maintains consistent user data across all features', async () => {
      const user = userEvent.setup()
      
      // Same user data should appear consistently
      const userData = {
        id: 'user-001',
        username: 'john.doe',
        email: 'john.doe@example.com',
        firstName: 'John',
        lastName: 'Doe'
      }

      // Mock user in audit events
      mockAuditService.getAuditEvents.mockResolvedValue({
        events: [{
          id: 'audit-006',
          timestamp: new Date(),
          user: 'john.doe',
          action: 'test_executed',
          resource: 'test-001',
          details: {},
          ipAddress: '10.0.0.5',
          userAgent: 'Mozilla/5.0'
        }],
        pagination: { page: 1, pageSize: 20, totalItems: 1, totalPages: 1 }
      })

      // Mock user in security events
      mockSecurityService.getSecurityMetrics.mockResolvedValue({
        vulnerabilityCount: { critical: 0, high: 0, medium: 0, low: 0 },
        complianceScore: 100,
        activeFuzzingCampaigns: 0,
        recentFindings: [{
          id: 'vuln-003',
          severity: 'low' as const,
          type: 'vulnerability' as const,
          title: 'Minor Issue',
          description: 'Minor security issue',
          affectedComponents: [],
          discoveredAt: new Date(),
          status: 'resolved' as const,
          resolvedBy: 'john.doe'
        }],
        securityTrends: []
      })

      // Check audit trail
      const { rerender } = renderWithProviders(<AuditCompliance />)
      
      await waitFor(() => {
        expect(screen.getByText('john.doe')).toBeInTheDocument()
      })

      // Switch to security dashboard
      rerender(
        <QueryClientProvider client={new QueryClient()}>
          <BrowserRouter>
            <SecurityDashboard />
          </BrowserRouter>
        </QueryClientProvider>
      )

      // Same user should appear with consistent data
      await waitFor(() => {
        expect(screen.getByText('john.doe')).toBeInTheDocument()
      })
    })
  })
})
