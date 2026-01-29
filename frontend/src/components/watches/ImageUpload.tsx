import { useState, useRef, DragEvent, ChangeEvent } from 'react'
import { useUploadImage } from '@/hooks/useWatchImages'
import { Upload, X, AlertCircle } from 'lucide-react'

interface ImageUploadProps {
  watchId: string
  onUploadComplete?: () => void
}

const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']

function validateFile(file: File): { valid: boolean; error?: string } {
  if (!ALLOWED_TYPES.includes(file.type)) {
    return { valid: false, error: 'Only JPG, PNG, GIF, and WebP images are allowed' }
  }
  if (file.size > MAX_FILE_SIZE) {
    return { valid: false, error: 'File size must be less than 20MB' }
  }
  return { valid: true }
}

export default function ImageUpload({ watchId, onUploadComplete }: ImageUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [previews, setPreviews] = useState<Array<{ file: File; url: string }>>([])
  const [errors, setErrors] = useState<string[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  const uploadMutation = useUploadImage()

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    handleFiles(files)
  }

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files)
      handleFiles(files)
    }
  }

  const handleFiles = (files: File[]) => {
    const newErrors: string[] = []
    const newPreviews: Array<{ file: File; url: string }> = []

    files.forEach((file) => {
      const validation = validateFile(file)
      if (validation.valid) {
        newPreviews.push({
          file,
          url: URL.createObjectURL(file),
        })
      } else {
        newErrors.push(`${file.name}: ${validation.error}`)
      }
    })

    setErrors(newErrors)
    setPreviews((prev) => [...prev, ...newPreviews])
  }

  const removePreview = (index: number) => {
    setPreviews((prev) => {
      URL.revokeObjectURL(prev[index].url)
      return prev.filter((_, i) => i !== index)
    })
  }

  const handleUpload = async () => {
    setErrors([])
    const uploadErrors: string[] = []

    for (const preview of previews) {
      try {
        await uploadMutation.mutateAsync({
          watchId,
          file: preview.file,
        })
      } catch (error: unknown) {
        const err = error as { response?: { data?: { detail?: string } } }
        const message = err.response?.data?.detail || 'Upload failed'
        uploadErrors.push(`${preview.file.name}: ${message}`)
      }
    }

    if (uploadErrors.length === 0) {
      // Clear previews on success
      previews.forEach((preview) => URL.revokeObjectURL(preview.url))
      setPreviews([])
      onUploadComplete?.()
    } else {
      setErrors(uploadErrors)
    }
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onClick={handleClick}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-colors
          ${isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
          }
        `}
      >
        <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <p className="text-sm text-gray-600 mb-2">
          Drag and drop images here, or click to select files
        </p>
        <p className="text-xs text-gray-500">
          JPG, PNG, GIF, WebP - Max 20MB per file
        </p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/jpeg,image/png,image/gif,image/webp"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {/* Error Messages */}
      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800 mb-1">
                Upload Errors
              </p>
              <ul className="text-sm text-red-700 space-y-1">
                {errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Preview Grid */}
      {previews.length > 0 && (
        <div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-4">
            {previews.map((preview, index) => (
              <div key={index} className="relative group">
                <img
                  src={preview.url}
                  alt={preview.file.name}
                  className="w-full h-32 object-cover rounded-lg border border-gray-200"
                />
                <button
                  onClick={() => removePreview(index)}
                  className="
                    absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full
                    opacity-0 group-hover:opacity-100 transition-opacity
                  "
                >
                  <X className="w-4 h-4" />
                </button>
                <p className="text-xs text-gray-600 mt-1 truncate">
                  {preview.file.name}
                </p>
              </div>
            ))}
          </div>

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={uploadMutation.isPending}
            className="
              w-full px-4 py-2 bg-blue-600 text-white rounded-lg
              hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed
              transition-colors
            "
          >
            {uploadMutation.isPending
              ? 'Uploading...'
              : `Upload ${previews.length} ${previews.length === 1 ? 'Image' : 'Images'}`
            }
          </button>
        </div>
      )}
    </div>
  )
}
