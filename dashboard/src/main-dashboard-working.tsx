import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { ConfigProvider } from 'antd'
import App from './App-fixed'
import ErrorBoundary from './components/ErrorBoundary'
import './index.css'

console.log('🚀 Starting full dashboard with working components...')

// Simplified QueryClient - this was likely the issue
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: false, // Disable complex retry logic that was causing issues
      staleTime: 5 * 60 * 1000,
      cacheTime: 10 * 60 * 1000,
    },
    mutations: {
      retry: false, // Disable complex retry logic
    },
  },
})

try {
  const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement)
  root.render(
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
  console.log('✅ Full dashboard rendered successfully')
} catch (error) {
  console.error('❌ Error rendering full dashboard:', error)
  document.body.innerHTML = `
    <div style="padding: 20px; color: red; font-family: Arial, sans-serif;">
      <h1>Dashboard Error</h1>
      <p>Failed to render dashboard:</p>
      <pre>${error}</pre>
      <p><a href="javascript:location.reload()">Reload Page</a></p>
    </div>
  `
}