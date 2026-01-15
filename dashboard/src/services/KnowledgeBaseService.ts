class KnowledgeBaseService {
  private baseUrl = '/api/knowledge-base';

  async getArticles(): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/articles`);
    if (!response.ok) throw new Error('Failed to fetch articles');
    return await response.json();
  }

  async searchArticles(query: string): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error('Failed to search articles');
    return await response.json();
  }

  async createArticle(article: any): Promise<any> {
    const response = await fetch(`${this.baseUrl}/articles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(article),
    });
    if (!response.ok) throw new Error('Failed to create article');
    return await response.json();
  }
}

export const knowledgeBaseService = new KnowledgeBaseService();
export default knowledgeBaseService;