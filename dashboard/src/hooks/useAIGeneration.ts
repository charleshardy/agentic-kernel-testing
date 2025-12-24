import { useMutation, useQueryClient } from 'react-query'
import { message } from 'antd'
import apiService, { TestCase, EnhancedTestCase } from '../services/api'
import { testCaseKeys } from './useTestCases'

interface GenerateFromDiffParams {
  diff: string
  maxTests: number
  testTypes: string[]
}

interface GenerateFromFunctionParams {
  functionName: string
  filePath: string
  subsystem: string
  maxTests: number
}

interface GenerateKernelDriverParams {
  functionName: string
  filePath: string
  subsystem: string
  testTypes: string[]
}

interface UseAIGenerationOptions {
  onSuccess?: (response: any, type: 'diff' | 'function' | 'kernel') => void
  onError?: (error: any, type: 'diff' | 'function' | 'kernel') => void
  preserveFilters?: boolean
  enableOptimisticUpdates?: boolean
}

// Helper function to generate optimistic test cases
const generateOptimisticTestCases = (
  type: 'diff' | 'function' | 'kernel',
  params: GenerateFromDiffParams | GenerateFromFunctionParams | GenerateKernelDriverParams,
  count: number = 3
): EnhancedTestCase[] => {
  const baseTime = new Date().toISOString()
  const testCases: EnhancedTestCase[] = []

  for (let i = 0; i < count; i++) {
    const testCase: EnhancedTestCase = {
      id: `optimistic-${type}-${Date.now()}-${i}`,
      name: type === 'diff' 
        ? `Generated Test ${i + 1} (from diff)` 
        : type === 'kernel'
        ? `Kernel Driver Test ${i + 1} (${(params as GenerateKernelDriverParams).functionName})`
        : `Generated Test ${i + 1} (${(params as GenerateFromFunctionParams).functionName})`,
      description: type === 'diff'
        ? 'Test case generated from code diff analysis'
        : type === 'kernel'
        ? `Kernel test driver generated for function ${(params as GenerateKernelDriverParams).functionName}`
        : `Test case generated for function ${(params as GenerateFromFunctionParams).functionName}`,
      test_type: 'unit',
      target_subsystem: type === 'function' 
        ? (params as GenerateFromFunctionParams).subsystem 
        : type === 'kernel'
        ? (params as GenerateKernelDriverParams).subsystem
        : 'unknown',
      code_paths: type === 'function' 
        ? [(params as GenerateFromFunctionParams).filePath]
        : type === 'kernel'
        ? [(params as GenerateKernelDriverParams).filePath]
        : [],
      execution_time_estimate: 60,
      test_script: '#!/bin/bash\n# Generated test script (pending)\necho "Test generation in progress..."',
      metadata: {
        optimistic: true, // Mark as optimistic update
      },
      generation_info: {
        method: type === 'diff' ? 'ai_diff' : type === 'kernel' ? 'ai_kernel_driver' : 'ai_function',
        generated_at: baseTime,
        source_data: type === 'diff' 
          ? { diff_content: (params as GenerateFromDiffParams).diff }
          : type === 'kernel'
          ? {
              function_name: (params as GenerateKernelDriverParams).functionName,
              file_path: (params as GenerateKernelDriverParams).filePath,
              subsystem: (params as GenerateKernelDriverParams).subsystem,
              test_types: (params as GenerateKernelDriverParams).testTypes
            }
          : { 
              function_name: (params as GenerateFromFunctionParams).functionName,
              file_path: (params as GenerateFromFunctionParams).filePath,
              subsystem: (params as GenerateFromFunctionParams).subsystem
            }
      },
      execution_status: 'never_run',
      created_at: baseTime,
      updated_at: baseTime,
    }
    testCases.push(testCase)
  }

  return testCases
}

export const useAIGeneration = (options: UseAIGenerationOptions = {}) => {
  const queryClient = useQueryClient()
  const { onSuccess, onError, preserveFilters = true, enableOptimisticUpdates = true } = options

  const generateFromDiffMutation = useMutation(
    (data: GenerateFromDiffParams) =>
      apiService.generateTestsFromDiff(data.diff, data.maxTests, data.testTypes),
    {
      onMutate: async (data: GenerateFromDiffParams) => {
        // Show loading indicator during generation
        message.loading('Generating tests from diff...', 0)

        if (enableOptimisticUpdates) {
          // Cancel any outgoing refetches (so they don't overwrite our optimistic update)
          await queryClient.cancelQueries(testCaseKeys.lists())

          // Snapshot the previous value
          const previousTestCases = queryClient.getQueriesData(testCaseKeys.lists())

          // Generate optimistic test cases
          const optimisticTests = generateOptimisticTestCases('diff', data, Math.min(data.maxTests, 5))

          // Optimistically update all testCases queries
          queryClient.setQueriesData(testCaseKeys.lists(), (old: any) => {
            if (!old?.tests) return old
            
            return {
              ...old,
              tests: [...optimisticTests, ...old.tests],
              pagination: {
                ...old.pagination,
                total_items: (old.pagination?.total_items || 0) + optimisticTests.length
              }
            }
          })

          // Return a context object with the snapshotted value
          return { previousTestCases }
        }
      },
      onSuccess: async (response) => {
        message.destroy() // Clear loading message
        message.success(`Generated ${response.data?.generated_count || 'multiple'} test cases from diff`)
        
        // Force immediate refresh of test-related queries
        await queryClient.invalidateQueries(testCaseKeys.lists())
        await queryClient.refetchQueries(testCaseKeys.lists())
        
        // Also refresh active executions
        queryClient.invalidateQueries('activeExecutions')
        
        // Call custom success handler if provided
        onSuccess?.(response, 'diff')
      },
      onError: (error: any, variables, context: any) => {
        message.destroy() // Clear loading message
        
        // Better error message handling
        let errorMessage = 'Failed to generate tests from diff'
        
        // Check for various error message sources
        if (error?.response?.data?.message) {
          errorMessage += `: ${error.response.data.message}`
        } else if (error?.response?.data?.error) {
          errorMessage += `: ${error.response.data.error}`
        } else if (error?.message && error.message !== 'undefined') {
          errorMessage += `: ${error.message}`
        } else if (error?.response?.status) {
          errorMessage += `: HTTP ${error.response.status}`
        } else if (error?.code) {
          errorMessage += `: ${error.code}`
        } else if (typeof error === 'string') {
          errorMessage += `: ${error}`
        } else {
          errorMessage += ': Network or server error occurred'
        }
        
        console.error('Diff generation error:', {
          error,
          variables,
          response: error?.response,
          message: error?.message,
          status: error?.response?.status,
          data: error?.response?.data
        })
        
        message.error(errorMessage)
        
        if (enableOptimisticUpdates && context?.previousTestCases) {
          // Rollback optimistic updates on error
          context.previousTestCases.forEach(([queryKey, data]: [any, any]) => {
            queryClient.setQueryData(queryKey, data)
          })
        }
        
        onError?.(error, 'diff')
      },
    }
  )

  const generateFromFunctionMutation = useMutation(
    (data: GenerateFromFunctionParams) =>
      apiService.generateTestsFromFunction(data.functionName, data.filePath, data.subsystem, data.maxTests),
    {
      onMutate: async (data: GenerateFromFunctionParams) => {
        // Show loading indicator during generation
        message.loading('Generating tests from function...', 0)

        if (enableOptimisticUpdates) {
          // Cancel any outgoing refetches (so they don't overwrite our optimistic update)
          await queryClient.cancelQueries(testCaseKeys.lists())

          // Snapshot the previous value
          const previousTestCases = queryClient.getQueriesData(testCaseKeys.lists())

          // Generate optimistic test cases
          const optimisticTests = generateOptimisticTestCases('function', data, Math.min(data.maxTests, 5))

          // Optimistically update all testCases queries
          queryClient.setQueriesData(testCaseKeys.lists(), (old: any) => {
            if (!old?.tests) return old
            
            return {
              ...old,
              tests: [...optimisticTests, ...old.tests],
              pagination: {
                ...old.pagination,
                total_items: (old.pagination?.total_items || 0) + optimisticTests.length
              }
            }
          })

          // Return a context object with the snapshotted value
          return { previousTestCases }
        }
      },
      onSuccess: async (response) => {
        message.destroy() // Clear loading message
        message.success(`Generated ${response.data?.generated_count || 'multiple'} test cases for function`)
        
        // Force immediate refresh of test-related queries
        await queryClient.invalidateQueries(testCaseKeys.lists())
        await queryClient.refetchQueries(testCaseKeys.lists())
        
        // Also refresh active executions
        queryClient.invalidateQueries('activeExecutions')
        
        // Call custom success handler if provided
        onSuccess?.(response, 'function')
      },
      onError: (error: any, variables, context: any) => {
        message.destroy() // Clear loading message
        
        // Better error message handling
        let errorMessage = 'Failed to generate tests from function'
        
        // Check for various error message sources
        if (error?.response?.data?.message) {
          errorMessage += `: ${error.response.data.message}`
        } else if (error?.response?.data?.error) {
          errorMessage += `: ${error.response.data.error}`
        } else if (error?.message && error.message !== 'undefined') {
          errorMessage += `: ${error.message}`
        } else if (error?.response?.status) {
          errorMessage += `: HTTP ${error.response.status}`
        } else if (error?.code) {
          errorMessage += `: ${error.code}`
        } else if (typeof error === 'string') {
          errorMessage += `: ${error}`
        } else {
          errorMessage += ': Network or server error occurred'
        }
        
        console.error('Function generation error:', {
          error,
          variables,
          response: error?.response,
          message: error?.message,
          status: error?.response?.status,
          data: error?.response?.data
        })
        
        message.error(errorMessage)
        
        if (enableOptimisticUpdates && context?.previousTestCases) {
          // Rollback optimistic updates on error
          context.previousTestCases.forEach(([queryKey, data]: [any, any]) => {
            queryClient.setQueryData(queryKey, data)
          })
        }
        
        onError?.(error, 'function')
      },
    }
  )

  const generateKernelDriverMutation = useMutation(
    (data: GenerateKernelDriverParams) =>
      apiService.generateKernelTestDriver(data.functionName, data.filePath, data.subsystem, data.testTypes),
    {
      onMutate: async (data: GenerateKernelDriverParams) => {
        // Show loading indicator during generation
        message.loading('Generating kernel test driver...', 0)

        if (enableOptimisticUpdates) {
          // Cancel any outgoing refetches (so they don't overwrite our optimistic update)
          await queryClient.cancelQueries(testCaseKeys.lists())

          // Snapshot the previous value
          const previousTestCases = queryClient.getQueriesData(testCaseKeys.lists())

          // Generate optimistic test cases
          const optimisticTests = generateOptimisticTestCases('kernel', data, 3)

          // Optimistically update all testCases queries
          queryClient.setQueriesData(testCaseKeys.lists(), (old: any) => {
            if (!old?.tests) return old
            
            return {
              ...old,
              tests: [...optimisticTests, ...old.tests],
              pagination: {
                ...old.pagination,
                total_items: (old.pagination?.total_items || 0) + optimisticTests.length
              }
            }
          })

          // Return a context object with the snapshotted value
          return { previousTestCases }
        }
      },
      onSuccess: async (response) => {
        message.destroy() // Clear loading message
        message.success(`Generated kernel test driver with ${response.data?.generated_count || 'multiple'} test cases`)
        
        // Force immediate refresh of test-related queries
        await queryClient.invalidateQueries(testCaseKeys.lists())
        await queryClient.refetchQueries(testCaseKeys.lists())
        
        // Also refresh active executions
        queryClient.invalidateQueries('activeExecutions')
        
        // Call custom success handler if provided
        onSuccess?.(response, 'kernel')
      },
      onError: (error: any, variables, context: any) => {
        message.destroy() // Clear loading message
        
        // Better error message handling
        let errorMessage = 'Failed to generate kernel test driver'
        
        // Check for various error message sources
        if (error?.response?.data?.message) {
          errorMessage += `: ${error.response.data.message}`
        } else if (error?.response?.data?.error) {
          errorMessage += `: ${error.response.data.error}`
        } else if (error?.message && error.message !== 'undefined') {
          errorMessage += `: ${error.message}`
        } else if (error?.response?.status) {
          errorMessage += `: HTTP ${error.response.status}`
        } else if (error?.code) {
          errorMessage += `: ${error.code}`
        } else if (typeof error === 'string') {
          errorMessage += `: ${error}`
        } else {
          errorMessage += ': Network or server error occurred'
        }
        
        console.error('Kernel driver generation error:', {
          error,
          variables,
          response: error?.response,
          message: error?.message,
          status: error?.response?.status,
          data: error?.response?.data
        })
        
        message.error(errorMessage)
        
        if (enableOptimisticUpdates && context?.previousTestCases) {
          // Rollback optimistic updates on error
          context.previousTestCases.forEach(([queryKey, data]: [any, any]) => {
            queryClient.setQueryData(queryKey, data)
          })
        }
        
        onError?.(error, 'kernel')
      },
    }
  )

  return {
    generateFromDiff: generateFromDiffMutation.mutate,
    generateFromFunction: generateFromFunctionMutation.mutate,
    generateKernelDriver: generateKernelDriverMutation.mutate,
    isGeneratingFromDiff: generateFromDiffMutation.isLoading,
    isGeneratingFromFunction: generateFromFunctionMutation.isLoading,
    isGeneratingKernelDriver: generateKernelDriverMutation.isLoading,
    isGenerating: generateFromDiffMutation.isLoading || generateFromFunctionMutation.isLoading || generateKernelDriverMutation.isLoading,
  }
}

export default useAIGeneration