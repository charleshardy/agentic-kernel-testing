import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import App from './App-minimal'
import './index.css'

console.log('🚀 Starting minimal React app...')

try {
  const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement)
  root.render(
    <React.StrictMode>
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
    </React.StrictMode>,
  )
  console.log('✅ Minimal React app rendered successfully')
} catch (error) {
  console.error('❌ Error rendering minimal React app:', error)
  document.body.innerHTML = `
    <div style="padding: 20px; color: red; font-family: Arial, sans-serif;">
      <h1>React Error</h1>
      <p>Failed to render React app:</p>
      <pre>${error}</pre>
    </div>
  `
}