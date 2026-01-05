import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  TrendingUp, 
  TrendingDown,
  Activity, 
  Clock,
  CheckCircle,
  XCircle,
  BarChart3,
  PieChart,
  Calendar,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';

interface DeploymentAnalyticsProps {
  timeRange?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface AnalyticsData {
  successRate: number;
  averageDuration: number;
  totalDeployments: number;
  failureRate: number;
  retryRate: number;
  environmentBreakdown: Record<string, number>;
  timeSeriesData: Array<{
    timestamp: string;
    successful: number;
    failed: number;
    duration: number;
  }>;
}

const DeploymentAnalytics: React.FC<DeploymentAnalyticsProps> = ({
  timeRange = '24h',
  autoRefresh = true,
  refreshInterval = 30000
}) => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
  const [activeTab, setActiveTab] = useState('overview');

  // Mock analytics data
  const mockAnalytics: AnalyticsData = {
    successRate: 87.5,
    averageDuration: 145.2,
    totalDeployments: 156,
    failureRate: 8.3,
    retryRate: 4.2,
    environmentBreakdown: {
      'qemu-x86-64': 45,
      'physical-arm64': 32,
      'qemu-arm64': 28,
      'container-x86': 21,
      'physical-x86': 18,
      'qemu-riscv': 12
    },
    timeSeriesData: [
      { timestamp: '00:00', successful: 12, failed: 2, duration: 142 },
      { timestamp: '04:00', successful: 8, failed: 1, duration: 138 },
      { timestamp: '08:00', successful: 15, failed: 3, duration: 156 },
      { timestamp: '12:00', successful: 18, failed: 2, duration: 149 },
      { timestamp: '16:00', successful: 22, failed: 1, duration: 134 },
      { timestamp: '20:00', successful: 16, failed: 3, duration: 152 }
    ]
  };

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      try {
        // In real implementation, fetch from API
        // const response = await fetch(`/api/v1/deployments/analytics/performance?time_range=${selectedTimeRange}`);
        // const data = await response.json();
        
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        setAnalytics(mockAnalytics);
      } catch (error) {
        console.error('Failed to fetch analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();

    if (autoRefresh) {
      const interval = setInterval(fetchAnalytics, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [selectedTimeRange, autoRefresh, refreshInterval]);

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 90) return 'text-green-600';
    if (rate >= 75) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getSuccessRateIcon = (rate: number) => {
    if (rate >= 90) return <TrendingUp className="h-4 w-4 text-green-600" />;
    if (rate >= 75) return <Activity className="h-4 w-4 text-yellow-600" />;
    return <TrendingDown className="h-4 w-4 text-red-600" />;
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <RefreshCw className="h-6 w-6 animate-spin mr-2" />
            Loading analytics...
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!analytics) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-gray-500">
            Failed to load analytics data
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Deployment Analytics</h2>
          <p className="text-gray-600">Performance insights and trends</p>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value)}
            className="border rounded px-3 py-1 text-sm"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Success Rate</p>
                <p className={`text-2xl font-bold ${getSuccessRateColor(analytics.successRate)}`}>
                  {analytics.successRate}%
                </p>
              </div>
              {getSuccessRateIcon(analytics.successRate)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Avg Duration</p>
                <p className="text-2xl font-bold">{formatDuration(analytics.averageDuration)}</p>
              </div>
              <Clock className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Total Deployments</p>
                <p className="text-2xl font-bold">{analytics.totalDeployments}</p>
              </div>
              <Activity className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Failure Rate</p>
                <p className="text-2xl font-bold text-red-600">{analytics.failureRate}%</p>
              </div>
              <XCircle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Retry Rate</p>
                <p className="text-2xl font-bold text-orange-600">{analytics.retryRate}%</p>
              </div>
              <RefreshCw className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Analytics Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="environments">Environments</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Success Rate Trend */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <TrendingUp className="h-5 w-5 mr-2" />
                  Success Rate Trend
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center">
                  <div className="w-full space-y-3">
                    {analytics.timeSeriesData.map((point, index) => {
                      const total = point.successful + point.failed;
                      const successRate = total > 0 ? (point.successful / total) * 100 : 0;
                      return (
                        <div key={index} className="flex items-center justify-between">
                          <span className="text-sm font-medium w-12">{point.timestamp}</span>
                          <div className="flex-1 mx-4">
                            <Progress value={successRate} className="h-2" />
                          </div>
                          <span className="text-sm text-gray-500 w-12 text-right">
                            {Math.round(successRate)}%
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Deployment Volume */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2" />
                  Deployment Volume
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-end justify-between space-x-2">
                  {analytics.timeSeriesData.map((point, index) => {
                    const total = point.successful + point.failed;
                    const maxTotal = Math.max(...analytics.timeSeriesData.map(p => p.successful + p.failed));
                    const height = (total / maxTotal) * 200;
                    
                    return (
                      <div key={index} className="flex flex-col items-center space-y-2">
                        <div className="flex flex-col items-center">
                          <div 
                            className="bg-green-500 rounded-t"
                            style={{ 
                              width: '20px', 
                              height: `${(point.successful / maxTotal) * 200}px`,
                              minHeight: '2px'
                            }}
                          />
                          <div 
                            className="bg-red-500 rounded-b"
                            style={{ 
                              width: '20px', 
                              height: `${(point.failed / maxTotal) * 200}px`,
                              minHeight: point.failed > 0 ? '2px' : '0px'
                            }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">{point.timestamp}</span>
                      </div>
                    );
                  })}
                </div>
                <div className="flex items-center justify-center space-x-4 mt-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-green-500 rounded" />
                    <span className="text-sm">Successful</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-red-500 rounded" />
                    <span className="text-sm">Failed</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="trends" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Performance Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <TrendingUp className="h-12 w-12 mx-auto mb-2" />
                  <p>Detailed trend analysis would be displayed here</p>
                  <p className="text-sm">Integration with time-series data pending</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="environments" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <PieChart className="h-5 w-5 mr-2" />
                Environment Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(analytics.environmentBreakdown)
                  .sort(([,a], [,b]) => b - a)
                  .map(([env, count]) => {
                    const percentage = (count / analytics.totalDeployments) * 100;
                    return (
                      <div key={env} className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="w-4 h-4 bg-blue-500 rounded" />
                          <span className="font-medium">{env}</span>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="w-32">
                            <Progress value={percentage} className="h-2" />
                          </div>
                          <span className="text-sm text-gray-500 w-12 text-right">
                            {count}
                          </span>
                          <span className="text-sm text-gray-500 w-12 text-right">
                            {Math.round(percentage)}%
                          </span>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Duration Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <Clock className="h-12 w-12 mx-auto mb-2" />
                    <p>Duration distribution chart would be displayed here</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Fastest Deployment</span>
                    <span className="text-sm">45s</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Slowest Deployment</span>
                    <span className="text-sm">8m 23s</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Median Duration</span>
                    <span className="text-sm">2m 18s</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">95th Percentile</span>
                    <span className="text-sm">4m 45s</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DeploymentAnalytics;