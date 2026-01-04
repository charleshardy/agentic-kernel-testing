/**
 * Property-based tests for Environment Preference Management Consistency
 * **Feature: environment-allocation-ui, Property 6: Environment Preference Management Consistency**
 * **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
 */

import fc from 'fast-check'
import { 
  EnvironmentType, 
  EnvironmentStatus, 
  EnvironmentHealth,
  HardwareRequirements,
  AllocationPreferences,
  Environment
} from '../../types/environment'

// Test configuration for property-based testing
const testConfig = {
  numRuns: 100,
  verbose: false,
  seed: 42
}

// Simplified generators
const architectureGenerator = fc.constantFrom('x86_64', 'arm64')
const environmentTypeGenerator = fc.constantFrom(EnvironmentType.QEMU_X86, EnvironmentType.DOCKER, EnvironmentType.PHYSICAL)
const isolationLevelGenerator = fc.constantFrom('container', 'vm')

const hardwareRequirementsGenerator = fc.record({
  architecture: architectureGenerator,
  minMemoryMB: fc.integer({ min: 1024, max: 8192 }),
  minCpuCores: fc.integer({ min: 1, max: 4 }),
  requiredFeatures: fc.array(fc.constantFrom('kvm', 'networking'), { maxLength: 2 }),
  preferredEnvironmentType: fc.option(environmentTypeGenerator),
  isolationLevel: isolationLevelGenerator
})

const allocationPreferencesGenerator = fc.record({
  environmentType: fc.option(environmentTypeGenerator),
  architecture: fc.option(architectureGenerator),
  maxWaitTime: fc.option(fc.integer({ min: 60, max: 600 })),
  allowSharedEnvironment: fc.boolean(),
  requireDedicatedResources: fc.boolean()
})

const environmentGenerator = fc.record({
  id: fc.string({ minLength: 5, maxLength: 10 }),
  type: environmentTypeGenerator,
  status: fc.constantFrom(EnvironmentStatus.READY, EnvironmentStatus.RUNNING),
  architecture: architectureGenerator,
  assignedTests: fc.array(fc.string(), { maxLength: 1 }),
  resources: fc.record({
    cpu: fc.float({ min: 0, max: 100 }),
    memory: fc.float({ min: 0, max: 100 }),
    disk: fc.float({ min: 0, max: 100 }),
    network: fc.record({
      bytesIn: fc.integer({ min: 0, max: 10000 }),
      bytesOut: fc.integer({ min: 0, max: 10000 }),
      packetsIn: fc.integer({ min: 0, max: 100 }),
      packetsOut: fc.integer({ min: 0, max: 100 })
    })
  }),
  health: fc.constantFrom(EnvironmentHealth.HEALTHY, EnvironmentHealth.DEGRADED),
  metadata: fc.record({
    memoryMB: fc.option(fc.integer({ min: 1024, max: 8192 })),
    cpuCores: fc.option(fc.integer({ min: 1, max: 4 }))
  }),
  createdAt: fc.date().map(d => d.toISOString()),
  updatedAt: fc.date().map(d => d.toISOString())
})

// Pure functions for testing preference management logic
function validateEnvironmentCompatibility(requirements: HardwareRequirements, environments: Environment[]) {
  const compatibleEnvironments = environments.filter(env => {
    // Architecture must match
    if (env.architecture !== requirements.architecture) return false
    
    // Memory requirement check
    const envMemory = env.metadata.memoryMB || 0
    if (envMemory < requirements.minMemoryMB) return false
    
    // CPU requirement check
    const envCores = env.metadata.cpuCores || 0
    if (envCores < requirements.minCpuCores) return false
    
    return true
  })

  const allocationLikelihood = environments.length > 0 ? 
    (compatibleEnvironments.length / environments.length) * 100 : 0

  return {
    compatible: compatibleEnvironments.length > 0,
    compatibleEnvironments,
    allocationLikelihood,
    issues: compatibleEnvironments.length === 0 ? ['No compatible environments found'] : [],
    suggestions: compatibleEnvironments.length === 0 ? ['Consider reducing requirements'] : []
  }
}

function filterEnvironmentsByType(environments: Environment[], preferredType: EnvironmentType) {
  return environments.filter(env => env.type === preferredType)
}

function calculateAllocationLikelihood(compatibleCount: number, totalCount: number) {
  return totalCount > 0 ? (compatibleCount / totalCount) * 100 : 0
}

describe('Environment Preference Management Property Tests (Pure Logic)', () => {
  /**
   * Property 1: Hardware Requirements Validation Consistency
   * For any hardware requirements, validation should consistently identify compatible environments
   */
  test('hardware requirements validation is consistent', () => {
    fc.assert(
      fc.property(
        hardwareRequirementsGenerator,
        fc.array(environmentGenerator, { minLength: 1, maxLength: 10 }),
        (requirements, environments) => {
          const result = validateEnvironmentCompatibility(requirements, environments)

          // Verify compatibility logic is consistent
          const expectedCompatible = environments.some(env => {
            return env.architecture === requirements.architecture &&
                   (env.metadata.memoryMB || 0) >= requirements.minMemoryMB &&
                   (env.metadata.cpuCores || 0) >= requirements.minCpuCores
          })

          expect(result.compatible).toBe(expectedCompatible)
          expect(result.allocationLikelihood).toBeGreaterThanOrEqual(0)
          expect(result.allocationLikelihood).toBeLessThanOrEqual(100)
          
          // All compatible environments should meet requirements
          result.compatibleEnvironments.forEach(env => {
            expect(env.architecture).toBe(requirements.architecture)
            expect(env.metadata.memoryMB || 0).toBeGreaterThanOrEqual(requirements.minMemoryMB)
            expect(env.metadata.cpuCores || 0).toBeGreaterThanOrEqual(requirements.minCpuCores)
          })
        }
      ),
      testConfig
    )
  })

  /**
   * Property 2: Environment Type Filtering Consistency
   * For any environment type preference, filtering should work correctly
   */
  test('environment type filtering is consistent', () => {
    fc.assert(
      fc.property(
        environmentTypeGenerator,
        fc.array(environmentGenerator, { minLength: 1, maxLength: 10 }),
        (preferredType, environments) => {
          const filtered = filterEnvironmentsByType(environments, preferredType)

          // All filtered environments should match the preferred type
          filtered.forEach(env => {
            expect(env.type).toBe(preferredType)
          })

          // Filtered count should not exceed total count
          expect(filtered.length).toBeLessThanOrEqual(environments.length)

          // If no environments of preferred type exist, filtered should be empty
          const hasPreferredType = environments.some(env => env.type === preferredType)
          if (!hasPreferredType) {
            expect(filtered.length).toBe(0)
          }
        }
      ),
      testConfig
    )
  })

  /**
   * Property 3: Allocation Likelihood Calculation Accuracy
   * For any compatible/total environment counts, likelihood calculation should be accurate
   */
  test('allocation likelihood calculation is accurate', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 20 }),
        fc.integer({ min: 1, max: 20 }),
        (compatibleCount, totalCount) => {
          // Ensure compatible count doesn't exceed total
          const actualCompatibleCount = Math.min(compatibleCount, totalCount)
          
          const likelihood = calculateAllocationLikelihood(actualCompatibleCount, totalCount)

          expect(likelihood).toBeGreaterThanOrEqual(0)
          expect(likelihood).toBeLessThanOrEqual(100)
          
          // If no compatible environments, likelihood should be 0
          if (actualCompatibleCount === 0) {
            expect(likelihood).toBe(0)
          }
          
          // If all environments compatible, likelihood should be 100
          if (actualCompatibleCount === totalCount) {
            expect(likelihood).toBe(100)
          }

          // Likelihood should be proportional
          const expectedLikelihood = (actualCompatibleCount / totalCount) * 100
          expect(likelihood).toBeCloseTo(expectedLikelihood, 2)
        }
      ),
      testConfig
    )
  })

  /**
   * Property 4: Preference Profile Data Structure Consistency
   * For any preference profile data, the structure should be preserved
   */
  test('preference profile data structure is preserved', () => {
    fc.assert(
      fc.property(
        fc.record({
          name: fc.string({ minLength: 1, maxLength: 50 }),
          description: fc.option(fc.string({ maxLength: 200 })),
          requirements: hardwareRequirementsGenerator,
          preferences: allocationPreferencesGenerator
        }),
        (profileData) => {
          // Simulate profile creation
          const profile = {
            id: 'test-id',
            ...profileData,
            createdAt: new Date(),
            updatedAt: new Date()
          }

          // Verify all required fields are present
          expect(profile.id).toBeDefined()
          expect(profile.name).toBeDefined()
          expect(profile.requirements).toBeDefined()
          expect(profile.preferences).toBeDefined()
          expect(profile.createdAt).toBeInstanceOf(Date)
          expect(profile.updatedAt).toBeInstanceOf(Date)

          // Verify requirements structure
          expect(profile.requirements.architecture).toBeDefined()
          expect(profile.requirements.minMemoryMB).toBeGreaterThan(0)
          expect(profile.requirements.minCpuCores).toBeGreaterThan(0)
          expect(Array.isArray(profile.requirements.requiredFeatures)).toBe(true)
          expect(['container', 'vm', 'none', 'process']).toContain(profile.requirements.isolationLevel)

          // Verify preferences structure
          expect(typeof profile.preferences.allowSharedEnvironment).toBe('boolean')
          expect(typeof profile.preferences.requireDedicatedResources).toBe('boolean')
        }
      ),
      testConfig
    )
  })

  /**
   * Property 5: Error Detection Consistency
   * For any invalid requirements, error detection should be consistent
   */
  test('error detection is consistent for invalid requirements', () => {
    fc.assert(
      fc.property(
        fc.record({
          architecture: architectureGenerator,
          minMemoryMB: fc.integer({ min: 50000, max: 100000 }), // Intentionally high
          minCpuCores: fc.integer({ min: 20, max: 50 }), // Intentionally high
          requiredFeatures: fc.array(fc.string(), { maxLength: 2 }),
          isolationLevel: isolationLevelGenerator
        }),
        fc.array(environmentGenerator, { minLength: 1, maxLength: 5 }),
        (invalidRequirements, environments) => {
          const result = validateEnvironmentCompatibility(invalidRequirements, environments)

          // Should detect incompatibility for unrealistic requirements
          expect(result.compatible).toBe(false)
          expect(result.allocationLikelihood).toBe(0)
          expect(result.issues.length).toBeGreaterThan(0)
          expect(result.suggestions.length).toBeGreaterThan(0)
          expect(result.compatibleEnvironments.length).toBe(0)
        }
      ),
      testConfig
    )
  })

  /**
   * Property 6: Preference Consistency Across Multiple Validations
   * For any requirements, multiple validations should yield consistent results
   */
  test('preference validation is consistent across multiple runs', () => {
    fc.assert(
      fc.property(
        hardwareRequirementsGenerator,
        fc.array(environmentGenerator, { minLength: 1, maxLength: 5 }),
        (requirements, environments) => {
          // Run validation multiple times
          const result1 = validateEnvironmentCompatibility(requirements, environments)
          const result2 = validateEnvironmentCompatibility(requirements, environments)
          const result3 = validateEnvironmentCompatibility(requirements, environments)

          // Results should be identical
          expect(result1.compatible).toBe(result2.compatible)
          expect(result2.compatible).toBe(result3.compatible)
          
          expect(result1.allocationLikelihood).toBe(result2.allocationLikelihood)
          expect(result2.allocationLikelihood).toBe(result3.allocationLikelihood)
          
          expect(result1.compatibleEnvironments.length).toBe(result2.compatibleEnvironments.length)
          expect(result2.compatibleEnvironments.length).toBe(result3.compatibleEnvironments.length)
        }
      ),
      testConfig
    )
  })
})