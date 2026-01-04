import React from 'react'
import { useSearchParams } from 'react-router-dom'
import EnvironmentManagementDashboard from '../components/EnvironmentManagementDashboard'

/**
 * Environment Management page component
 * Provides a dedicated page for environment management monitoring and operations
 */
const EnvironmentManagement: React.FC = () => {
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

export default EnvironmentManagement