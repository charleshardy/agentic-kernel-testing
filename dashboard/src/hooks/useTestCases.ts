import { useQuery, useMutation, useQueryClient, UseQueryOptions } from 'react-query'
import { message } from 'antd'
import apiService, { 
  EnhancedTestCase, 
  TestListResponse, 
  TestCaseFilters, 
  BulkOperationRequest,
  BulkOperationResponse,
  TestCase
} from '../services/api'

// Query keys for test case data
export const testCaseKeys = {
  all: ['testCases'] as const,
  lists: () => [...testCaseKeys.all, 'list'] as const,
  list: (filters: TestCaseFilters) => [...testCaseKeys.lists(), filters] as const,
  details: () => [...testCaseKeys.all, 'detail'] as const,
  detail: (id: string) => [...testCaseKeys.details(), id] as const,
}

interface UseTestCasesOptions {
  filters?: TestCaseFilters
  page?: number
  pageSize?: number
  enabled?: boolean
}

interface UseTestCaseOptions {
  testId: string
  enabled?: boolean
}

interface UseTestCaseMutationOptions {
  onSuccess?: (data: any) => void
  onError?: (error: any) => void
  preserveFilters?: boolean
  enableOptimisticUpdates?: boolean
}

// Hook for fetching test cases list with filtering and pagination
export const useTestCases = (options: UseTestCasesOptions = {}) => {
  const { filters = {}, page = 1, pageSize = 20, enabled = true } = options

  const queryParams = {
    page,
    page_size: pageSize,
    ...filters,
  }

  return useQuery(
    testCaseKeys.list(filters),
    () => apiService.getTests(queryParams),
    {
      enabled,
      keepPreviousData: true, // Keep previous data while loading new page
      staleTime: 30 * 1000, // 30 seconds - shorter stale time for more frequent updates
      cacheTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: true, // Refetch when window gains focus
      refetchInterval: 10000, // Refetch every 10 seconds when component is active
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors except 401
        if (error?.response?.status >= 400 && error?.response?.status < 500 && error?.response?.status !== 401) {
          return false
        }
        return failureCount < 2
      },
    }
  )
}

// Hook for fetching a single test case
export const useTestCase = (options: UseTestCaseOptions) => {
  const { testId, enabled = true } = options

  return useQuery(
    testCaseKeys.detail(testId),
    () => apiService.getTestById(testId),
    {
      enabled: enabled && !!testId,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error: any) => {
        if (error?.response?.status >= 400 && error?.response?.status < 500 && error?.response?.status !== 401) {
          return false
        }
        return failureCount < 2
      },
    }
  )
}

// Hook for test case mutations (update, delete, execute, bulk operations)
export const useTestCaseMutations = (options: UseTestCaseMutationOptions = {}) => {
  const queryClient = useQueryClient()
  const { onSuccess, onError, preserveFilters = true, enableOptimisticUpdates = true } = options

  // Update test case mutation
  const updateTestMutation = useMutation(
    ({ testId, updates }: { testId: string; updates: Partial<TestCase> }) =>
      apiService.updateTest(testId, updates),
    {
      onMutate: async ({ testId, updates }) => {
        if (enableOptimisticUpdates) {
          // Cancel any outgoing refetches
          await queryClient.cancelQueries(testCaseKeys.detail(testId))
          await queryClient.cancelQueries(testCaseKeys.lists())

          // Snapshot the previous values
          const previousTestCase = queryClient.getQueryData(testCaseKeys.detail(testId))
          const previousTestLists = queryClient.getQueriesData(testCaseKeys.lists())

          // Optimistically update the test case detail
          const existingTestCase = queryClient.getQueryData<EnhancedTestCase>(testCaseKeys.detail(testId))
          if (existingTestCase) {
            queryClient.setQueryData(testCaseKeys.detail(testId), {
              ...existingTestCase,
              ...updates,
              updated_at: new Date().toISOString(),
            })
          }

          // Optimistically update test lists
          const testListQueries = queryClient.getQueriesData(testCaseKeys.lists())
          testListQueries.forEach(([queryKey, data]) => {
            if (data && (data as TestListResponse).tests) {
              const oldData = data as TestListResponse
              queryClient.setQueryData(queryKey, {
                ...oldData,
                tests: oldData.tests.map(test => 
                  test.id === testId 
                    ? { ...test, ...updates, updated_at: new Date().toISOString() }
                    : test
                )
              })
            }
          })

          return { previousTestCase, previousTestLists }
        }
      },
      onSuccess: (data, variables) => {
        message.success('Test case updated successfully')
        
        // Update the cache with real data
        queryClient.setQueryData(testCaseKeys.detail(variables.testId), data)
        
        // Invalidate and refetch lists to ensure consistency
        if (preserveFilters) {
          queryClient.invalidateQueries(testCaseKeys.lists())
        } else {
          queryClient.resetQueries(testCaseKeys.lists())
        }
        
        onSuccess?.(data)
      },
      onError: (error: any, variables, context: any) => {
        message.error(`Failed to update test case: ${error.message}`)
        
        if (enableOptimisticUpdates && context) {
          // Rollback optimistic updates
          if (context.previousTestCase) {
            queryClient.setQueryData(testCaseKeys.detail(variables.testId), context.previousTestCase)
          }
          if (context.previousTestLists) {
            context.previousTestLists.forEach(([queryKey, data]: [any, any]) => {
              queryClient.setQueryData(queryKey, data)
            })
          }
        }
        
        onError?.(error)
      },
    }
  )

  // Delete test case mutation
  const deleteTestMutation = useMutation(
    (testId: string) => apiService.deleteTest(testId),
    {
      onMutate: async (testId) => {
        if (enableOptimisticUpdates) {
          // Cancel any outgoing refetches
          await queryClient.cancelQueries(testCaseKeys.lists())

          // Snapshot the previous values
          const previousTestLists = queryClient.getQueriesData(testCaseKeys.lists())

          // Optimistically remove from test lists
          const testListQueries = queryClient.getQueriesData(testCaseKeys.lists())
          testListQueries.forEach(([queryKey, data]) => {
            if (data && (data as TestListResponse).tests) {
              const oldData = data as TestListResponse
              queryClient.setQueryData(queryKey, {
                ...oldData,
                tests: oldData.tests.filter(test => test.id !== testId),
                pagination: {
                  ...oldData.pagination,
                  total_items: Math.max(0, oldData.pagination.total_items - 1)
                }
              })
            }
          })

          return { previousTestLists }
        }
      },
      onSuccess: (data, testId) => {
        message.success('Test case deleted successfully')
        
        // Remove from cache
        queryClient.removeQueries(testCaseKeys.detail(testId))
        
        // Invalidate lists to ensure consistency
        queryClient.invalidateQueries(testCaseKeys.lists())
        
        onSuccess?.(data)
      },
      onError: (error: any, testId, context: any) => {
        message.error(`Failed to delete test case: ${error.message}`)
        
        if (enableOptimisticUpdates && context?.previousTestLists) {
          // Rollback optimistic updates
          context.previousTestLists.forEach(([queryKey, data]: [any, any]) => {
            queryClient.setQueryData(queryKey, data)
          })
        }
        
        onError?.(error)
      },
    }
  )

  // Execute test case mutation
  const executeTestMutation = useMutation(
    ({ testId, options: execOptions }: { testId: string; options?: any }) =>
      apiService.executeTest(testId, execOptions),
    {
      onSuccess: (data, variables) => {
        message.success(`Test execution started. Plan ID: ${data.execution_plan_id}`)
        
        // Refresh active executions
        queryClient.invalidateQueries('activeExecutions')
        
        // Update test case status if we have it cached
        const existingTestCase = queryClient.getQueryData<EnhancedTestCase>(testCaseKeys.detail(variables.testId))
        if (existingTestCase) {
          queryClient.setQueryData(testCaseKeys.detail(variables.testId), {
            ...existingTestCase,
            execution_status: 'running',
            last_execution_at: new Date().toISOString(),
          })
        }
        
        onSuccess?.(data)
      },
      onError: (error: any) => {
        message.error(`Failed to execute test case: ${error.message}`)
        onError?.(error)
      },
    }
  )

  // Bulk operations mutation
  const bulkOperationMutation = useMutation(
    (request: BulkOperationRequest) => apiService.bulkOperations(request),
    {
      onMutate: async (request) => {
        if (enableOptimisticUpdates && request.operation === 'delete') {
          // Cancel any outgoing refetches
          await queryClient.cancelQueries(testCaseKeys.lists())

          // Snapshot the previous values
          const previousTestLists = queryClient.getQueriesData(testCaseKeys.lists())

          // Optimistically remove deleted tests from lists
          const testListQueries = queryClient.getQueriesData(testCaseKeys.lists())
          testListQueries.forEach(([queryKey, data]) => {
            if (data && (data as TestListResponse).tests) {
              const oldData = data as TestListResponse
              queryClient.setQueryData(queryKey, {
                ...oldData,
                tests: oldData.tests.filter(test => !request.test_ids.includes(test.id)),
                pagination: {
                  ...oldData.pagination,
                  total_items: Math.max(0, oldData.pagination.total_items - request.test_ids.length)
                }
              })
            }
          })

          return { previousTestLists }
        }
      },
      onSuccess: (data, variables) => {
        const { operation, test_ids } = variables
        const { summary } = data
        
        if (summary.successful > 0) {
          message.success(`Bulk ${operation}: ${summary.successful}/${summary.total} operations completed successfully`)
        }
        
        if (summary.failed > 0) {
          message.warning(`Bulk ${operation}: ${summary.failed}/${summary.total} operations failed`)
        }
        
        // Remove deleted tests from cache
        if (operation === 'delete') {
          test_ids.forEach(testId => {
            queryClient.removeQueries(testCaseKeys.detail(testId))
          })
        }
        
        // Refresh lists and active executions
        queryClient.invalidateQueries(testCaseKeys.lists())
        if (operation === 'execute') {
          queryClient.invalidateQueries('activeExecutions')
        }
        
        onSuccess?.(data)
      },
      onError: (error: any, variables, context: any) => {
        message.error(`Bulk ${variables.operation} failed: ${error.message}`)
        
        if (enableOptimisticUpdates && context?.previousTestLists) {
          // Rollback optimistic updates
          context.previousTestLists.forEach(([queryKey, data]: [any, any]) => {
            queryClient.setQueryData(queryKey, data)
          })
        }
        
        onError?.(error)
      },
    }
  )

  return {
    // Mutation functions
    updateTest: updateTestMutation.mutate,
    deleteTest: deleteTestMutation.mutate,
    executeTest: executeTestMutation.mutate,
    bulkOperation: bulkOperationMutation.mutate,
    
    // Loading states
    isUpdating: updateTestMutation.isLoading,
    isDeleting: deleteTestMutation.isLoading,
    isExecuting: executeTestMutation.isLoading,
    isBulkOperating: bulkOperationMutation.isLoading,
    
    // Combined loading state
    isLoading: updateTestMutation.isLoading || 
               deleteTestMutation.isLoading || 
               executeTestMutation.isLoading || 
               bulkOperationMutation.isLoading,
  }
}

// Hook for invalidating test case queries (useful for manual refresh)
export const useTestCaseInvalidation = () => {
  const queryClient = useQueryClient()

  return {
    invalidateAll: () => queryClient.invalidateQueries(testCaseKeys.all),
    invalidateLists: () => queryClient.invalidateQueries(testCaseKeys.lists()),
    invalidateDetail: (testId: string) => queryClient.invalidateQueries(testCaseKeys.detail(testId)),
    refetchAll: () => queryClient.refetchQueries(testCaseKeys.all),
    refetchLists: () => queryClient.refetchQueries(testCaseKeys.lists()),
  }
}

export default useTestCases