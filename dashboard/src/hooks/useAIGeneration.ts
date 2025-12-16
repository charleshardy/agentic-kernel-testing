import { useMutation, useQueryClient } from 'react-query'
import { message } from 'antd'
import apiService, { TestCase } from '../services/api'

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

interface UseAIGenerationOptions {
  onSuccess?: (response: any, type: 'diff' | 'function') => void
  onError?: (error: any, type: 'diff' | 'function') => void
  preserveFilters?: boolean
  enableOptimisticUpdates?: boolean
}

// Helper function to generate optimistic test cases
const generateOptimisticTestCases = (
  type: 'diff' | 'function',
  params: GenerateFromDiffParams | GenerateFromFunctionParams,
  count: number = 3
): TestCase[] => {
  const baseTime = new Date().toISOString()
  const testCases: TestCase[] = []

  for (let i = 0; i < count; i++) {
    const testCase: TestCase = {
      id: `optimistic-${type}-${Date.now()}-${i}`,
      name: type === 'diff' 
        ? `Generated Test ${i + 1} (from diff)` 
        : `Generated Test ${i + 1} (${(params as GenerateFromFunctionParams).functionName})`,
      description: type === 'diff'
        ? 'Test case generated from code diff analysis'
        : `Test case generated for function ${(params as GenerateFromFunctionParams).functionName}`,
      test_type: 'unit',
      target_subsystem: type === 'function' 
        ? (params as GenerateFromFunctionParams).subsystem 
        : 'unknown',
      code_paths: type === 'function' 
        ? [(params as GenerateFromFunctionParams).filePath]
        : [],
      execution_time_estimate: 60,
      test_script: '#!/bin/bash\n# Generated test script (pending)\necho "Test generation in progress..."',
      metadata: {
        generation_method: type === 'diff' ? 'ai_diff' : 'ai_function',
        execution_status: 'pending',
        generated_at: baseTime,
        optimistic: true, // Mark as optimistic update
        source_data: type === 'diff' 
          ? { diff_content: (params as GenerateFromDiffParams).diff }
          : { 
              function_name: (params as GenerateFromFunctionParams).functionName,
              file_path: (params as GenerateFromFunctionParams).filePath,
              subsystem: (params as GenerateFromFunctionParams).subsystem
            }
      },
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
          await queryClient.cancelQueries(['testCases'])

          // Snapshot the previous value
          const previousTestCases = queryClient.getQueriesData(['testCases'])

          // Generate optimistic test cases
          const optimisticTests = generateOptimisticTestCases('diff', data, Math.min(data.maxTests, 5))

          // Optimistically update all testCases queries
          queryClient.setQueriesData(['testCases'], (old: any) => {
            if (!old?.tests) return old
            
            return {
              ...old,
              tests: [...optimisticTests, ...old.tests],
              total: (old.total || 0) + optimisticTests.length
            }
          })

          // Return a context object with the snapshotted value
          return { previousTestCases }
        }
      },
      onSuccess: (response) => {
        message.destroy() // Clear loading message
        message.success(`Generated ${response.data?.generated_count || 'multiple'} test cases from diff`)
        
        // Refresh test-related queries to get real data
        if (preserveFilters) {
          queryClient.invalidateQueries(['testCases'])
        } else {
          queryClient.invalidateQueries(['testCases'])
          queryClient.resetQueries(['testCases'])
        }
        
        // Also refresh active executions
        queryClient.invalidateQueries('activeExecutions')
        
        // Call custom success handler if provided
        onSuccess?.(response, 'diff')
      },
      onError: (error: any, variables, context: any) => {
        message.destroy() // Clear loading message
        message.error(`Failed to generate tests from diff: ${error.message}`)
        
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
          await queryClient.cancelQueries(['testCases'])

          // Snapshot the previous value
          const previousTestCases = queryClient.getQueriesData(['testCases'])

          // Generate optimistic test cases
          const optimisticTests = generateOptimisticTestCases('function', data, Math.min(data.maxTests, 5))

          // Optimistically update all testCases queries
          queryClient.setQueriesData(['testCases'], (old: any) => {
            if (!old?.tests) return old
            
            return {
              ...old,
              tests: [...optimisticTests, ...old.tests],
              total: (old.total || 0) + optimisticTests.length
            }
          })

          // Return a context object with the snapshotted value
          return { previousTestCases }
        }
      },
      onSuccess: (response) => {
        message.destroy() // Clear loading message
        message.success(`Generated ${response.data?.generated_count || 'multiple'} test cases for function`)
        
        // Refresh test-related queries to get real data
        if (preserveFilters) {
          queryClient.invalidateQueries(['testCases'])
        } else {
          queryClient.invalidateQueries(['testCases'])
          queryClient.resetQueries(['testCases'])
        }
        
        // Also refresh active executions
        queryClient.invalidateQueries('activeExecutions')
        
        // Call custom success handler if provided
        onSuccess?.(response, 'function')
      },
      onError: (error: any, variables, context: any) => {
        message.destroy() // Clear loading message
        message.error(`Failed to generate tests from function: ${error.message}`)
        
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

  return {
    generateFromDiff: generateFromDiffMutation.mutate,
    generateFromFunction: generateFromFunctionMutation.mutate,
    isGeneratingFromDiff: generateFromDiffMutation.isLoading,
    isGeneratingFromFunction: generateFromFunctionMutation.isLoading,
    isGenerating: generateFromDiffMutation.isLoading || generateFromFunctionMutation.isLoading,
  }
}

export default useAIGeneration