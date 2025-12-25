import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import MinimalApp from './App-minimal-test'

console.log('🚀 Starting minimal test app...')
console.log('🚀 Current location:', window.location.href)

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <BrowserRouter>
    <MinimalApp />
  </BrowserRouter>
)