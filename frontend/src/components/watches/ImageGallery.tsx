import { useState } from 'react'
import { useUpdateImage, useDeleteImage } from '@/hooks/useWatchImages'
import { Star, Trash2, Image as ImageIcon } from 'lucide-react'
import type { WatchImage } from '@/types'

interface ImageGalleryProps {
  watchId: string
  images: WatchImage[]
  onImageClick: (index: number) => void
}

export default function ImageGallery({ watchId, images, onImageClick }: ImageGalleryProps) {
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)
  const updateMutation = useUpdateImage()
  const deleteMutation = useDeleteImage()

  const handleSetPrimary = async (imageId: string) => {
    try {
      await updateMutation.mutateAsync({
        watchId,
        imageId,
        data: { is_primary: true },
      })
    } catch (error) {
      console.error('Failed to set primary image:', error)
    }
  }

  const handleDelete = async (imageId: string) => {
    try {
      await deleteMutation.mutateAsync({ watchId, imageId })
      setDeleteConfirm(null)
    } catch (error) {
      console.error('Failed to delete image:', error)
    }
  }

  if (images.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <ImageIcon className="w-16 h-16 mx-auto mb-4 text-gray-400" />
        <p className="text-gray-600 font-medium mb-1">No images yet</p>
        <p className="text-sm text-gray-500">
          Upload images to showcase this watch
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
      {images.map((image, index) => (
        <div key={image.id} className="relative group">
          {/* Image */}
          <div
            onClick={() => onImageClick(index)}
            className="
              relative w-full h-48 bg-gray-100 rounded-lg overflow-hidden
              cursor-pointer transition-transform hover:scale-105
            "
          >
            <img
              src={image.url}
              alt={`Watch image ${index + 1}`}
              className="w-full h-full object-cover"
            />

            {/* Primary Badge */}
            {image.is_primary && (
              <div className="absolute top-2 left-2 px-2 py-1 bg-yellow-500 text-white text-xs font-medium rounded">
                Primary
              </div>
            )}

            {/* Hover Overlay */}
            <div className="
              absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30
              transition-all duration-200
            " />
          </div>

          {/* Action Buttons */}
          <div className="
            absolute bottom-2 left-2 right-2 flex gap-2
            opacity-0 group-hover:opacity-100 transition-opacity
          ">
            {/* Set Primary Button */}
            {!image.is_primary && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleSetPrimary(image.id)
                }}
                disabled={updateMutation.isPending}
                className="
                  flex-1 px-2 py-1 bg-yellow-500 text-white text-xs rounded
                  hover:bg-yellow-600 disabled:bg-gray-400
                  transition-colors flex items-center justify-center gap-1
                "
                title="Set as primary"
              >
                <Star className="w-3 h-3" />
                <span className="hidden sm:inline">Primary</span>
              </button>
            )}

            {/* Delete Button */}
            {deleteConfirm === image.id ? (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleDelete(image.id)
                }}
                disabled={deleteMutation.isPending}
                className="
                  flex-1 px-2 py-1 bg-red-600 text-white text-xs rounded
                  hover:bg-red-700 disabled:bg-gray-400
                  transition-colors
                "
              >
                Confirm?
              </button>
            ) : (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setDeleteConfirm(image.id)
                  // Auto-cancel after 3 seconds
                  setTimeout(() => setDeleteConfirm(null), 3000)
                }}
                className="
                  flex-1 px-2 py-1 bg-red-500 text-white text-xs rounded
                  hover:bg-red-600
                  transition-colors flex items-center justify-center gap-1
                "
                title="Delete image"
              >
                <Trash2 className="w-3 h-3" />
                <span className="hidden sm:inline">Delete</span>
              </button>
            )}
          </div>

          {/* File Info */}
          <div className="mt-2 text-xs text-gray-500 truncate">
            {image.file_name}
          </div>
        </div>
      ))}
    </div>
  )
}
