import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { serviceHistoryApi } from '@/lib/api'
import type {
  ServiceHistoryCreate,
  ServiceHistoryUpdate,
} from '@/types'

export function useServiceHistory(watchId: string | undefined) {
  return useQuery({
    queryKey: ['watches', watchId, 'service-history'],
    queryFn: () => serviceHistoryApi.list(watchId!),
    enabled: !!watchId,
  })
}

export function useServiceHistoryRecord(
  watchId: string | undefined,
  serviceId: string | undefined
) {
  return useQuery({
    queryKey: ['watches', watchId, 'service-history', serviceId],
    queryFn: () => serviceHistoryApi.get(watchId!, serviceId!),
    enabled: !!watchId && !!serviceId,
  })
}

export function useCreateServiceHistory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      watchId,
      data,
    }: {
      watchId: string
      data: ServiceHistoryCreate
    }) => serviceHistoryApi.create(watchId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'service-history'],
      })
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId],
      })
    },
  })
}

export function useUpdateServiceHistory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      watchId,
      serviceId,
      data,
    }: {
      watchId: string
      serviceId: string
      data: ServiceHistoryUpdate
    }) => serviceHistoryApi.update(watchId, serviceId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'service-history'],
      })
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'service-history', variables.serviceId],
      })
    },
  })
}

export function useDeleteServiceHistory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      watchId,
      serviceId,
    }: {
      watchId: string
      serviceId: string
    }) => serviceHistoryApi.delete(watchId, serviceId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'service-history'],
      })
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId],
      })
    },
  })
}

export function useUploadServiceDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      watchId,
      serviceId,
      file,
    }: {
      watchId: string
      serviceId: string
      file: File
    }) => serviceHistoryApi.uploadDocument(watchId, serviceId, file),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'service-history'],
      })
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'service-history', variables.serviceId],
      })
    },
  })
}

export function useDeleteServiceDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      watchId,
      serviceId,
      docId,
    }: {
      watchId: string
      serviceId: string
      docId: string
    }) => serviceHistoryApi.deleteDocument(watchId, serviceId, docId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'service-history'],
      })
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'service-history', variables.serviceId],
      })
    },
  })
}
