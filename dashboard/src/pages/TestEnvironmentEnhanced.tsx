import React, { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Activity, 
  Server, 
  Deployment,
  TrendingUp,
  Settings,
  Eye
} from 'lucide-react'
import EnvironmentManagementDashboard from '../components/EnvironmentManagementDashboard'
import ParallelDeploymentMonitor from '../components/ParallelDeploymentMonitor'
import DeploymentMonitor from '../components/DeploymentMonitor'

/**
 * Enhanced Test Environment page with integrated deployment monitoring
 * Provides comprehensive environment management and deployment tracking
 */
const TestEnvironmentEnhanced: React.FC = () => {
  const [searchParams] = useSearchParams()
  const planId = searchParams.get('planId')
  const [selectedDeployment, setSelectedDeployment] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('environments')

  // Mock deployment data for demonstration
  const [recentDeployments] = useState([
    {
      id: 'deploy_001',
      environment: 'qemu-x86-64',
      status: 'completed',
      progress: 100,
      duration: '2m 34s',
      artifacts: 3
    },
    {
      id: 'deploy_002', 
      environment: 'physical-arm64',
      status: 'running',
      progress: 67,
      duration: '1m 12s',
      artifacts: 2
    },
    {
      id: 'deploy_003',
      environment: 'qemu-arm64',
      status: 'failed',
      progress: 45,
      duration: '3m 01s',
      artifacts: 1
    }
  ])

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed': return 'default'
      case 'running': return 'outline'
      case 'failed': return 'destructive'
      default: return 'secondary'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600'
      case 'running': return 'text-blue-600'
      case 'failed': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  if (selectedDeployment) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Button 
            variant="outline" 
            onClick={() => setSelectedDeployment(null)}
          >
            ← Back to Environment Overview
          </Button>
        </div>
        <DeploymentMonitor 
          deploymentId={selectedDeployment}
          onClose={() => setSelectedDeployment(null)}
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Test Environment Management</h1>
          <p className="text-gray-600">Monitor environments and deployment activities</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-2" />
            Configure
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Active Environments</p>
                <p className="text-2xl font-bold">5</p>
              </div>
              <Server className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Running Deployments</p>
                <p className="text-2xl font-bold">3</p>
              </div>
              <Activity className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Success Rate</p>
                <p className="text-2xl font-bold">94%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Queue Size</p>
                <p className="text-2xl font-bold">2</p>
              </div>
              <Deployment className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Deployments Summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center">
              <Activity className="h-5 w-5 mr-2" />
              Recent Deployment Activity
            </CardTitle>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => setActiveTab('deployments')}
            >
              View All
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentDeployments.map((deployment) => (
              <div 
                key={deployment.id}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
                onClick={() => setSelectedDeployment(deployment.id)}
              >
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${
                    deployment.status === 'completed' ? 'bg-green-500' :
                    deployment.status === 'running' ? 'bg-blue-500' : 'bg-red-500'
                  }`} />
                  <div>
                    <p className="font-medium">{deployment.id}</p>
                    <p className="text-sm text-gray-500">{deployment.environment}</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <p className="text-sm font-medium">{deployment.progress}%</p>
                    <p className="text-xs text-gray-500">{deployment.duration}</p>
                  </div>
                  <Badge variant={getStatusBadgeVariant(deployment.status)}>
                    {deployment.status.toUpperCase()}
                  </Badge>
                  <Button variant="outline" size="sm">
                    <Eye className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="environments" className="flex items-center">
            <Server className="h-4 w-4 mr-2" />
            Environments
          </TabsTrigger>
          <TabsTrigger value="deployments" className="flex items-center">
            <Activity className="h-4 w-4 mr-2" />
            Deployments
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center">
            <TrendingUp className="h-4 w-4 mr-2" />
            Analytics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="environments" className="mt-6">
          <EnvironmentManagementDashboard 
            planId={planId || undefined}
            autoRefresh={true}
            refreshInterval={2000}
          />
        </TabsContent>

        <TabsContent value="deployments" className="mt-6">
          <ParallelDeploymentMonitor 
            autoRefresh={true}
            refreshInterval={3000}
            maxDeployments={50}
          />
        </TabsContent>

        <TabsContent value="analytics" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Deployment Success Rate Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Deployment Success Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <TrendingUp className="h-12 w-12 mx-auto mb-2" />
                    <p>Success rate analytics would be displayed here</p>
                    <p className="text-sm">Integration with analytics API pending</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Environment Utilization */}
            <Card>
              <CardHeader>
                <CardTitle>Environment Utilization</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">QEMU x86-64</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-600 h-2 rounded-full" style={{width: '75%'}}></div>
                      </div>
                      <span className="text-sm text-gray-500">75%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Physical ARM64</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div className="bg-green-600 h-2 rounded-full" style={{width: '45%'}}></div>
                      </div>
                      <span className="text-sm text-gray-500">45%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">QEMU ARM64</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div className="bg-purple-600 h-2 rounded-full" style={{width: '60%'}}></div>
                      </div>
                      <span className="text-sm text-gray-500">60%</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Deployment Timeline */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Deployment Timeline</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-32 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <Activity className="h-8 w-8 mx-auto mb-2" />
                    <p>Deployment timeline visualization would be displayed here</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default TestEnvironmentEnhanced