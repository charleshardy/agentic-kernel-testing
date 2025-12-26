import React from 'react'
import { useSearchParams } from 'react-router-dom'
import EnvironmentAllocationDashboard from '../components/EnvironmentAllocationDashboard'

/**
 * Environment Allocation page component
 * Provides a dedicated page for environment allocation monitoring and management
 */
const EnvironmentAllocation: React.FC = () => {
  const [searchParams] = useSearchParams()
  const planId = searchParams.get('planId')

  return (
    <EnvironmentAllocationDashboard 
      planId={planId || undefined}
      autoRefresh={true}
      refreshInterval={2000}
    />
  )
}

export default EnvironmentAllocation