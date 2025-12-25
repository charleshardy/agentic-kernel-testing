import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import App from './App-fixed'
import ErrorBoundary from './components/ErrorBoundary'
import './index.css'

console.log('🚀 Starting dashboard WITHOUT React Query...')

try {
  const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement)
  root.render(
    <React.StrictMode>
      <ErrorBoundary>
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
      </ErrorBoundary>
    </React.StrictMode>,
  )
  console.log('✅ Dashboard without React Query rendered successfully')
} catch (error) {
  console.error('❌ Error rendering dashboard:', error)
  document.body.innerHTML = `
    <div style="padding: 20px; color: red; font-family: Arial, sans-serif;">
      <h1>Dashboard Error</h1>
      <p>Failed to render dashboard:</p>
      <pre>${error}</pre>
      <p><a href="javascript:location.reload()">Reload Page</a></p>
    </div>
  `
}