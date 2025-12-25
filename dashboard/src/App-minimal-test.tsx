import React from 'react'
import { Routes, Route } from 'react-router-dom'
import WorkflowBasic from './pages/WorkflowBasic'

function MinimalApp() {
  console.log('🔧 MinimalApp rendering - pathname:', window.location.pathname)
  
  return (
    <div style={{ padding: '20px' }}>
      <h1>Minimal App Test</h1>
      <p>Current path: {window.location.pathname}</p>
      
      <Routes>
        <Route path="/" element={
          <div>
            <h2>Home Route</h2>
            <p>This is the home route</p>
            <a href="/workflow-basic">Go to Workflow Basic</a>
          </div>
        } />
        
        <Route path="/workflow-basic" element={
          <div>
            <h2>Workflow Basic Route Matched!</h2>
            <WorkflowBasic />
          </div>
        } />
        
        <Route path="*" element={
          <div>
            <h2>Catch-all Route</h2>
            <p>Path: {window.location.pathname}</p>
            <p>This route was not matched by any specific route.</p>
            <a href="/">Go Home</a> | <a href="/workflow-basic">Go to Workflow Basic</a>
          </div>
        } />
      </Routes>
    </div>
  )
}

export default MinimalApp