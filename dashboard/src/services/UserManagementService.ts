class UserManagementService {
  private baseUrl = '/api/users';

  async getUsers(): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}`);
    if (!response.ok) throw new Error('Failed to fetch users');
    return await response.json();
  }

  async createUser(user: any): Promise<any> {
    const response = await fetch(`${this.baseUrl}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(user),
    });
    if (!response.ok) throw new Error('Failed to create user');
    return await response.json();
  }

  async updateUser(id: string, updates: any): Promise<any> {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    if (!response.ok) throw new Error('Failed to update user');
    return await response.json();
  }

  async deleteUser(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${id}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Failed to delete user');
  }
}

export const userManagementService = new UserManagementService();
export default userManagementService;