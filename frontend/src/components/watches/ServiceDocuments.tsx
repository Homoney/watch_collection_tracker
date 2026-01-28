import { useState, useRef } from 'react'
import { FileText, Download, Trash2, Upload, File, Image as ImageIcon } from 'lucide-react'
import { ServiceDocument } from '@/types'
import {
  useUploadServiceDocument,
  useDeleteServiceDocument,
} from '@/hooks/useServiceHistory'

interface ServiceDocumentsProps {
  watchId: string
  serviceId: string
  documents: ServiceDocument[]
}

export default function ServiceDocuments({
  watchId,
  serviceId,
  documents,
}: ServiceDocumentsProps) {
  const uploadMutation = useUploadServiceDocument()
  const deleteMutation = useDeleteServiceDocument()
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getFileIcon = (mimeType: string) => {
    if (mimeType === 'application/pdf') {
      return <FileText className="h-8 w-8 text-red-500" />
    }
    if (mimeType.startsWith('image/')) {
      return <ImageIcon className="h-8 w-8 text-blue-500" />
    }
    return <File className="h-8 w-8 text-gray-500" />
  }

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png']
    if (!allowedTypes.includes(file.type)) {
      alert('Only PDF, JPG, and PNG files are allowed')
      return
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB')
      return
    }

    try {
      await uploadMutation.mutateAsync({
        watchId,
        serviceId,
        file,
      })
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      console.error('Failed to upload document:', error)
      alert('Failed to upload document. Please try again.')
    }
  }

  const handleDelete = async (docId: string) => {
    try {
      await deleteMutation.mutateAsync({
        watchId,
        serviceId,
        docId,
      })
      setDeleteConfirmId(null)
    } catch (error) {
      console.error('Failed to delete document:', error)
      alert('Failed to delete document. Please try again.')
    }
  }

  const handleDownload = (doc: ServiceDocument) => {
    const link = document.createElement('a')
    link.href = doc.url
    link.download = doc.file_name
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-gray-900">
          Documents ({documents.length})
        </h4>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploadMutation.isPending}
          className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 disabled:opacity-50"
        >
          <Upload className="h-4 w-4" />
          {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {documents.length === 0 ? (
        <div className="text-center py-6 bg-gray-50 rounded-lg border border-dashed border-gray-300">
          <File className="mx-auto h-8 w-8 text-gray-400" />
          <p className="mt-2 text-sm text-gray-500">No documents attached</p>
          <p className="text-xs text-gray-400 mt-1">
            Upload receipts, certificates, or warranties
          </p>
        </div>
      ) : (
        <div className="grid gap-3">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
            >
              {/* File Icon */}
              <div className="flex-shrink-0">{getFileIcon(doc.mime_type)}</div>

              {/* File Info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {doc.file_name}
                </p>
                <p className="text-xs text-gray-500">{formatFileSize(doc.file_size)}</p>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleDownload(doc)}
                  className="p-1.5 text-gray-400 hover:text-blue-600 rounded-md hover:bg-white"
                  title="Download"
                >
                  <Download className="h-4 w-4" />
                </button>

                {deleteConfirmId === doc.id ? (
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => handleDelete(doc.id)}
                      disabled={deleteMutation.isPending}
                      className="px-2 py-1 text-xs font-medium text-white bg-red-600 hover:bg-red-700 rounded"
                    >
                      Delete
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeleteConfirmId(null)}
                      className="px-2 py-1 text-xs font-medium text-gray-700 bg-white hover:bg-gray-100 rounded"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => setDeleteConfirmId(doc.id)}
                    className="p-1.5 text-gray-400 hover:text-red-600 rounded-md hover:bg-white"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Help Text */}
      <p className="text-xs text-gray-500">
        Accepted formats: PDF, JPG, PNG • Max size: 10MB
      </p>
    </div>
  )
}
