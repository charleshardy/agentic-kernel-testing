import React from 'react'
import ReactDOM from 'react-dom/client'

console.log('🚀 Starting React test...')

// Simple React component without any external dependencies
const TestApp: React.FC = () => {
  const [count, setCount] = React.useState(0)
  
  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: 'Arial, sans-serif',
      background: '#f0f2f5',
      minHeight: '100vh'
    }}>
      <h1 style={{ color: '#1890ff' }}>React Test Working!</h1>
      <p>If you can see this, React is working correctly.</p>
      <p>Current time: {new Date().toLocaleString()}</p>
      
      <div style={{ 
        marginTop: '20px', 
        padding: '16px', 
        background: 'white', 
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <h3>React State Test:</h3>
        <p>Count: {count}</p>
        <button 
          onClick={() => setCount(count + 1)}
          style={{
            padding: '8px 16px',
            background: '#1890ff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            marginRight: '8px'
          }}
        >
          Increment
        </button>
        <button 
          onClick={() => setCount(0)}
          style={{
            padding: '8px 16px',
            background: '#ff4d4f',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Reset
        </button>
      </div>
      
      <div style={{ 
        marginTop: '20px', 
        padding: '16px', 
        background: 'white', 
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <h3>Debug Info:</h3>
        <p>React Version: {React.version}</p>
        <p>Location: {window.location.href}</p>
        <p>Timestamp: {Date.now()}</p>
      </div>
    </div>
  )
}

try {
  const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement)
  root.render(<TestApp />)
  console.log('✅ React test rendered successfully')
} catch (error) {
  console.error('❌ Error rendering React test:', error)
  document.body.innerHTML = `
    <div style="padding: 20px; color: red; font-family: Arial, sans-serif;">
      <h1>React Error</h1>
      <p>Failed to render React app:</p>
      <pre>${error}</pre>
    </div>
  `
}