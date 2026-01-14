import {
  ResourceMetrics,
  InfrastructureMetrics,
  CapacityMetrics,
  ResourceAlert,
  ResourceThreshold,
  ResourceFilters,
  AlertPolicy,
  CapacityRecommendation,
  ResourceType,
  AlertSeverity,
  ResourceStatus,
  MetricType
} from '../types/resources';

class ResourceMonitoringService {
  private baseUrl = '/api/resources';
  private wsConnection: WebSocket | null = null;
  private metricsCache = new Map<string, { data: any; timestamp: number }>();
  private cacheTimeout = 30000; // 30 seconds

  // Resource Management
  async getResources(filters?: ResourceFilters): Promise<ResourceMetrics[]> {
    try {
      const queryParams = new URLSearchParams();
      
      if (filters) {
        if (filters.type) filters.type.forEach(t => queryParams.append('type', t));
        if (filters.status) filters.status.forEach(s => queryParams.append('status', s));
        if (filters.location) queryParams.append('location', filters.location);
        if (filters.provider) queryParams.append('provider', filters.provider);
        if (filters.tags) filters.tags.forEach(t => queryParams.append('tags', t));
        if (filters.search) queryParams.append('search', filters.search);
      }

      const cacheKey = `resources-${queryParams.toString()}`;
      const cached = this.getCachedData(cacheKey);
      if (cached) return cached;

      const response = await fetch(`${this.baseUrl}?${queryParams}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch resources: ${response.statusText}`);
      }
      
      const data = await response.json();
      this.setCachedData(cacheKey, data);
      return data;
    } catch (error) {
      console.error('Error fetching resources:', error);
      throw error;
    }
  }

  async getResource(resourceId: string): Promise<ResourceMetrics> {
    try {
      const cacheKey = `resource-${resourceId}`;
      const cached = this.getCachedData(cacheKey);
      if (cached) return cached;

      const response = await fetch(`${this.baseUrl}/${resourceId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch resource: ${response.statusText}`);
      }
      
      const data = await response.json();
      this.setCachedData(cacheKey, data);
      return data;
    } catch (error) {
      console.error('Error fetching resource:', error);
      throw error;
    }
  }

  async updateResourceThresholds(resourceId: string, thresholds: ResourceThreshold): Promise<ResourceMetrics> {
    try {
      const response = await fetch(`${this.baseUrl}/${resourceId}/thresholds`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(thresholds),
      });

      if (!response.ok) {
        throw new Error(`Failed to update resource thresholds: ${response.statusText}`);
      }

      // Invalidate cache for this resource
      this.invalidateCache(`resource-${resourceId}`);
      
      return await response.json();
    } catch (error) {
      console.error('Error updating resource thresholds:', error);
      throw error;
    }
  }

  // Real-time Metrics
  async getResourceMetrics(resourceId: string, timeRange?: { start: string; end: string }): Promise<{
    cpu: Array<{ timestamp: string; value: number }>;
    memory: Array<{ timestamp: string; value: number }>;
    disk: Array<{ timestamp: string; value: number }>;
    network: Array<{ timestamp: string; value: number }>;
  }> {
    try {
      const queryParams = new URLSearchParams();
      if (timeRange) {
        queryParams.append('start', timeRange.start);
        queryParams.append('end', timeRange.end);
      }

      const response = await fetch(`${this.baseUrl}/${resourceId}/metrics?${queryParams}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch resource metrics: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching resource metrics:', error);
      throw error;
    }
  }

  async getInfrastructureMetrics(): Promise<InfrastructureMetrics> {
    try {
      const cacheKey = 'infrastructure-metrics';
      const cached = this.getCachedData(cacheKey);
      if (cached) return cached;

      const response = await fetch(`${this.baseUrl}/infrastructure/metrics`);
      if (!response.ok) {
        throw new Error(`Failed to fetch infrastructure metrics: ${response.statusText}`);
      }
      
      const data = await response.json();
      this.setCachedData(cacheKey, data);
      return data;
    } catch (error) {
      console.error('Error fetching infrastructure metrics:', error);
      throw error;
    }
  }

  // Capacity Planning
  async getCapacityMetrics(): Promise<CapacityMetrics> {
    try {
      const cacheKey = 'capacity-metrics';
      const cached = this.getCachedData(cacheKey);
      if (cached) return cached;

      const response = await fetch(`${this.baseUrl}/capacity/metrics`);
      if (!response.ok) {
        throw new Error(`Failed to fetch capacity metrics: ${response.statusText}`);
      }
      
      const data = await response.json();
      this.setCachedData(cacheKey, data);
      return data;
    } catch (error) {
      console.error('Error fetching capacity metrics:', error);
      throw error;
    }
  }

  async getCapacityForecast(
    resourceType: MetricType,
    timeHorizon: '30d' | '60d' | '90d' | '180d' | '365d'
  ): Promise<{
    projectedUtilization: number;
    confidenceInterval: { lower: number; upper: number };
    recommendedAction: 'none' | 'monitor' | 'scale_up' | 'scale_out';
    timeline: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/capacity/forecast?type=${resourceType}&horizon=${timeHorizon}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch capacity forecast: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching capacity forecast:', error);
      throw error;
    }
  }

  async getCapacityRecommendations(): Promise<CapacityRecommendation[]> {
    try {
      const response = await fetch(`${this.baseUrl}/capacity/recommendations`);
      if (!response.ok) {
        throw new Error(`Failed to fetch capacity recommendations: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching capacity recommendations:', error);
      throw error;
    }
  }

  async implementCapacityRecommendation(recommendationId: string): Promise<{
    success: boolean;
    taskId: string;
    estimatedCompletion: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/capacity/recommendations/${recommendationId}/implement`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to implement capacity recommendation: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error implementing capacity recommendation:', error);
      throw error;
    }
  }

  // Alert Management
  async getAlerts(filters?: {
    resourceId?: string;
    severity?: AlertSeverity[];
    status?: 'active' | 'acknowledged' | 'resolved'[];
    dateRange?: { start: string; end: string };
  }): Promise<ResourceAlert[]> {
    try {
      const queryParams = new URLSearchParams();
      
      if (filters) {
        if (filters.resourceId) queryParams.append('resourceId', filters.resourceId);
        if (filters.severity) filters.severity.forEach(s => queryParams.append('severity', s));
        if (filters.status) filters.status.forEach(s => queryParams.append('status', s));
        if (filters.dateRange) {
          queryParams.append('start', filters.dateRange.start);
          queryParams.append('end', filters.dateRange.end);
        }
      }

      const response = await fetch(`${this.baseUrl}/alerts?${queryParams}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch alerts: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching alerts:', error);
      throw error;
    }
  }

  async acknowledgeAlert(alertId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/alerts/${alertId}/acknowledge`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to acknowledge alert: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error acknowledging alert:', error);
      throw error;
    }
  }

  async resolveAlert(alertId: string, resolution: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/alerts/${alertId}/resolve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ resolution }),
      });

      if (!response.ok) {
        throw new Error(`Failed to resolve alert: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error resolving alert:', error);
      throw error;
    }
  }

  // Alert Policy Management
  async getAlertPolicies(): Promise<AlertPolicy[]> {
    try {
      const response = await fetch(`${this.baseUrl}/alert-policies`);
      if (!response.ok) {
        throw new Error(`Failed to fetch alert policies: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching alert policies:', error);
      throw error;
    }
  }

  async createAlertPolicy(policy: Omit<AlertPolicy, 'id' | 'createdAt' | 'updatedAt'>): Promise<AlertPolicy> {
    try {
      const response = await fetch(`${this.baseUrl}/alert-policies`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(policy),
      });

      if (!response.ok) {
        throw new Error(`Failed to create alert policy: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating alert policy:', error);
      throw error;
    }
  }

  async updateAlertPolicy(policyId: string, updates: Partial<AlertPolicy>): Promise<AlertPolicy> {
    try {
      const response = await fetch(`${this.baseUrl}/alert-policies/${policyId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error(`Failed to update alert policy: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating alert policy:', error);
      throw error;
    }
  }

  async deleteAlertPolicy(policyId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/alert-policies/${policyId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete alert policy: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error deleting alert policy:', error);
      throw error;
    }
  }

  // Performance Baseline Management
  async getPerformanceBaselines(): Promise<{
    [resourceId: string]: {
      cpu: { baseline: number; current: number; variance: number };
      memory: { baseline: number; current: number; variance: number };
      disk: { baseline: number; current: number; variance: number };
      network: { baseline: number; current: number; variance: number };
    };
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/baselines`);
      if (!response.ok) {
        throw new Error(`Failed to fetch performance baselines: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching performance baselines:', error);
      throw error;
    }
  }

  async updatePerformanceBaseline(
    resourceId: string,
    metric: MetricType,
    baseline: number
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/${resourceId}/baselines/${metric}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ baseline }),
      });

      if (!response.ok) {
        throw new Error(`Failed to update performance baseline: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error updating performance baseline:', error);
      throw error;
    }
  }

  async recalculateBaselines(resourceId?: string): Promise<void> {
    try {
      const url = resourceId 
        ? `${this.baseUrl}/${resourceId}/baselines/recalculate`
        : `${this.baseUrl}/baselines/recalculate`;
        
      const response = await fetch(url, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to recalculate baselines: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error recalculating baselines:', error);
      throw error;
    }
  }

  // Cost Analysis
  async getCostAnalysis(timeRange?: { start: string; end: string }): Promise<{
    totalCost: number;
    costByProvider: Record<string, number>;
    costByResourceType: Record<string, number>;
    costTrend: Array<{ date: string; cost: number }>;
    optimizationOpportunities: Array<{
      type: string;
      description: string;
      potentialSavings: number;
      effort: 'low' | 'medium' | 'high';
    }>;
  }> {
    try {
      const queryParams = new URLSearchParams();
      if (timeRange) {
        queryParams.append('start', timeRange.start);
        queryParams.append('end', timeRange.end);
      }

      const response = await fetch(`${this.baseUrl}/cost-analysis?${queryParams}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch cost analysis: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching cost analysis:', error);
      throw error;
    }
  }

  async getCostOptimizationRecommendations(): Promise<Array<{
    id: string;
    type: 'rightsizing' | 'reserved_instances' | 'auto_scaling' | 'storage_optimization';
    title: string;
    description: string;
    potentialSavings: number;
    effort: 'low' | 'medium' | 'high';
    timeline: string;
    resources: string[];
    implementation: {
      steps: string[];
      risks: string[];
      prerequisites: string[];
    };
  }>> {
    try {
      const response = await fetch(`${this.baseUrl}/cost-optimization`);
      if (!response.ok) {
        throw new Error(`Failed to fetch cost optimization recommendations: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching cost optimization recommendations:', error);
      throw error;
    }
  }

  // Real-time Data Streaming
  connectToRealTimeMetrics(
    resourceIds: string[],
    onMetricsUpdate: (resourceId: string, metrics: any) => void,
    onError?: (error: Error) => void
  ): void {
    try {
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/resources/ws`;
      this.wsConnection = new WebSocket(wsUrl);

      this.wsConnection.onopen = () => {
        console.log('Connected to real-time metrics stream');
        // Subscribe to specific resources
        this.wsConnection?.send(JSON.stringify({
          type: 'subscribe',
          resourceIds
        }));
      };

      this.wsConnection.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'metrics_update') {
            onMetricsUpdate(data.resourceId, data.metrics);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.wsConnection.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(new Error('WebSocket connection error'));
      };

      this.wsConnection.onclose = () => {
        console.log('Disconnected from real-time metrics stream');
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          if (this.wsConnection?.readyState === WebSocket.CLOSED) {
            this.connectToRealTimeMetrics(resourceIds, onMetricsUpdate, onError);
          }
        }, 5000);
      };
    } catch (error) {
      console.error('Error connecting to real-time metrics:', error);
      onError?.(error as Error);
    }
  }

  disconnectFromRealTimeMetrics(): void {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
  }

  // Trend Analysis
  async getTrendAnalysis(
    metric: MetricType,
    timeRange: { start: string; end: string },
    aggregation: 'hourly' | 'daily' | 'weekly' = 'daily'
  ): Promise<{
    trend: 'increasing' | 'decreasing' | 'stable';
    slope: number;
    correlation: number;
    seasonality: {
      detected: boolean;
      period?: string;
      strength?: number;
    };
    anomalies: Array<{
      timestamp: string;
      value: number;
      severity: 'low' | 'medium' | 'high';
      description: string;
    }>;
    forecast: Array<{
      timestamp: string;
      predicted: number;
      confidence: { lower: number; upper: number };
    }>;
  }> {
    try {
      const queryParams = new URLSearchParams({
        metric,
        start: timeRange.start,
        end: timeRange.end,
        aggregation
      });

      const response = await fetch(`${this.baseUrl}/trend-analysis?${queryParams}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch trend analysis: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching trend analysis:', error);
      throw error;
    }
  }

  // Resource Provisioning
  async provisionResource(config: {
    type: ResourceType;
    name: string;
    specifications: {
      cpu: number;
      memory: number;
      disk: number;
      network?: number;
    };
    location: string;
    provider: string;
    tags?: string[];
  }): Promise<{
    resourceId: string;
    status: 'provisioning' | 'ready' | 'failed';
    estimatedCompletion?: string;
    taskId: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/provision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`Failed to provision resource: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error provisioning resource:', error);
      throw error;
    }
  }

  async scaleResource(
    resourceId: string,
    action: 'scale_up' | 'scale_down' | 'scale_out' | 'scale_in',
    parameters: {
      cpu?: number;
      memory?: number;
      instances?: number;
    }
  ): Promise<{
    success: boolean;
    taskId: string;
    estimatedCompletion: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/${resourceId}/scale`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action, parameters }),
      });

      if (!response.ok) {
        throw new Error(`Failed to scale resource: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error scaling resource:', error);
      throw error;
    }
  }

  // Cache Management
  private getCachedData(key: string): any | null {
    const cached = this.metricsCache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    return null;
  }

  private setCachedData(key: string, data: any): void {
    this.metricsCache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  private invalidateCache(key?: string): void {
    if (key) {
      this.metricsCache.delete(key);
    } else {
      this.metricsCache.clear();
    }
  }

  // Utility Methods
  calculateResourceUtilization(metrics: ResourceMetrics): number {
    const weights = { cpu: 0.3, memory: 0.3, disk: 0.2, network: 0.2 };
    return (
      metrics.metrics.cpu.usage * weights.cpu +
      metrics.metrics.memory.usage * weights.memory +
      metrics.metrics.disk.usage * weights.disk +
      metrics.metrics.network.usage * weights.network
    );
  }

  determineResourceHealth(metrics: ResourceMetrics): ResourceStatus {
    const utilization = this.calculateResourceUtilization(metrics);
    const hasActiveAlerts = metrics.alerts.some(alert => 
      alert.status === 'active' && !alert.acknowledged
    );

    if (hasActiveAlerts) {
      const hasCriticalAlerts = metrics.alerts.some(alert => 
        alert.severity === 'critical' && alert.status === 'active'
      );
      return hasCriticalAlerts ? 'critical' : 'warning';
    }

    if (utilization > 85) return 'critical';
    if (utilization > 70) return 'warning';
    return 'healthy';
  }

  formatBytes(bytes: number): string {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  }

  formatBandwidth(mbps: number): string {
    if (mbps < 1000) return `${mbps.toFixed(2)} Mbps`;
    return `${(mbps / 1000).toFixed(2)} Gbps`;
  }
}

export const resourceMonitoringService = new ResourceMonitoringService();
export default resourceMonitoringService;