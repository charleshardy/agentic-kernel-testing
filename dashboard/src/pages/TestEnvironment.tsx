import React from 'react'
import { useSearchParams } from 'react-router-dom'
import EnvironmentManagementDashboard from '../components/EnvironmentManagementDashboard'

/**
 * Test Environment page component
 * Provides a dedicated page for test environment monitoring and operations
 */
const TestEnvironment: React.FC = () => {
  const [searchParams] = useSearchParams()
  const planId = searchParams.get('planId')

  return (
    <EnvironmentManagementDashboard 
      planId={planId || undefined}
      autoRefresh={true}
      refreshInterval={2000}
    />
  )
}

export default TestEnvironment