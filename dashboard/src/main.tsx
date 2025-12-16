import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { ConfigProvider } from 'antd'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors except 401 (auth errors should retry once)
        if (error?.response?.status >= 400 && error?.response?.status < 500 && error?.response?.status !== 401) {
          return false
        }
        // Retry up to 2 times for network errors and 5xx errors
        return failureCount < 2
      },
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
    },
    mutations: {
      retry: (failureCount, error: any) => {
        // Don't retry mutations on 4xx errors except 401
        if (error?.response?.status >= 400 && error?.response?.status < 500 && error?.response?.status !== 401) {
          return false
        }
        // Retry once for network errors and 5xx errors
        return failureCount < 1
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000), // Exponential backoff
    },
  },
})

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider
          theme={{
            token: {
              colorPrimary: '#1890ff',
            },
          }}
        >
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </ConfigProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)