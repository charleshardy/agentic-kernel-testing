class BackupService {
  private baseUrl = '/api/backups';

  async getBackups(): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}`);
    if (!response.ok) throw new Error('Failed to fetch backups');
    return await response.json();
  }

  async createBackup(config: any): Promise<any> {
    const response = await fetch(`${this.baseUrl}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!response.ok) throw new Error('Failed to create backup');
    return await response.json();
  }

  async restoreBackup(id: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/${id}/restore`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to restore backup');
    return await response.json();
  }

  async deleteBackup(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${id}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Failed to delete backup');
  }
}

export const backupService = new BackupService();
export default backupService;