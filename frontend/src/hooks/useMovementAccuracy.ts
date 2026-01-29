import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { movementAccuracyApi } from '@/lib/api'
import type {
  MovementAccuracyReadingCreate,
  MovementAccuracyReadingUpdate,
  MovementAccuracyReading,
  MovementAccuracyReadingWithDrift,
  AccuracyAnalytics,
  AtomicTimeResponse,
} from '@/types'

// Query keys
const QUERY_KEYS = {
  atomicTime: (timezone: string) => ['atomic-time', timezone] as const,
  readings: (watchId: string) => ['watches', watchId, 'accuracy-readings'] as const,
  reading: (watchId: string, readingId: string) => ['watches', watchId, 'accuracy-readings', readingId] as const,
  analytics: (watchId: string) => ['watches', watchId, 'accuracy-analytics'] as const,
}

// Atomic Time Hook (public, refreshes every 1 second)
export function useAtomicTime(timezone: string = 'UTC', enabled: boolean = true) {
  return useQuery<AtomicTimeResponse>({
    queryKey: QUERY_KEYS.atomicTime(timezone),
    queryFn: () => movementAccuracyApi.getAtomicTime(timezone),
    refetchInterval: 1000, // Refresh every 1 second
    enabled,
    staleTime: 0, // Always consider stale
    gcTime: 60000, // Keep in cache for 1 minute
  })
}

// List Accuracy Readings
export function useAccuracyReadings(watchId: string) {
  return useQuery<MovementAccuracyReadingWithDrift[]>({
    queryKey: QUERY_KEYS.readings(watchId),
    queryFn: () => movementAccuracyApi.list(watchId),
    staleTime: 30000, // 30 seconds
  })
}

// Get Single Accuracy Reading
export function useAccuracyReading(watchId: string, readingId: string) {
  return useQuery<MovementAccuracyReadingWithDrift>({
    queryKey: QUERY_KEYS.reading(watchId, readingId),
    queryFn: () => movementAccuracyApi.get(watchId, readingId),
    staleTime: 30000,
  })
}

// Get Accuracy Analytics
export function useAccuracyAnalytics(watchId: string) {
  return useQuery<AccuracyAnalytics>({
    queryKey: QUERY_KEYS.analytics(watchId),
    queryFn: () => movementAccuracyApi.getAnalytics(watchId),
    staleTime: 30000,
  })
}

// Create Accuracy Reading
export function useCreateAccuracyReading() {
  const queryClient = useQueryClient()

  return useMutation<MovementAccuracyReading, Error, { watchId: string; data: MovementAccuracyReadingCreate }>({
    mutationFn: ({ watchId, data }) => movementAccuracyApi.create(watchId, data),
    onSuccess: (_, variables) => {
      // Invalidate readings and analytics for this watch
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.readings(variables.watchId) })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.analytics(variables.watchId) })
      // Also invalidate watch detail in case we display accuracy info there
      queryClient.invalidateQueries({ queryKey: ['watches', variables.watchId] })
    },
  })
}

// Update Accuracy Reading
export function useUpdateAccuracyReading() {
  const queryClient = useQueryClient()

  return useMutation<
    MovementAccuracyReading,
    Error,
    { watchId: string; readingId: string; data: MovementAccuracyReadingUpdate }
  >({
    mutationFn: ({ watchId, readingId, data }) => movementAccuracyApi.update(watchId, readingId, data),
    onSuccess: (_, variables) => {
      // Invalidate specific reading, all readings, and analytics
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.reading(variables.watchId, variables.readingId) })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.readings(variables.watchId) })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.analytics(variables.watchId) })
    },
  })
}

// Delete Accuracy Reading
export function useDeleteAccuracyReading() {
  const queryClient = useQueryClient()

  return useMutation<void, Error, { watchId: string; readingId: string }>({
    mutationFn: ({ watchId, readingId }) => movementAccuracyApi.delete(watchId, readingId),
    onSuccess: (_, variables) => {
      // Invalidate readings and analytics
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.readings(variables.watchId) })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.analytics(variables.watchId) })
      queryClient.invalidateQueries({ queryKey: ['watches', variables.watchId] })
    },
  })
}
