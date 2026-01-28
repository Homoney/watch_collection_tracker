import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { imagesApi } from '@/lib/api'
import type { WatchImageUpdate } from '@/types'

export function useWatchImages(watchId: string | undefined) {
  return useQuery({
    queryKey: ['watches', watchId, 'images'],
    queryFn: () => imagesApi.list(watchId!),
    enabled: !!watchId,
  })
}

export function useUploadImage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ watchId, file }: { watchId: string; file: File }) =>
      imagesApi.upload(watchId, file),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'images']
      })
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId]
      })
      queryClient.invalidateQueries({ queryKey: ['watches'] })
    },
  })
}

export function useUpdateImage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      watchId,
      imageId,
      data
    }: {
      watchId: string
      imageId: string
      data: WatchImageUpdate
    }) => imagesApi.update(watchId, imageId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'images']
      })
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId]
      })
      queryClient.invalidateQueries({ queryKey: ['watches'] })
    },
  })
}

export function useDeleteImage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ watchId, imageId }: { watchId: string; imageId: string }) =>
      imagesApi.delete(watchId, imageId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId, 'images']
      })
      queryClient.invalidateQueries({
        queryKey: ['watches', variables.watchId]
      })
      queryClient.invalidateQueries({ queryKey: ['watches'] })
    },
  })
}
