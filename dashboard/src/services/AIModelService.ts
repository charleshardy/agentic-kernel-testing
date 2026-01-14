import {
  AIModel,
  ModelMetrics,
  ModelConfiguration,
  PromptTemplate,
  ModelRegistry,
  TemplateVariable,
  AIModelFilter,
  PromptTemplateFilter,
  ModelPerformanceReport,
  AIModelError
} from '../types/ai-models';

class AIModelService {
  private baseUrl: string;
  private apiKey?: string;

  constructor(baseUrl: string = '/api/ai-models', apiKey?: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new AIModelError(
          errorData.code || 'UNKNOWN_ERROR',
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          errorData.details,
          new Date()
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof AIModelError) {
        throw error;
      }
      
      throw new AIModelError(
        'NETWORK_ERROR',
        `Failed to communicate with AI model service: ${error instanceof Error ? error.message : 'Unknown error'}`,
        { originalError: error },
        new Date()
      );
    }
  }

  // AI Model Management
  async getAIModels(filters?: AIModelFilter): Promise<AIModel[]> {
    const queryParams = new URLSearchParams();
    
    if (filters) {
      if (filters.provider?.length) {
        queryParams.append('provider', filters.provider.join(','));
      }
      if (filters.status?.length) {
        queryParams.append('status', filters.status.join(','));
      }
      if (filters.name) {
        queryParams.append('name', filters.name);
      }
      if (filters.version) {
        queryParams.append('version', filters.version);
      }
    }

    const endpoint = `/models${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await this.request<AIModel[]>(endpoint);
  }

  async getAIModel(id: string): Promise<AIModel> {
    return await this.request<AIModel>(`/models/${id}`);
  }

  async createAIModel(model: Omit<AIModel, 'id' | 'metrics'>): Promise<AIModel> {
    return await this.request<AIModel>('/models', {
      method: 'POST',
      body: JSON.stringify(model),
    });
  }

  async updateAIModel(id: string, updates: Partial<AIModel>): Promise<AIModel> {
    return await this.request<AIModel>(`/models/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async deleteAIModel(id: string): Promise<void> {
    await this.request<void>(`/models/${id}`, {
      method: 'DELETE',
    });
  }

  async activateModel(id: string): Promise<AIModel> {
    return await this.updateAIModel(id, { status: 'active' });
  }

  async deactivateModel(id: string): Promise<AIModel> {
    return await this.updateAIModel(id, { status: 'inactive' });
  }

  async testModelConnection(id: string): Promise<{ success: boolean; responseTime: number; error?: string }> {
    return await this.request<{ success: boolean; responseTime: number; error?: string }>(`/models/${id}/test`, {
      method: 'POST',
    });
  }

  // Model Configuration Management
  async updateModelConfiguration(id: string, config: Partial<ModelConfiguration>): Promise<AIModel> {
    return await this.request<AIModel>(`/models/${id}/configuration`, {
      method: 'PATCH',
      body: JSON.stringify(config),
    });
  }

  async getModelConfiguration(id: string): Promise<ModelConfiguration> {
    return await this.request<ModelConfiguration>(`/models/${id}/configuration`);
  }

  async validateModelConfiguration(config: ModelConfiguration): Promise<{ valid: boolean; errors?: string[] }> {
    return await this.request<{ valid: boolean; errors?: string[] }>('/models/validate-config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // Model Metrics and Performance
  async getModelMetrics(id: string, timeRange?: { start: Date; end: Date }): Promise<ModelMetrics> {
    const queryParams = new URLSearchParams();
    
    if (timeRange) {
      queryParams.append('startDate', timeRange.start.toISOString());
      queryParams.append('endDate', timeRange.end.toISOString());
    }

    const endpoint = `/models/${id}/metrics${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await this.request<ModelMetrics>(endpoint);
  }

  async getModelPerformanceReport(id: string, timeRange: { start: Date; end: Date }): Promise<ModelPerformanceReport> {
    const queryParams = new URLSearchParams({
      startDate: timeRange.start.toISOString(),
      endDate: timeRange.end.toISOString(),
    });

    return await this.request<ModelPerformanceReport>(`/models/${id}/performance-report?${queryParams.toString()}`);
  }

  async getModelUsageStatistics(): Promise<{
    totalRequests: number;
    totalCost: number;
    averageResponseTime: number;
    errorRate: number;
    topModels: Array<{ id: string; name: string; requestCount: number }>;
  }> {
    return await this.request<{
      totalRequests: number;
      totalCost: number;
      averageResponseTime: number;
      errorRate: number;
      topModels: Array<{ id: string; name: string; requestCount: number }>;
    }>('/models/usage-statistics');
  }

  // Prompt Template Management
  async getPromptTemplates(filters?: PromptTemplateFilter): Promise<PromptTemplate[]> {
    const queryParams = new URLSearchParams();
    
    if (filters) {
      if (filters.category?.length) {
        queryParams.append('category', filters.category.join(','));
      }
      if (filters.name) {
        queryParams.append('name', filters.name);
      }
      if (filters.createdBy) {
        queryParams.append('createdBy', filters.createdBy);
      }
      if (filters.version) {
        queryParams.append('version', filters.version);
      }
    }

    const endpoint = `/templates${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await this.request<PromptTemplate[]>(endpoint);
  }

  async getPromptTemplate(id: string): Promise<PromptTemplate> {
    return await this.request<PromptTemplate>(`/templates/${id}`);
  }

  async createPromptTemplate(template: Omit<PromptTemplate, 'id' | 'createdAt'>): Promise<PromptTemplate> {
    return await this.request<PromptTemplate>('/templates', {
      method: 'POST',
      body: JSON.stringify(template),
    });
  }

  async updatePromptTemplate(id: string, updates: Partial<PromptTemplate>): Promise<PromptTemplate> {
    return await this.request<PromptTemplate>(`/templates/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async deletePromptTemplate(id: string): Promise<void> {
    await this.request<void>(`/templates/${id}`, {
      method: 'DELETE',
    });
  }

  async testPromptTemplate(id: string, variables: Record<string, any>): Promise<{ 
    renderedPrompt: string; 
    estimatedTokens: number; 
    validationErrors?: string[] 
  }> {
    return await this.request<{ 
      renderedPrompt: string; 
      estimatedTokens: number; 
      validationErrors?: string[] 
    }>(`/templates/${id}/test`, {
      method: 'POST',
      body: JSON.stringify({ variables }),
    });
  }

  async renderPromptTemplate(id: string, variables: Record<string, any>): Promise<string> {
    const response = await this.request<{ renderedPrompt: string }>(`/templates/${id}/render`, {
      method: 'POST',
      body: JSON.stringify({ variables }),
    });
    return response.renderedPrompt;
  }

  // Model Registry Management
  async getModelRegistry(): Promise<ModelRegistry> {
    return await this.request<ModelRegistry>('/registry');
  }

  async syncModelRegistry(): Promise<{ synced: number; errors: string[] }> {
    return await this.request<{ synced: number; errors: string[] }>('/registry/sync', {
      method: 'POST',
    });
  }

  // Fallback Management
  async setModelFallback(modelId: string, fallbackModelId: string): Promise<AIModel> {
    return await this.updateAIModel(modelId, { fallbackModel: fallbackModelId });
  }

  async removeModelFallback(modelId: string): Promise<AIModel> {
    return await this.updateAIModel(modelId, { fallbackModel: undefined });
  }

  async getFallbackChain(modelId: string): Promise<AIModel[]> {
    return await this.request<AIModel[]>(`/models/${modelId}/fallback-chain`);
  }

  async testFallbackChain(modelId: string): Promise<{
    chain: Array<{ modelId: string; name: string; available: boolean; responseTime?: number }>;
    recommendedFallback?: string;
  }> {
    return await this.request<{
      chain: Array<{ modelId: string; name: string; available: boolean; responseTime?: number }>;
      recommendedFallback?: string;
    }>(`/models/${modelId}/test-fallback-chain`, {
      method: 'POST',
    });
  }

  // Model Execution
  async executePrompt(
    modelId: string, 
    prompt: string, 
    options?: {
      temperature?: number;
      maxTokens?: number;
      stopSequences?: string[];
      stream?: boolean;
    }
  ): Promise<{
    response: string;
    usage: {
      promptTokens: number;
      completionTokens: number;
      totalTokens: number;
    };
    model: string;
    responseTime: number;
  }> {
    return await this.request<{
      response: string;
      usage: {
        promptTokens: number;
        completionTokens: number;
        totalTokens: number;
      };
      model: string;
      responseTime: number;
    }>(`/models/${modelId}/execute`, {
      method: 'POST',
      body: JSON.stringify({ prompt, options }),
    });
  }

  async executeTemplate(
    templateId: string,
    variables: Record<string, any>,
    modelId?: string,
    options?: {
      temperature?: number;
      maxTokens?: number;
      stopSequences?: string[];
    }
  ): Promise<{
    response: string;
    renderedPrompt: string;
    usage: {
      promptTokens: number;
      completionTokens: number;
      totalTokens: number;
    };
    model: string;
    responseTime: number;
  }> {
    return await this.request<{
      response: string;
      renderedPrompt: string;
      usage: {
        promptTokens: number;
        completionTokens: number;
        totalTokens: number;
      };
      model: string;
      responseTime: number;
    }>(`/templates/${templateId}/execute`, {
      method: 'POST',
      body: JSON.stringify({ variables, modelId, options }),
    });
  }

  // Model Health and Monitoring
  async getModelHealth(): Promise<Array<{
    modelId: string;
    name: string;
    status: 'healthy' | 'degraded' | 'unhealthy';
    lastCheck: Date;
    issues?: string[];
  }>> {
    return await this.request<Array<{
      modelId: string;
      name: string;
      status: 'healthy' | 'degraded' | 'unhealthy';
      lastCheck: Date;
      issues?: string[];
    }>>('/models/health');
  }

  async refreshModelHealth(modelId?: string): Promise<void> {
    const endpoint = modelId ? `/models/${modelId}/health/refresh` : '/models/health/refresh';
    await this.request<void>(endpoint, {
      method: 'POST',
    });
  }

  // Utility Methods
  async healthCheck(): Promise<{ status: string; timestamp: Date }> {
    return await this.request<{ status: string; timestamp: Date }>('/health');
  }

  async getApiVersion(): Promise<{ version: string; buildDate: Date }> {
    return await this.request<{ version: string; buildDate: Date }>('/version');
  }
}

// Singleton instance
export const aiModelService = new AIModelService();

export default AIModelService;