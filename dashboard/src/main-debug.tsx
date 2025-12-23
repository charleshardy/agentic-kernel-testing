import React from 'react'
import ReactDOM from 'react-dom/client'

// Simple test component to verify React is working
const TestApp = () => {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>React Debug Test</h1>
      <p>If you can see this, React is working!</p>
      <p>Current time: {new Date().toLocaleString()}</p>
    </div>
  )
}

console.log('🚀 Starting React debug app...')

try {
  const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement)
  root.render(<TestApp />)
  console.log('✅ React app rendered successfully')
} catch (error) {
  console.error('❌ Error rendering React app:', error)
  document.body.innerHTML = `
    <div style="padding: 20px; color: red; font-family: Arial, sans-serif;">
      <h1>React Error</h1>
      <p>Failed to render React app:</p>
      <pre>${error}</pre>
    </div>
  `
}