# API Integration Guide

## Overview

This guide explains how to integrate the new backend API endpoints with the frontend services. The backend API has been implemented with 10 new routers covering all feature areas, and the frontend has API client infrastructure ready for integration.

## Backend API Endpoints

All new API endpoints are available at `/api/v1/` with the following routers:

### 1. Security API (`/api/v1/security`)
- `GET /metrics` - Get security metrics
- `GET /vulnerabilities` - List vulnerabilities with filtering
- `GET /fuzzing-results` - Get fuzzing test results
- `GET /policies` - List security policies
- `POST /scan` - Trigger security scan

### 2. AI Models API (`/api/v1/ai-models`)
- `GET /` - List all AI models
- `GET /{model_id}/metrics` - Get model performance metrics
- `GET /prompts` - List prompt templates
- `GET /fallback-config` - Get fallback configuration
- `POST /` - Register new model
- `PUT /{model_id}` - Update model

### 3. Audit & Compliance API (`/api/v1/audit`)
- `GET /events` - Get audit trail events
- `GET /frameworks` - List compliance frameworks
- `GET /reports` - List compliance reports
- `POST /reports/generate` - Generate compliance report
- `GET /search` - Search audit events

### 4. Resource Monitoring API (`/api/v1/resources`)
- `GET /metrics/current` - Get current resource metrics
- `GET /metrics/history` - Get historical metrics
- `GET /infrastructure` - Get infrastructure overview
- `GET /capacity/forecast` - Get capacity forecasts
- `GET /alerts` - List resource alerts
- `POST /alerts/{alert_id}/acknowledge` - Acknowledge alert

### 5. Integrations API (`/api/v1/integrations`)
- `GET /` - List all integrations
- `GET /{integration_id}` - Get integration details
- `GET /{integration_id}/health` - Get health status
- `GET /{integration_id}/webhooks` - List webhooks
- `POST /` - Create integration
- `PUT /{integration_id}` - Update integration
- `POST /{integration_id}/test` - Test connection
- `POST /{integration_id}/sync` - Trigger sync

### 6. User Management API (`/api/v1/users`)
- `GET /` - List users
- `GET /{user_id}` - Get user details
- `GET /teams/list` - List teams
- `GET /roles/list` - List roles
- `GET /permissions/list` - List permissions
- `POST /` - Create user
- `PUT /{user_id}` - Update user
- `POST /teams` - Create team
- `PUT /teams/{team_id}/members` - Update team members

### 7. Notifications API (`/api/v1/notifications`)
- `GET /` - List notifications
- `GET /unread-count` - Get unread count
- `GET /preferences` - Get notification preferences
- `PUT /preferences` - Update preferences
- `GET /policies` - List alert policies
- `POST /policies` - Create alert policy
- `POST /{notification_id}/read` - Mark as read
- `POST /mark-all-read` - Mark all as read
- `DELETE /{notification_id}` - Delete notification

### 8. Knowledge Base API (`/api/v1/knowledge-base`)
- `GET /articles` - List articles
- `GET /articles/{article_id}` - Get article
- `GET /search` - Search articles
- `GET /contextual-help` - Get contextual help
- `GET /categories` - List categories
- `POST /articles` - Create article
- `PUT /articles/{article_id}` - Update article
- `POST /articles/{article_id}/helpful` - Mark helpful

### 9. Analytics API (`/api/v1/analytics`)
- `GET /metrics` - Get analytics metrics
- `GET /trends` - Get trend analysis
- `GET /insights` - Get AI-powered insights
- `GET /predictions` - Get predictive analytics
- `GET /reports` - List custom reports
- `POST /reports` - Create custom report
- `POST /reports/{report_id}/generate` - Generate report
- `GET /dashboard-data` - Get dashboard widget data

### 10. Backup & Recovery API (`/api/v1/backup`)
- `GET /policies` - List backup policies
- `GET /recovery-points` - List recovery points
- `GET /status` - Get backup status
- `GET /recovery-tests` - List recovery tests
- `POST /policies` - Create backup policy
- `PUT /policies/{policy_id}` - Update policy
- `POST /policies/{policy_id}/execute` - Execute backup
- `POST /recovery-points/{recovery_point_id}/restore` - Restore
- `POST /recovery-tests` - Create recovery test
- `DELETE /recovery-points/{recovery_point_id}` - Delete recovery point

## Frontend API Client

### Base Client (`dashboard/src/api/client.ts`)

The base API client provides:
- Automatic authentication with Bearer tokens
- Error handling with typed APIError
- Request/response type safety
- Token management (localStorage)

```typescript
import { apiClient } from './api/client';

// Set authentication token
apiClient.setToken('your-jwt-token');

// Make requests
const data = await apiClient.get('/security/metrics');
const result = await apiClient.post('/security/scan', { target: 'network-driver' });
```

### API Endpoints (`dashboard/src/api/endpoints.ts`)

Pre-configured endpoint functions for all features:

```typescript
import api from './api/endpoints';

// Security
const metrics = await api.security.getMetrics();
const vulnerabilities = await api.security.getVulnerabilities({ severity: 'critical' });

// AI Models
const models = await api.aiModels.listModels();
const modelMetrics = await api.aiModels.getModelMetrics('model-001');

// Notifications
const notifications = await api.notifications.listNotifications({ read: false });
await api.notifications.markAsRead('notif-001');

// Analytics
const insights = await api.analytics.getInsights({ severity: 'high' });
const predictions = await api.analytics.getPredictions('success_rate', 7);
```

### React Hooks (`dashboard/src/hooks/useAPI.ts`)

Convenient hooks for API calls:

```typescript
import { useAPI, useAPIPolling, useMutation, usePaginatedAPI } from './hooks/useAPI';
import api from './api/endpoints';

// Basic API call
const { data, loading, error, execute } = useAPI(api.security.getMetrics, { immediate: true });

// Polling (auto-refresh every 5 seconds)
const { data: metrics } = useAPIPolling(api.resources.getCurrentMetrics, 5000);

// Mutations
const { mutate, loading } = useMutation(api.notifications.markAsRead, {
  onSuccess: () => console.log('Marked as read'),
  onError: (error) => console.error(error),
});

// Paginated data
const {
  data,
  page,
  totalPages,
  nextPage,
  prevPage,
  hasNextPage,
} = usePaginatedAPI(api.audit.getEvents, 20);
```

### WebSocket Client (`dashboard/src/api/websocket.ts`)

Real-time updates via WebSocket:

```typescript
import { wsClient } from './api/websocket';

// Connect
wsClient.connect(authToken);

// Subscribe to events
const unsubscribe = wsClient.on('test.completed', (data) => {
  console.log('Test completed:', data);
});

// Subscribe to channels
wsClient.subscribe('notifications');
wsClient.subscribe('resource-metrics');

// Send messages
wsClient.send('ping', { timestamp: Date.now() });

// Cleanup
unsubscribe();
wsClient.disconnect();
```

## Integration Steps

### Step 1: Update Service Classes

Replace mock implementations in service classes with actual API calls:

```typescript
// Before (mock)
async getSecurityMetrics(): Promise<SecurityMetrics> {
  return {
    totalScans: 156,
    vulnerabilitiesFound: 23,
    // ... mock data
  };
}

// After (real API)
import { securityAPI } from '../api/endpoints';

async getSecurityMetrics(): Promise<SecurityMetrics> {
  const data = await securityAPI.getMetrics();
  return {
    totalScans: data.total_scans,
    vulnerabilitiesFound: data.vulnerabilities_found,
    // ... map API response to interface
  };
}
```

### Step 2: Update Components

Use the API hooks in React components:

```typescript
import { useAPI } from '../hooks/useAPI';
import api from '../api/endpoints';

function SecurityDashboard() {
  const { data: metrics, loading, error } = useAPI(
    api.security.getMetrics,
    { immediate: true, cache: true }
  );

  if (loading) return <Spin />;
  if (error) return <Alert message={error.message} type="error" />;

  return <MetricsDisplay metrics={metrics} />;
}
```

### Step 3: Add Real-Time Updates

Integrate WebSocket for live data:

```typescript
import { wsClient } from '../api/websocket';
import { useEffect, useState } from 'react';

function NotificationCenter() {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    // Subscribe to notification events
    const unsubscribe = wsClient.on('notification.new', (notification) => {
      setNotifications(prev => [notification, ...prev]);
    });

    wsClient.subscribe('notifications');

    return () => {
      unsubscribe();
      wsClient.unsubscribe('notifications');
    };
  }, []);

  return <NotificationList notifications={notifications} />;
}
```

### Step 4: Error Handling

Implement consistent error handling:

```typescript
import { APIError } from '../api/client';
import { message } from 'antd';

try {
  await api.security.triggerScan('network-driver', 'vulnerability');
  message.success('Scan initiated successfully');
} catch (error) {
  if (error instanceof APIError) {
    if (error.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    } else if (error.status === 403) {
      message.error('You do not have permission to perform this action');
    } else {
      message.error(error.message);
    }
  }
}
```

### Step 5: Configure Environment Variables

Create `.env` file in dashboard directory:

```bash
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

For production:

```bash
VITE_API_URL=https://api.example.com/api/v1
VITE_WS_URL=wss://api.example.com/ws
```

## Testing the Integration

### 1. Start Backend API

```bash
# From project root
python -m api.main
# or
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Frontend

```bash
cd dashboard
npm run dev
```

### 3. Test API Endpoints

```bash
# Test security metrics
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/security/metrics

# Test vulnerabilities
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/security/vulnerabilities

# Test notifications
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/notifications/
```

### 4. Check API Documentation

Visit http://localhost:8000/docs for interactive Swagger UI documentation.

## Authentication Flow

1. User logs in via `/api/v1/auth/login`
2. Backend returns JWT token
3. Frontend stores token: `apiClient.setToken(token)`
4. All subsequent requests include token in Authorization header
5. WebSocket connects with token: `wsClient.connect(token)`

## Error Handling Best Practices

1. **Network Errors**: Show retry button
2. **401 Unauthorized**: Redirect to login
3. **403 Forbidden**: Show permission denied message
4. **404 Not Found**: Show resource not found
5. **500 Server Error**: Show generic error with support contact
6. **Rate Limiting**: Show "too many requests" with retry timer

## Performance Optimization

1. **Caching**: Use `cache: true` option in useAPI hook
2. **Pagination**: Use usePaginatedAPI for large datasets
3. **Debouncing**: Debounce search inputs
4. **Lazy Loading**: Load components on demand
5. **Virtual Scrolling**: Use VirtualList for large lists
6. **Request Batching**: Batch multiple requests when possible

## Security Considerations

1. **Token Storage**: Tokens stored in localStorage (consider httpOnly cookies for production)
2. **HTTPS**: Always use HTTPS in production
3. **CORS**: Configure CORS properly in backend
4. **Input Validation**: Validate all user inputs
5. **XSS Prevention**: Use React's built-in XSS protection
6. **CSRF Protection**: Implement CSRF tokens for state-changing operations

## Next Steps

1. Replace mock data in all service classes with real API calls
2. Add WebSocket integration for real-time features
3. Implement comprehensive error handling
4. Add loading states and skeletons
5. Set up API response caching
6. Add retry logic for failed requests
7. Implement request cancellation for unmounted components
8. Add API call logging and monitoring
9. Create integration tests for API client
10. Document API usage patterns for team

## Support

For issues or questions:
- Check API documentation: http://localhost:8000/docs
- Review error logs in browser console
- Check network tab for failed requests
- Verify authentication token is valid
- Ensure backend API is running
