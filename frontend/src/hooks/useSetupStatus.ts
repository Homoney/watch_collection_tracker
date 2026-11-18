import { useQuery } from '@tanstack/react-query'
import { authApi } from '@/lib/api'

/** True while the database has no accounts (first sign-up creates the admin). */
export function useSetupRequired(): boolean {
  const { data } = useQuery({
    queryKey: ['setup-status'],
    queryFn: authApi.setupStatus,
    staleTime: 0,
    retry: false,
  })
  return data?.setup_required === true
}
