import { useQuery } from '@tanstack/react-query'
import { authApi } from '@/lib/api'

/**
 * True while no account exists and signing up creates the admin
 * (INITIAL_ADMIN_EMAIL is set). Otherwise the normal pages are shown.
 */
export function useAdminSignup(): boolean {
  const { data } = useQuery({
    queryKey: ['setup-status'],
    queryFn: authApi.setupStatus,
    staleTime: 0,
    retry: false,
  })
  return data?.admin_signup === true
}
