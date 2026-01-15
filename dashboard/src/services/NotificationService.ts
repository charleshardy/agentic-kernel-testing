class NotificationService {
  private baseUrl = '/api/notifications';

  async getNotifications(): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}`);
    if (!response.ok) throw new Error('Failed to fetch notifications');
    return await response.json();
  }

  async markAsRead(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${id}/read`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to mark notification as read');
  }

  async deleteNotification(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${id}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Failed to delete notification');
  }
}

export const notificationService = new NotificationService();
export default notificationService;