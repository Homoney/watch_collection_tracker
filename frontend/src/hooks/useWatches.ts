import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { watchesApi } from '@/lib/api'
import type { WatchCreate, WatchUpdate, WatchFilters } from '@/types'

export function useWatches(filters?: WatchFilters, limit = 20, offset = 0) {
  return useQuery({
    queryKey: ['watches', filters, limit, offset],
    queryFn: () => watchesApi.list(filters, limit, offset),
  })
}

export function useWatch(id: string | undefined) {
  return useQuery({
    queryKey: ['watches', id],
    queryFn: () => watchesApi.get(id!),
    enabled: !!id,
  })
}

export function useCreateWatch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: WatchCreate) => watchesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watches'] })
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}

export function useUpdateWatch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WatchUpdate }) =>
      watchesApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['watches'] })
      queryClient.invalidateQueries({ queryKey: ['watches', variables.id] })
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}

export function useDeleteWatch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => watchesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watches'] })
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}
