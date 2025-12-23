import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { ConfigProvider } from 'antd'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'
import './index.css'

console.log('🚀 Starting full React app with improved error handling...')

// Create QueryClient with more conservative settings
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: false, // Disable retries to prevent hanging
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      // Remove complex retry logic that might cause issues
    },
    mutations: {
      retry: false, // Disable retries for mutations too
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
  console.log('✅ Full React app rendered successfully')
} catch (error) {
  console.error('❌ Error rendering full React app:', error)
  document.body.innerHTML = `
    <div style="padding: 20px; color: red; font-family: Arial, sans-serif;">
      <h1>React Error</h1>
      <p>Failed to render React app:</p>
      <pre>${error}</pre>
      <p><a href="javascript:location.reload()">Reload Page</a></p>
    </div>
  `
}