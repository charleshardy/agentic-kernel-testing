import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Pause, 
  Play,
  RotateCcw,
  Eye,
  Filter,
  Grid,
  List,
  TrendingUp,
  AlertTriangle
} from 'lucide-react';
import DeploymentMonitor from './DeploymentMonitor';

// Types for parallel deployment monitoring
interface DeploymentSummary {
  deployment_id: string;
  plan_id: string;
  environment_id: string;
  status: string;
  start_time: string;
  end_time?: string;
  duration_seconds?: number;
  completion_percentage: number;
  artifacts_deployed: number;
  error_message?: string;
  retry_count: number;
}

interface DeploymentMetrics {
  total_deployments: number;
  successful_deployments: number;
  failed_deployments: number;
  cancelled_deployments: number;
  active_deployments: number;
  queue_size: number;
  average_duration_seconds: number;
  retry_count: number;
  environment_usage: Record<string, number>;
}

interface ParallelDeploymentMonitorProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
  maxDeployments?: number;
}

const ParallelDeploymentMonitor: React.FC<ParallelDeploymentMonitorProps> = ({
  autoRefresh = true,
  refreshInterval = 3000,
  maxDeployments = 50
}) => {
  const [deployments, setDeployments] = useState<DeploymentSummary[]>([]);
  const [metrics, setMetrics] = useState<DeploymentMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(autoRefresh);
  const [selectedDeployment, setSelectedDeployment] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [environmentFilter, setEnvironmentFilter] = useState<string>('all');

  // Fetch deployment history and metrics
  const fetchDeployments = useCallback(async () => {
    try {
      const [deploymentsResponse, metricsResponse] = await Promise.all([
        fetch(`/api/v1/deployments/history?limit=${maxDeployments}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }),
        fetch('/api/v1/deployments/metrics', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        })
      ]);

      if (!deploymentsResponse.ok || !metricsResponse.ok) {
        throw new Error('Failed to fetch deployment data');
      }

      const deploymentsData = await deploymentsResponse.json();
      const metricsData = await metricsResponse.json();

      setDeployments(deploymentsData.deployments || []);
      setMetrics(metricsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  }, [maxDeployments]);

  // Auto-refresh effect
  useEffect(() => {
    fetchDeployments();

    if (isRefreshing) {
      const interval = setInterval(fetchDeployments, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchDeployments, isRefreshing, refreshInterval]);

  // Get status badge variant
  const getStatusBadgeVariant = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'default';
      case 'failed': return 'destructive';
      case 'cancelled': return 'secondary';
      case 'pending': return 'outline';
      default: return 'outline';
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'cancelled': return <Pause className="h-4 w-4 text-gray-500" />;
      case 'pending': return <Clock className="h-4 w-4 text-yellow-500" />;
      default: return <Activity className="h-4 w-4 text-blue-500" />;
    }
  };

  // Format duration
  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  // Filter deployments
  const filteredDeployments = deployments.filter(deployment => {
    if (statusFilter !== 'all' && deployment.status !== statusFilter) {
      return false;
    }
    if (environmentFilter !== 'all' && deployment.environment_id !== environmentFilter) {
      return false;
    }
    return true;
  });

  // Get unique environments for filter
  const uniqueEnvironments = Array.from(new Set(deployments.map(d => d.environment_id)));

  // Calculate summary statistics
  const activeDeploys = filteredDeployments.filter(d => 
    !['completed', 'failed', 'cancelled'].includes(d.status)
  );
  const completedDeploys = filteredDeployments.filter(d => d.status === 'completed');
  const failedDeploys = filteredDeployments.filter(d => d.status === 'failed');

  if (selectedDeployment) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Button 
            variant="outline" 
            onClick={() => setSelectedDeployment(null)}
          >
            ← Back to Overview
          </Button>
        </div>
        <DeploymentMonitor 
          deploymentId={selectedDeployment}
          onClose={() => setSelectedDeployment(null)}
        />
      </div>
    );
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <Activity className="h-6 w-6 animate-spin mr-2" />
            Loading deployment data...
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <Button onClick={fetchDeployments} className="mt-4">
            <RotateCcw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center">
              <Activity className="h-5 w-5 mr-2" />
              Parallel Deployment Monitor
            </CardTitle>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsRefreshing(!isRefreshing)}
              >
                {isRefreshing ? <Pause className="h-4 w-4 mr-2" /> : <Play className="h-4 w-4 mr-2" />}
                {isRefreshing ? 'Pause' : 'Resume'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
              >
                {viewMode === 'grid' ? <List className="h-4 w-4" /> : <Grid className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="flex flex-wrap gap-4 mb-4">
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="border rounded px-2 py-1 text-sm"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="preparing">Preparing</option>
                <option value="connecting">Connecting</option>
                <option value="installing_dependencies">Installing</option>
                <option value="deploying_scripts">Deploying</option>
                <option value="configuring_instrumentation">Configuring</option>
                <option value="validating">Validating</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            <div className="flex items-center space-x-2">
              <select
                value={environmentFilter}
                onChange={(e) => setEnvironmentFilter(e.target.value)}
                className="border rounded px-2 py-1 text-sm"
              >
                <option value="all">All Environments</option>
                {uniqueEnvironments.map(env => (
                  <option key={env} value={env}>{env}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Summary Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{activeDeploys.length}</div>
              <div className="text-sm text-gray-500">Active</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{completedDeploys.length}</div>
              <div className="text-sm text-gray-500">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{failedDeploys.length}</div>
              <div className="text-sm text-gray-500">Failed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">{metrics?.queue_size || 0}</div>
              <div className="text-sm text-gray-500">Queued</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Overview */}
      {metrics && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="h-5 w-5 mr-2" />
              Performance Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm font-medium text-gray-500">Success Rate</p>
                <p className="text-lg font-semibold">
                  {metrics.total_deployments > 0 
                    ? Math.round((metrics.successful_deployments / metrics.total_deployments) * 100)
                    : 0}%
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500">Avg Duration</p>
                <p className="text-lg font-semibold">
                  {formatDuration(metrics.average_duration_seconds)}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500">Total Retries</p>
                <p className="text-lg font-semibold">{metrics.retry_count}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500">Environments</p>
                <p className="text-lg font-semibold">{Object.keys(metrics.environment_usage).length}</p>
              </div>
            </div>

            {/* Environment Usage */}
            {Object.keys(metrics.environment_usage).length > 0 && (
              <div className="mt-4">
                <h4 className="font-medium mb-2">Environment Usage</h4>
                <div className="space-y-2">
                  {Object.entries(metrics.environment_usage).map(([env, usage]) => (
                    <div key={env} className="flex items-center justify-between">
                      <span className="text-sm">{env}</span>
                      <div className="flex items-center space-x-2">
                        <Progress value={(usage / 3) * 100} className="w-20 h-2" />
                        <span className="text-sm text-gray-500">{usage}/3</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Deployments Display */}
      <Card>
        <CardHeader>
          <CardTitle>
            Deployments ({filteredDeployments.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredDeployments.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              No deployments found matching the current filters
            </div>
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredDeployments.map((deployment) => (
                <Card key={deployment.deployment_id} className="cursor-pointer hover:shadow-md transition-shadow">
                  <CardContent className="p-4" onClick={() => setSelectedDeployment(deployment.deployment_id)}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(deployment.status)}
                        <span className="font-medium text-sm truncate">
                          {deployment.deployment_id}
                        </span>
                      </div>
                      <Badge variant={getStatusBadgeVariant(deployment.status)} className="text-xs">
                        {deployment.status.toUpperCase()}
                      </Badge>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="text-xs text-gray-500">
                        <div>Plan: {deployment.plan_id}</div>
                        <div>Env: {deployment.environment_id}</div>
                      </div>
                      
                      <div className="flex justify-between text-xs">
                        <span>Duration: {formatDuration(deployment.duration_seconds)}</span>
                        <span>Artifacts: {deployment.artifacts_deployed}</span>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span>Progress</span>
                          <span>{Math.round(deployment.completion_percentage)}%</span>
                        </div>
                        <Progress value={deployment.completion_percentage} className="h-1" />
                      </div>
                      
                      {deployment.error_message && (
                        <div className="text-xs text-red-600 truncate">
                          {deployment.error_message}
                        </div>
                      )}
                      
                      {deployment.retry_count > 0 && (
                        <div className="text-xs text-orange-600">
                          Retries: {deployment.retry_count}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredDeployments.map((deployment) => (
                <div 
                  key={deployment.deployment_id}
                  className="flex items-center justify-between p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                  onClick={() => setSelectedDeployment(deployment.deployment_id)}
                >
                  <div className="flex items-center space-x-4 flex-1">
                    {getStatusIcon(deployment.status)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium truncate">{deployment.deployment_id}</span>
                        <Badge variant={getStatusBadgeVariant(deployment.status)} className="text-xs">
                          {deployment.status.toUpperCase()}
                        </Badge>
                      </div>
                      <div className="text-sm text-gray-500 truncate">
                        {deployment.plan_id} • {deployment.environment_id}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 text-sm">
                    <div className="text-center">
                      <div className="font-medium">{Math.round(deployment.completion_percentage)}%</div>
                      <div className="text-xs text-gray-500">Progress</div>
                    </div>
                    <div className="text-center">
                      <div className="font-medium">{formatDuration(deployment.duration_seconds)}</div>
                      <div className="text-xs text-gray-500">Duration</div>
                    </div>
                    <div className="text-center">
                      <div className="font-medium">{deployment.artifacts_deployed}</div>
                      <div className="text-xs text-gray-500">Artifacts</div>
                    </div>
                    <Button variant="outline" size="sm">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ParallelDeploymentMonitor;