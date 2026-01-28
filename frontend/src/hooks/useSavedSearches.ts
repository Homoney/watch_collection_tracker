import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { savedSearchesApi } from '@/lib/api'
import type { SavedSearchCreate, SavedSearchUpdate } from '@/types'

export function useSavedSearches() {
  return useQuery({
    queryKey: ['saved-searches'],
    queryFn: () => savedSearchesApi.list(),
  })
}

export function useCreateSavedSearch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: SavedSearchCreate) => savedSearchesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] })
    },
  })
}

export function useUpdateSavedSearch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ searchId, data }: { searchId: string; data: SavedSearchUpdate }) =>
      savedSearchesApi.update(searchId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] })
    },
  })
}

export function useDeleteSavedSearch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (searchId: string) => savedSearchesApi.delete(searchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] })
    },
  })
}
