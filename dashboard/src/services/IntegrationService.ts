import {
  Integration,
  IntegrationConfig,
  WebhookConfig,
  IntegrationHealth,
  IntegrationType,
  IntegrationStatus,
  IntegrationProvider
} from '../types/integrations';

class IntegrationService {
  private baseUrl = '/api/integrations';

  async getIntegrations(filters?: {
    type?: IntegrationType[];
    provider?: IntegrationProvider[];
    status?: IntegrationStatus[];
  }): Promise<Integration[]> {
    try {
      const queryParams = new URLSearchParams();
      if (filters) {
        if (filters.type) filters.type.forEach(t => queryParams.append('type', t));
        if (filters.provider) filters.provider.forEach(p => queryParams.append('provider', p));
        if (filters.status) filters.status.forEach(s => queryParams.append('status', s));
      }

      const response = await fetch(`${this.baseUrl}?${queryParams}`);
      if (!response.ok) throw new Error(`Failed to fetch integrations: ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching integrations:', error);
      throw error;
    }
  }

  async createIntegration(integration: Omit<Integration, 'id' | 'createdAt' | 'updatedAt'>): Promise<Integration> {
    try {
      const response = await fetch(`${this.baseUrl}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(integration),
      });
      if (!response.ok) throw new Error(`Failed to create integration: ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error('Error creating integration:', error);
      throw error;
    }
  }

  async updateIntegration(id: string, updates: Partial<Integration>): Promise<Integration> {
    try {
      const response = await fetch(`${this.baseUrl}/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (!response.ok) throw new Error(`Failed to update integration: ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error('Error updating integration:', error);
      throw error;
    }
  }

  async deleteIntegration(id: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/${id}`, { method: 'DELETE' });
      if (!response.ok) throw new Error(`Failed to delete integration: ${response.statusText}`);
    } catch (error) {
      console.error('Error deleting integration:', error);
      throw error;
    }
  }
}

export const integrationService = new IntegrationService();
export default integrationService;