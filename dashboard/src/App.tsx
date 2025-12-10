import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Layout } from 'antd'
import DashboardLayout from './components/Layout/DashboardLayout'
import Dashboard from './pages/Dashboard'
import TestExecution from './pages/TestExecution'
import TestResults from './pages/TestResults'
import Coverage from './pages/Coverage'
import Performance from './pages/Performance'
import Settings from './pages/Settings'

const { Content } = Layout

function App() {
  return (
    <DashboardLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/tests" element={<TestExecution />} />
        <Route path="/results" element={<TestResults />} />
        <Route path="/coverage" element={<Coverage />} />
        <Route path="/performance" element={<Performance />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </DashboardLayout>
  )
}

export default App