import { useQueries } from '@tanstack/react-query'
import { watchesApi } from '@/lib/api'

export function useCompareWatches(watchIds: string[]) {
  const queries = useQueries({
    queries: watchIds.map(id => ({
      queryKey: ['watches', id],
      queryFn: () => watchesApi.get(id),
      staleTime: 5 * 60 * 1000, // 5 minutes
    }))
  })

  return {
    watches: queries
      .filter(q => q.data)
      .map(q => q.data!),
    isLoading: queries.some(q => q.isLoading),
    errors: queries.filter(q => q.isError),
    hasErrors: queries.some(q => q.isError),
  }
}
