import React, { useState, useEffect } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import { 
  Play, 
  Pause,
  Square,
  Activity, 
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Deployment,
  TrendingUp,
  Eye,
  Plus,
  RotateCcw
} from 'lucide-react'
import DeploymentMonitor from '../components/DeploymentMonitor'
import ParallelDeploymentMonitor from '../components/ParallelDeploymentMonitor'

/**
 * Enhanced Test Execution page with integrated deployment monitoring
 * Provides comprehensive test execution and deployment tracking
 */
const TestExecutionEnhanced: React.FC = () => {
  const [selectedDeployment, setSelectedDeployment] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('execution')
  const [executionMetrics, setExecutionMetrics] = useState({
    activeTests: 12,
    queuedTests: 8,
    completedToday: 45,
    successRate: 87
  })

  // Mock active executions data
  const [activeExecutions] = useState([
    {
      id: 'exec_001',
      testName: 'Memory Management Stress Test',
      environment: 'qemu-x86-64',
      status: 'running',
      progress: 65,
      duration: '4m 23s',
      deploymentId: 'deploy_001'
    },
    {
      id: 'exec_002',
      testName: 'Network Stack Validation',
      environment: 'physical-arm64',
      status: 'deploying',
      progress: 25,
      duration: '1m 45s',
      deploymentId: 'deploy_002'
    },
    {
      id: 'exec_003',
      testName: 'File System Integrity Check',
      environment: 'qemu-arm64',
      status: 'queued',
      progress: 0,
      duration: '0s',
      deploymentId: null
    }
  ])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Play className="h-4 w-4 text-green-500" />
      case 'deploying': return <Activity className="h-4 w-4 text-blue-500" />
      case 'queued': return <Clock className="h-4 w-4 text-yellow-500" />
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />
      default: return <AlertTriangle className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'running': return 'default'
      case 'deploying': return 'outline'
      case 'queued': return 'secondary'
      case 'completed': return 'default'
      case 'failed': return 'destructive'
      default: return 'secondary'
    }
  }

  const handleStartDeployment = async (testId: string) => {
    // Mock deployment start
    console.log(`Starting deployment for test ${testId}`)
    // In real implementation, this would call the deployment API
  }

  const handleViewDeployment = (deploymentId: string) => {
    setSelectedDeployment(deploymentId)
  }

  if (selectedDeployment) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Button 
            variant="outline" 
            onClick={() => setSelectedDeployment(null)}
          >
            ← Back to Test Execution
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
          <h1 className="text-3xl font-bold">Test Execution & Deployment</h1>
          <p className="text-gray-600">Monitor test execution and deployment activities</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Plus className="h-4 w-4 mr-2" />
            New Test
          </Button>
          <Button variant="outline" size="sm">
            <Deployment className="h-4 w-4 mr-2" />
            Deploy
          </Button>
        </div>
      </div>

      {/* Execution Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Active Tests</p>
                <p className="text-2xl font-bold">{executionMetrics.activeTests}</p>
              </div>
              <Play className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Queued Tests</p>
                <p className="text-2xl font-bold">{executionMetrics.queuedTests}</p>
              </div>
              <Clock className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Completed Today</p>
                <p className="text-2xl font-bold">{executionMetrics.completedToday}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Success Rate</p>
                <p className="text-2xl font-bold">{executionMetrics.successRate}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Executions Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center">
              <Activity className="h-5 w-5 mr-2" />
              Active Test Executions
            </CardTitle>
            <Button variant="outline" size="sm">
              <RotateCcw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {activeExecutions.map((execution) => (
              <div key={execution.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(execution.status)}
                    <div>
                      <h4 className="font-medium">{execution.testName}</h4>
                      <p className="text-sm text-gray-500">
                        {execution.environment} • {execution.duration}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={getStatusBadgeVariant(execution.status)}>
                      {execution.status.toUpperCase()}
                    </Badge>
                    {execution.deploymentId && (
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleViewDeployment(execution.deploymentId!)}
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        Deployment
                      </Button>
                    )}
                  </div>
                </div>
                
                {execution.progress > 0 && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Progress</span>
                      <span>{execution.progress}%</span>
                    </div>
                    <Progress value={execution.progress} className="h-2" />
                  </div>
                )}
                
                {execution.status === 'queued' && (
                  <div className="mt-3">
                    <Button 
                      size="sm" 
                      onClick={() => handleStartDeployment(execution.id)}
                    >
                      <Deployment className="h-4 w-4 mr-2" />
                      Start Deployment
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="execution" className="flex items-center">
            <Play className="h-4 w-4 mr-2" />
            Test Execution
          </TabsTrigger>
          <TabsTrigger value="deployments" className="flex items-center">
            <Deployment className="h-4 w-4 mr-2" />
            Deployments
          </TabsTrigger>
          <TabsTrigger value="monitoring" className="flex items-center">
            <Activity className="h-4 w-4 mr-2" />
            Live Monitoring
          </TabsTrigger>
        </TabsList>

        <TabsContent value="execution" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Test Queue */}
            <Card>
              <CardHeader>
                <CardTitle>Test Queue</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="flex items-center justify-between p-3 border rounded">
                      <div>
                        <p className="font-medium">Queued Test {i}</p>
                        <p className="text-sm text-gray-500">Waiting for environment</p>
                      </div>
                      <Badge variant="secondary">QUEUED</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Recent Results */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { name: 'Kernel Boot Test', status: 'passed', time: '2m ago' },
                    { name: 'Memory Leak Detection', status: 'failed', time: '5m ago' },
                    { name: 'Network Performance', status: 'passed', time: '8m ago' },
                    { name: 'File System Check', status: 'passed', time: '12m ago' }
                  ].map((result, i) => (
                    <div key={i} className="flex items-center justify-between p-3 border rounded">
                      <div>
                        <p className="font-medium">{result.name}</p>
                        <p className="text-sm text-gray-500">{result.time}</p>
                      </div>
                      <Badge variant={result.status === 'passed' ? 'default' : 'destructive'}>
                        {result.status.toUpperCase()}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="deployments" className="mt-6">
          <ParallelDeploymentMonitor 
            autoRefresh={true}
            refreshInterval={3000}
            maxDeployments={50}
          />
        </TabsContent>

        <TabsContent value="monitoring" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* System Resources */}
            <Card>
              <CardHeader>
                <CardTitle>System Resources</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>CPU Usage</span>
                      <span>45%</span>
                    </div>
                    <Progress value={45} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Memory Usage</span>
                      <span>67%</span>
                    </div>
                    <Progress value={67} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Disk I/O</span>
                      <span>23%</span>
                    </div>
                    <Progress value={23} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Network</span>
                      <span>12%</span>
                    </div>
                    <Progress value={12} className="h-2" />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Environment Status */}
            <Card>
              <CardHeader>
                <CardTitle>Environment Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { name: 'QEMU x86-64', status: 'healthy', load: 'Medium' },
                    { name: 'Physical ARM64', status: 'healthy', load: 'Low' },
                    { name: 'QEMU ARM64', status: 'warning', load: 'High' },
                    { name: 'Container x86-64', status: 'healthy', load: 'Low' }
                  ].map((env, i) => (
                    <div key={i} className="flex items-center justify-between p-3 border rounded">
                      <div className="flex items-center space-x-3">
                        <div className={`w-3 h-3 rounded-full ${
                          env.status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'
                        }`} />
                        <div>
                          <p className="font-medium">{env.name}</p>
                          <p className="text-sm text-gray-500">Load: {env.load}</p>
                        </div>
                      </div>
                      <Badge variant={env.status === 'healthy' ? 'default' : 'outline'}>
                        {env.status.toUpperCase()}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Live Logs */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Live Execution Logs</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-black text-green-400 p-4 rounded-lg font-mono text-sm h-64 overflow-y-auto">
                  <div className="space-y-1">
                    <div>[2024-01-04 10:23:45] Starting test execution on qemu-x86-64</div>
                    <div>[2024-01-04 10:23:46] Deploying test artifacts...</div>
                    <div>[2024-01-04 10:23:48] <span className="text-blue-400">INFO</span> Kernel boot sequence initiated</div>
                    <div>[2024-01-04 10:23:52] <span className="text-green-400">SUCCESS</span> Environment ready for testing</div>
                    <div>[2024-01-04 10:23:53] Running memory management tests...</div>
                    <div>[2024-01-04 10:23:55] <span className="text-yellow-400">WARN</span> High memory usage detected</div>
                    <div>[2024-01-04 10:23:57] Test progress: 65% complete</div>
                    <div>[2024-01-04 10:23:58] <span className="text-blue-400">INFO</span> Collecting performance metrics</div>
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

export default TestExecutionEnhanced