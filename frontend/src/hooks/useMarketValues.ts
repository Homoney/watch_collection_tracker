import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { marketValuesApi } from '@/lib/api'
import type {
  MarketValueCreate,
  MarketValueUpdate,
} from '@/types'

export function useMarketValues(
  watchId: string | undefined,
  params?: { start_date?: string; end_date?: string; limit?: number }
) {
  return useQuery({
    queryKey: ['watches', watchId, 'market-values', params],
    queryFn: () => marketValuesApi.list(watchId!, params),
    enabled: !!watchId,
  })
}

export function useMarketValue(
  watchId: string | undefined,
  valueId: string | undefined
) {
  return useQuery({
    queryKey: ['watches', watchId, 'market-values', valueId],
    queryFn: () => marketValuesApi.get(watchId!, valueId!),
    enabled: !!watchId && !!valueId,
  })
}

export function useCreateMarketValue() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      watchId,
      data,
    }: {
      watchId: string
      data: MarketValueCreate
    }) => marketValuesApi.create(watchId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'market-values'],
      })
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'analytics'],
      })
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId],
      })
      queryClient.invalidateQueries({
        queryKey: ['collection-analytics'],
      })
    },
  })
}

export function useUpdateMarketValue() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      watchId,
      valueId,
      data,
    }: {
      watchId: string
      valueId: string
      data: MarketValueUpdate
    }) => marketValuesApi.update(watchId, valueId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'market-values'],
      })
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'analytics'],
      })
    },
  })
}

export function useDeleteMarketValue() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      watchId,
      valueId,
    }: {
      watchId: string
      valueId: string
    }) => marketValuesApi.delete(watchId, valueId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'market-values'],
      })
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'analytics'],
      })
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId],
      })
      queryClient.invalidateQueries({
        queryKey: ['collection-analytics'],
      })
    },
  })
}

export function useWatchAnalytics(watchId: string | undefined) {
  return useQuery({
    queryKey: ['watches', watchId, 'analytics'],
    queryFn: () => marketValuesApi.getWatchAnalytics(watchId!),
    enabled: !!watchId,
  })
}

export function useCollectionAnalytics(currency = 'USD') {
  return useQuery({
    queryKey: ['collection-analytics', currency],
    queryFn: () => marketValuesApi.getCollectionAnalytics(currency),
  })
}
