# Environment Allocation UI Integration Guide

## Overview

This guide provides comprehensive instructions for integrating the Environment Allocation UI components into your existing dashboard application.

## Prerequisites

- React 18+
- TypeScript 4.5+
- Ant Design 5.x
- React Query 3.x or 4.x
- React Router 6.x

## Installation

### 1. Install Dependencies

```bash
npm install antd react-query react-router-dom recharts react-window
npm install -D @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

### 2. TypeScript Configuration

Ensure your `tsconfig.json` includes:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["DOM", "DOM.Iterable", "ES6"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  }
}
```

## Component Integration

### 1. Basic Setup

```tsx
import React from 'react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import { EnvironmentAllocationDashboard } from './components/EnvironmentAllocationDashboard'
import { ErrorBoundary } from './components/ErrorHandling'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ConfigProvider>
          <ErrorBoundary>
            <EnvironmentAllocationDashboard />
          </ErrorBoundary>
        </ConfigProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
```

### 2. Environment Types Setup

Create your environment types file:

```tsx
// types/environment.ts
export enum EnvironmentType {
  QEMU_X86 = 'qemu-x86',
  QEMU_ARM = 'qemu-arm',
  DOCKER = 'docker',
  PHYSICAL = 'physical',
  CONTAINER = 'container'
}

export enum EnvironmentStatus {
  ALLOCATING = 'allocating',
  READY = 'ready',
  RUNNING = 'running',
  CLEANUP = 'cleanup',
  MAINTENANCE = 'maintenance',
  ERROR = 'error',
  OFFLINE = 'offline'
}

export enum EnvironmentHealth {
  HEALTHY = 'healthy',
  DEGRADED = 'degraded',
  UNHEALTHY = 'unhealthy',
  UNKNOWN = 'unknown'
}

export interface Environment {
  id: string
  type: EnvironmentType
  status: EnvironmentStatus
  architecture: string
  assignedTests: string[]
  resources: ResourceUsage
  health: EnvironmentHealth
  metadata: EnvironmentMetadata
  createdAt: Date
  lastUpdated: Date
}

export interface ResourceUsage {
  cpu: number        // Percentage 0-100
  memory: number     // Percentage 0-100
  disk: number       // Percentage 0-100
  network: NetworkMetrics
}

export interface NetworkMetrics {
  bytesIn: number
  bytesOut: number
  packetsIn: number
  packetsOut: number
}

export interface EnvironmentMetadata {
  [key: string]: any
}
```

### 3. API Service Integration

```tsx
// services/api.ts
import axios from 'axios'
import { Environment, AllocationRequest } from '../types/environment'

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || '/api',
  timeout: 10000,
})

export const environmentAPI = {
  // Get all environments
  getEnvironments: async (): Promise<Environment[]> => {
    const response = await api.get('/environments')
    return response.data
  },

  // Get environment by ID
  getEnvironment: async (id: string): Promise<Environment> => {
    const response = await api.get(`/environments/${id}`)
    return response.data
  },

  // Get allocation queue
  getAllocationQueue: async (): Promise<AllocationRequest[]> => {
    const response = await api.get('/environments/allocation/queue')
    return response.data
  },

  // Get allocation history
  getAllocationHistory: async (params?: {
    startDate?: Date
    endDate?: Date
    environmentId?: string
    testId?: string
  }): Promise<AllocationEvent[]> => {
    const response = await api.get('/environments/allocation/history', { params })
    return response.data
  },

  // Environment actions
  performEnvironmentAction: async (
    environmentId: string, 
    action: EnvironmentAction
  ): Promise<void> => {
    await api.post(`/environments/${environmentId}/actions/${action}`)
  },
}

export default api
```

### 4. Real-time Updates Setup

```tsx
// hooks/useRealTimeUpdates.ts
import { useEffect, useCallback, useRef } from 'react'
import { useQueryClient } from 'react-query'

interface UseRealTimeUpdatesProps {
  enableWebSocket?: boolean
  enableSSE?: boolean
  onAllocationEvent?: (event: AllocationEvent) => void
  onEnvironmentUpdate?: (environment: Environment) => void
}

export const useRealTimeUpdates = ({
  enableWebSocket = true,
  enableSSE = true,
  onAllocationEvent,
  onEnvironmentUpdate
}: UseRealTimeUpdatesProps) => {
  const queryClient = useQueryClient()
  const wsRef = useRef<WebSocket | null>(null)
  const sseRef = useRef<EventSource | null>(null)

  const handleAllocationEvent = useCallback((event: AllocationEvent) => {
    // Invalidate relevant queries
    queryClient.invalidateQueries(['environments'])
    queryClient.invalidateQueries(['allocation-queue'])
    queryClient.invalidateQueries(['allocation-history'])
    
    if (onAllocationEvent) {
      onAllocationEvent(event)
    }
  }, [queryClient, onAllocationEvent])

  const handleEnvironmentUpdate = useCallback((environment: Environment) => {
    // Update specific environment in cache
    queryClient.setQueryData(['environment', environment.id], environment)
    
    // Update environments list
    queryClient.setQueryData(['environments'], (old: Environment[] | undefined) => {
      if (!old) return [environment]
      return old.map(env => env.id === environment.id ? environment : env)
    })
    
    if (onEnvironmentUpdate) {
      onEnvironmentUpdate(environment)
    }
  }, [queryClient, onEnvironmentUpdate])

  useEffect(() => {
    if (enableWebSocket) {
      const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/environments/allocation'
      wsRef.current = new WebSocket(wsUrl)
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'allocation_event') {
          handleAllocationEvent(data.payload)
        } else if (data.type === 'environment_update') {
          handleEnvironmentUpdate(data.payload)
        }
      }
    }

    if (enableSSE) {
      const sseUrl = process.env.REACT_APP_SSE_URL || '/api/environments/allocation/events'
      sseRef.current = new EventSource(sseUrl)
      
      sseRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data)
        handleAllocationEvent(data)
      }
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (sseRef.current) {
        sseRef.current.close()
      }
    }
  }, [enableWebSocket, enableSSE, handleAllocationEvent, handleEnvironmentUpdate])

  return {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN || 
                 sseRef.current?.readyState === EventSource.OPEN
  }
}
```

## Performance Optimization

### 1. Code Splitting

```tsx
// Lazy load components for better performance
import { lazy, Suspense } from 'react'
import { Spin } from 'antd'

const EnvironmentAllocationDashboard = lazy(() => 
  import('./components/EnvironmentAllocationDashboard')
)
const ResourceUtilizationCharts = lazy(() => 
  import('./components/ResourceUtilizationCharts')
)

function App() {
  return (
    <Suspense fallback={<Spin size="large" />}>
      <EnvironmentAllocationDashboard />
    </Suspense>
  )
}
```

### 2. Virtualization for Large Lists

```tsx
import { VirtualizedEnvironmentTable } from './components/VirtualizedEnvironmentTable'

function EnvironmentList({ environments }: { environments: Environment[] }) {
  return (
    <VirtualizedEnvironmentTable
      environments={environments}
      height={600}
      itemHeight={60}
      enableVirtualization={environments.length > 100}
      onEnvironmentSelect={(envId) => console.log('Selected:', envId)}
      onEnvironmentAction={(envId, action) => console.log('Action:', action, envId)}
    />
  )
}
```

### 3. Memory Management

```tsx
import { useMemoryMonitor } from './hooks/usePerformanceOptimization'

function PerformanceWrapper({ children }: { children: React.ReactNode }) {
  const { logMemoryUsage } = useMemoryMonitor()

  useEffect(() => {
    // Log memory usage periodically in development
    if (process.env.NODE_ENV === 'development') {
      const interval = setInterval(() => {
        logMemoryUsage('Periodic check')
      }, 30000) // Every 30 seconds

      return () => clearInterval(interval)
    }
  }, [logMemoryUsage])

  return <>{children}</>
}
```

## Accessibility Configuration

### 1. ARIA Labels and Roles

```tsx
import { useAriaAttributes } from './hooks/useAccessibility'

function AccessibleEnvironmentTable() {
  const { generateId, getListboxProps, getOptionProps } = useAriaAttributes()
  
  const listboxId = generateId('environment-list')
  
  return (
    <div {...getListboxProps(listboxId, 'environment-table-label')}>
      {environments.map((env, index) => (
        <div
          key={env.id}
          {...getOptionProps(`env-${index}`, selectedId === env.id, false)}
        >
          {env.id}
        </div>
      ))}
    </div>
  )
}
```

### 2. Keyboard Navigation

```tsx
import { useKeyboardNavigation } from './hooks/useAccessibility'

function KeyboardNavigableList({ items }: { items: any[] }) {
  const { focusedIndex, getContainerProps, getItemProps } = useKeyboardNavigation(
    items,
    (index, item) => console.log('Selected:', item),
    { loop: true }
  )

  return (
    <div {...getContainerProps()}>
      {items.map((item, index) => (
        <div key={item.id} {...getItemProps(index)}>
          {item.name}
        </div>
      ))}
    </div>
  )
}
```

### 3. Screen Reader Support

```tsx
import { useScreenReader } from './hooks/useAccessibility'

function AccessibleNotifications() {
  const { announce } = useScreenReader()

  const handleEnvironmentChange = (environment: Environment) => {
    announce(
      `Environment ${environment.id} status changed to ${environment.status}`,
      'polite'
    )
  }

  return <div>...</div>
}
```

## Error Handling Integration

### 1. Global Error Boundary

```tsx
import { ErrorBoundary } from './components/ErrorHandling'

function App() {
  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // Send to error reporting service
        console.error('Global error:', error, errorInfo)
      }}
    >
      <YourAppComponents />
    </ErrorBoundary>
  )
}
```

### 2. Component-Level Error Handling

```tsx
import { useErrorHandler } from './hooks/useErrorHandler'
import { ErrorAlert } from './components/ErrorHandling'

function EnvironmentComponent() {
  const { errors, handleError, clearError } = useErrorHandler({
    showToast: true,
    autoRetry: true
  })

  const fetchEnvironments = async () => {
    try {
      const environments = await environmentAPI.getEnvironments()
      return environments
    } catch (error) {
      handleError(error, {
        component: 'EnvironmentComponent',
        action: 'fetchEnvironments'
      })
      throw error
    }
  }

  return (
    <div>
      {errors.map(error => (
        <ErrorAlert
          key={error.id}
          error={error}
          onDismiss={clearError}
          onRetry={(errorId) => {
            clearError(errorId)
            fetchEnvironments()
          }}
        />
      ))}
      {/* Your component content */}
    </div>
  )
}
```

## Testing Integration

### 1. Test Setup

```tsx
// test-utils.tsx
import React from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'

const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ConfigProvider>
          {children}
        </ConfigProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }
```

### 2. Component Testing

```tsx
import { render, screen, fireEvent, waitFor } from './test-utils'
import { EnvironmentAllocationDashboard } from '../EnvironmentAllocationDashboard'

test('should display environments and handle interactions', async () => {
  render(<EnvironmentAllocationDashboard />)
  
  // Wait for environments to load
  await waitFor(() => {
    expect(screen.getByText('Environment Allocation')).toBeInTheDocument()
  })
  
  // Test environment selection
  const environmentRow = screen.getByText('env-001')
  fireEvent.click(environmentRow)
  
  expect(screen.getByText('Selected Environment: env-001')).toBeInTheDocument()
})
```

## Deployment Configuration

### 1. Environment Variables

Create `.env.production`:

```bash
REACT_APP_API_BASE_URL=https://your-api-domain.com/api
REACT_APP_WS_URL=wss://your-api-domain.com/ws/environments/allocation
REACT_APP_SSE_URL=https://your-api-domain.com/api/environments/allocation/events
REACT_APP_ENVIRONMENT=production
```

### 2. Build Optimization

```json
// package.json
{
  "scripts": {
    "build": "react-scripts build",
    "build:analyze": "npm run build && npx webpack-bundle-analyzer build/static/js/*.js",
    "test:coverage": "npm test -- --coverage --watchAll=false"
  }
}
```

### 3. Docker Configuration

```dockerfile
# Dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 4. Nginx Configuration

```nginx
# nginx.conf
server {
    listen 80;
    server_name localhost;
    
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Monitoring and Analytics

### 1. Performance Monitoring

```tsx
import { PerformanceMonitor } from './components/PerformanceMonitor'

function App() {
  return (
    <div>
      <YourAppComponents />
      <PerformanceMonitor 
        enabled={process.env.NODE_ENV === 'development'}
        showDetails={true}
        onOptimizationSuggestion={(suggestion) => {
          console.log('Optimization suggestion:', suggestion)
        }}
      />
    </div>
  )
}
```

### 2. Error Tracking

```tsx
// Initialize error tracking service (e.g., Sentry)
import * as Sentry from '@sentry/react'

Sentry.init({
  dsn: process.env.REACT_APP_SENTRY_DSN,
  environment: process.env.REACT_APP_ENVIRONMENT,
  integrations: [
    new Sentry.BrowserTracing(),
  ],
  tracesSampleRate: 1.0,
})
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failures**
   - Check CORS configuration
   - Verify WebSocket URL format
   - Ensure proper SSL/TLS setup for production

2. **Performance Issues with Large Datasets**
   - Enable virtualization for tables with >100 items
   - Implement proper pagination
   - Use React.memo for expensive components

3. **Accessibility Warnings**
   - Ensure all interactive elements have proper ARIA labels
   - Test with screen readers
   - Verify keyboard navigation works correctly

4. **Memory Leaks**
   - Clean up event listeners in useEffect cleanup
   - Cancel pending requests on component unmount
   - Use the memory monitor in development

### Debug Mode

Enable debug mode in development:

```tsx
// Add to your main App component
if (process.env.NODE_ENV === 'development') {
  // Enable React Query devtools
  import('react-query/devtools-development').then(({ ReactQueryDevtools }) => {
    // Add devtools to your app
  })
}
```

## Support

For additional support and documentation:

1. Check the component prop interfaces in TypeScript
2. Review the test files for usage examples
3. Use the browser's React Developer Tools
4. Enable performance monitoring in development mode

## Migration Guide

If migrating from an existing environment management system:

1. **Data Migration**: Map your existing environment data to the new interfaces
2. **API Integration**: Update your API endpoints to match the expected format
3. **Component Replacement**: Gradually replace existing components
4. **Testing**: Run comprehensive tests before deploying to production
5. **Monitoring**: Set up proper monitoring and error tracking