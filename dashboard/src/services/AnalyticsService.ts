class AnalyticsService {
  private baseUrl = '/api/analytics';

  async getMetrics(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/metrics`);
    if (!response.ok) throw new Error('Failed to fetch metrics');
    return await response.json();
  }

  async getTrendData(metric: string, timeRange: string): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/trends?metric=${metric}&range=${timeRange}`);
    if (!response.ok) throw new Error('Failed to fetch trend data');
    return await response.json();
  }

  async generateReport(config: any): Promise<any> {
    const response = await fetch(`${this.baseUrl}/reports`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!response.ok) throw new Error('Failed to generate report');
    return await response.json();
  }
}

export const analyticsService = new AnalyticsService();
export default analyticsService;