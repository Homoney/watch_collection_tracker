import { useQuery } from '@tanstack/react-query'
import { referenceApi } from '@/lib/api'

export function useBrands() {
  return useQuery({
    queryKey: ['brands'],
    queryFn: referenceApi.listBrands,
    staleTime: 1000 * 60 * 60, // 1 hour - reference data rarely changes
  })
}

export function useMovementTypes() {
  return useQuery({
    queryKey: ['movementTypes'],
    queryFn: referenceApi.listMovementTypes,
    staleTime: 1000 * 60 * 60, // 1 hour
  })
}

export function useComplications() {
  return useQuery({
    queryKey: ['complications'],
    queryFn: referenceApi.listComplications,
    staleTime: 1000 * 60 * 60, // 1 hour
  })
}
