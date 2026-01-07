import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Activity,
  Calendar,
  Filter,
  Download,
  RefreshCw,
  Server,
  Cpu,
  HardDrive,
  Network
} from 'lucide-react';

// Types for analytics data
interface DeploymentMetrics {
  total_deployments: number;
  successful_deployments: number;
  failed_deployments: number;
  cancelled_deployments: number;
  average_duration_seconds: number;
  success_rate_percentage: number;
  retry_rate_percentage: number;
  environment_utilization: Record<string, number>;
  failure_categories: Record<string, number>;
  performance_trends: {
    date: string;
    deployments: number;
    success_rate: number;
    average_duration: number;
  }[];
}

interface EnvironmentAnalytics {
  environment_id: string;
  environment_type: string;
  total_deployments: number;
  successful_deployments: number;
  failed_deployments: number;
  average_duration_seconds: number;
  resource_efficiency: {
    cpu_utilization: number;
    memory_utilization: number;
    disk_utilization: number;
  };
  failure_reasons: Record<string, number>;
  peak_usage_hours: number[];
}

interface TimeRangeFilter {
  label: string;
  value: string;
  days: number;
}

interface DeploymentAnalyticsProps {
  className?: string;
}

const DeploymentAnalytics: React.FC<DeploymentAnalyticsProps> = ({
  className = ""
}) => {
  const [metrics, setMetrics] = useState<DeploymentMetrics | null>(null);
  const [environmentAnalytics, setEnvironmentAnalytics] = useState<EnvironmentAnalytics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('7d');
  const [selectedEnvironment, setSelectedEnvironment] = useState<string>('all');

  const timeRangeOptions: TimeRangeFilter[] = [
    { label: 'Last 24 Hours', value: '1d', days: 1 },
    { label: 'Last 7 Days', value: '7d', days: 7 },
    { label: 'Last 30 Days', value: '30d', days: 30 },
    { label: 'Last 90 Days', value: '90d', days: 90 }
  ];

  // Fetch analytics data
  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      const [metricsResponse, environmentsResponse] = await Promise.all([
        fetch(`/api/v1/deployments/analytics?time_range=${timeRange}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }),
        fetch(`/api/v1/deployments/analytics/environments?time_range=${timeRange}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        })
      ]);

      if (!metricsResponse.ok || !environmentsResponse.ok) {
        throw new Error('Failed to fetch analytics data');
      }

      const metricsData = await metricsResponse.json();
      const environmentsData = await environmentsResponse.json();

      setMetrics(metricsData);
      setEnvironmentAnalytics(environmentsData.environments || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  // Export analytics data
  const exportAnalytics = async () => {
    try {
      const response = await fetch(`/api/v1/deployments/analytics/export?time_range=${timeRange}&format=csv`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `deployment_analytics_${timeRange}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      console.error('Failed to export analytics:', err);
    }
  };

  // Format duration
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  // Get trend indicator
  const getTrendIndicator = (current: number, previous: number) => {
    if (current > previous) {
      return <TrendingUp className="h-4 w-4 text-green-500" />;
    } else if (current < previous) {
      return <TrendingDown className="h-4 w-4 text-red-500" />;
    }
    return <div className="h-4 w-4" />;
  };

  // Get environment type icon
  const getEnvironmentTypeIcon = (type: string) => {
    switch (type) {
      case 'qemu': return <Server className="h-4 w-4" />;
      case 'physical': return <Cpu className="h-4 w-4" />;
      case 'cloud': return <Network className="h-4 w-4" />;
      default: return <Server className="h-4 w-4" />;
    }
  };

  if (loading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center">
              <Activity className="h-6 w-6 animate-spin mr-2" />
              Loading analytics data...
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`space-y-6 ${className}`}>
        <Card>
          <CardContent className="p-6">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
            <Button onClick={fetchAnalytics} className="mt-4">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className={`space-y-6 ${className}`}>
        <Card>
          <CardContent className="p-6">
            <div className="text-center text-gray-500">
              No analytics data available
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Deployment Analytics</h2>
          <p className="text-gray-500">Performance insights and trends</p>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
          >
            {timeRangeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <Button variant="outline" size="sm" onClick={exportAnalytics}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" size="sm" onClick={fetchAnalytics}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Total Deployments</p>
                <p className="text-2xl font-bold">{metrics.total_deployments}</p>
              </div>
              <BarChart3 className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Success Rate</p>
                <p className="text-2xl font-bold">{metrics.success_rate_percentage.toFixed(1)}%</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Avg Duration</p>
                <p className="text-2xl font-bold">{formatDuration(metrics.average_duration_seconds)}</p>
              </div>
              <Clock className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Retry Rate</p>
                <p className="text-2xl font-bold">{metrics.retry_rate_percentage.toFixed(1)}%</p>
              </div>
              <RefreshCw className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts and Detailed Analytics */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="environments">Environments</TabsTrigger>
          <TabsTrigger value="failures">Failure Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Success vs Failure Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <PieChart className="h-5 w-5 mr-2" />
                  Deployment Status Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <span className="text-sm">Successful</span>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">{metrics.successful_deployments}</div>
                      <div className="text-xs text-gray-500">
                        {((metrics.successful_deployments / metrics.total_deployments) * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                  <Progress 
                    value={(metrics.successful_deployments / metrics.total_deployments) * 100} 
                    className="h-2"
                  />

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      <span className="text-sm">Failed</span>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">{metrics.failed_deployments}</div>
                      <div className="text-xs text-gray-500">
                        {((metrics.failed_deployments / metrics.total_deployments) * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                  <Progress 
                    value={(metrics.failed_deployments / metrics.total_deployments) * 100} 
                    className="h-2"
                  />

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
                      <span className="text-sm">Cancelled</span>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">{metrics.cancelled_deployments}</div>
                      <div className="text-xs text-gray-500">
                        {((metrics.cancelled_deployments / metrics.total_deployments) * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                  <Progress 
                    value={(metrics.cancelled_deployments / metrics.total_deployments) * 100} 
                    className="h-2"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Environment Utilization */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Server className="h-5 w-5 mr-2" />
                  Environment Utilization
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(metrics.environment_utilization).map(([env, usage]) => (
                    <div key={env}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium">{env}</span>
                        <span className="text-sm text-gray-500">{usage} deployments</span>
                      </div>
                      <Progress 
                        value={(usage / Math.max(...Object.values(metrics.environment_utilization))) * 100} 
                        className="h-2"
                      />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="trends" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <TrendingUp className="h-5 w-5 mr-2" />
                Performance Trends
              </CardTitle>
            </CardHeader>
            <CardContent>
              {metrics.performance_trends.length > 0 ? (
                <div className="space-y-4">
                  {/* Simple trend visualization */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center">
                      <p className="text-sm text-gray-500">Deployments Trend</p>
                      <div className="flex items-center justify-center space-x-2">
                        <span className="text-lg font-bold">
                          {metrics.performance_trends[metrics.performance_trends.length - 1]?.deployments || 0}
                        </span>
                        {getTrendIndicator(
                          metrics.performance_trends[metrics.performance_trends.length - 1]?.deployments || 0,
                          metrics.performance_trends[metrics.performance_trends.length - 2]?.deployments || 0
                        )}
                      </div>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-500">Success Rate Trend</p>
                      <div className="flex items-center justify-center space-x-2">
                        <span className="text-lg font-bold">
                          {(metrics.performance_trends[metrics.performance_trends.length - 1]?.success_rate || 0).toFixed(1)}%
                        </span>
                        {getTrendIndicator(
                          metrics.performance_trends[metrics.performance_trends.length - 1]?.success_rate || 0,
                          metrics.performance_trends[metrics.performance_trends.length - 2]?.success_rate || 0
                        )}
                      </div>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-500">Duration Trend</p>
                      <div className="flex items-center justify-center space-x-2">
                        <span className="text-lg font-bold">
                          {formatDuration(metrics.performance_trends[metrics.performance_trends.length - 1]?.average_duration || 0)}
                        </span>
                        {getTrendIndicator(
                          metrics.performance_trends[metrics.performance_trends.length - 2]?.average_duration || 0,
                          metrics.performance_trends[metrics.performance_trends.length - 1]?.average_duration || 0
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Trend data table */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">Date</th>
                          <th className="text-left p-2">Deployments</th>
                          <th className="text-left p-2">Success Rate</th>
                          <th className="text-left p-2">Avg Duration</th>
                        </tr>
                      </thead>
                      <tbody>
                        {metrics.performance_trends.slice(-7).map((trend, index) => (
                          <tr key={index} className="border-b">
                            <td className="p-2">{new Date(trend.date).toLocaleDateString()}</td>
                            <td className="p-2">{trend.deployments}</td>
                            <td className="p-2">{trend.success_rate.toFixed(1)}%</td>
                            <td className="p-2">{formatDuration(trend.average_duration)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  No trend data available for the selected time range
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="environments" className="space-y-6">
          <div className="grid grid-cols-1 gap-6">
            {environmentAnalytics.map((env) => (
              <Card key={env.environment_id}>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    {getEnvironmentTypeIcon(env.environment_type)}
                    <span className="ml-2">{env.environment_id}</span>
                    <Badge variant="outline" className="ml-2">
                      {env.environment_type}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-500">Total Deployments</p>
                      <p className="text-lg font-bold">{env.total_deployments}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Success Rate</p>
                      <p className="text-lg font-bold">
                        {env.total_deployments > 0 
                          ? ((env.successful_deployments / env.total_deployments) * 100).toFixed(1)
                          : 0}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Avg Duration</p>
                      <p className="text-lg font-bold">{formatDuration(env.average_duration_seconds)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Failed</p>
                      <p className="text-lg font-bold text-red-600">{env.failed_deployments}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-medium mb-2">Resource Efficiency</h4>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span>CPU Utilization</span>
                          <span>{env.resource_efficiency.cpu_utilization.toFixed(1)}%</span>
                        </div>
                        <Progress value={env.resource_efficiency.cpu_utilization} className="h-1" />
                        
                        <div className="flex items-center justify-between text-sm">
                          <span>Memory Utilization</span>
                          <span>{env.resource_efficiency.memory_utilization.toFixed(1)}%</span>
                        </div>
                        <Progress value={env.resource_efficiency.memory_utilization} className="h-1" />
                        
                        <div className="flex items-center justify-between text-sm">
                          <span>Disk Utilization</span>
                          <span>{env.resource_efficiency.disk_utilization.toFixed(1)}%</span>
                        </div>
                        <Progress value={env.resource_efficiency.disk_utilization} className="h-1" />
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Top Failure Reasons</h4>
                      <div className="space-y-2">
                        {Object.entries(env.failure_reasons)
                          .sort(([,a], [,b]) => b - a)
                          .slice(0, 3)
                          .map(([reason, count]) => (
                            <div key={reason} className="flex items-center justify-between text-sm">
                              <span className="truncate">{reason}</span>
                              <Badge variant="outline">{count}</Badge>
                            </div>
                          ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="failures" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <XCircle className="h-5 w-5 mr-2" />
                Failure Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <h4 className="font-medium">Failure Categories</h4>
                {Object.entries(metrics.failure_categories)
                  .sort(([,a], [,b]) => b - a)
                  .map(([category, count]) => (
                    <div key={category}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium capitalize">
                          {category.replace(/_/g, ' ')}
                        </span>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-500">{count} failures</span>
                          <Badge variant="outline">
                            {((count / metrics.failed_deployments) * 100).toFixed(1)}%
                          </Badge>
                        </div>
                      </div>
                      <Progress 
                        value={(count / Math.max(...Object.values(metrics.failure_categories))) * 100} 
                        className="h-2"
                      />
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DeploymentAnalytics;