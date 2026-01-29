import { useState, useEffect } from 'react'
import { QrCode, Download, Printer } from 'lucide-react'
import Button from '@/components/common/Button'
import { api } from '@/lib/api'

interface WatchQRCodeProps {
  watchId: string
}

export default function WatchQRCode({ watchId }: WatchQRCodeProps) {
  const [showQR, setShowQR] = useState(false)
  const [qrCodeBlobUrl, setQrCodeBlobUrl] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const baseUrl = window.location.origin

  // Fetch QR code image with auth token when showQR becomes true
  useEffect(() => {
    if (showQR && !qrCodeBlobUrl) {
      fetchQRCode()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showQR, watchId])

  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      if (qrCodeBlobUrl) {
        URL.revokeObjectURL(qrCodeBlobUrl)
      }
    }
  }, [qrCodeBlobUrl])

  const fetchQRCode = async () => {
    setIsLoading(true)
    try {
      const response = await api.get(
        `/v1/watches/${watchId}/qr-code?base_url=${encodeURIComponent(baseUrl)}`,
        { responseType: 'blob' }
      )
      const blobUrl = URL.createObjectURL(response.data)
      setQrCodeBlobUrl(blobUrl)
    } catch (error) {
      console.error('Failed to fetch QR code:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = () => {
    if (!qrCodeBlobUrl) return
    const link = document.createElement('a')
    link.href = qrCodeBlobUrl
    link.download = `watch-${watchId}-qr.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handlePrint = () => {
    if (!qrCodeBlobUrl) return
    const printWindow = window.open(qrCodeBlobUrl, '_blank')
    if (printWindow) {
      printWindow.onload = () => {
        printWindow.print()
      }
    }
  }

  if (!showQR) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <QrCode className="h-5 w-5" />
              QR Code
            </h3>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Generate a QR code for this watch to print labels or quick access
            </p>
          </div>
          <Button onClick={() => setShowQR(true)}>
            Generate QR Code
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <QrCode className="h-5 w-5" />
          QR Code
        </h3>
        <Button variant="ghost" size="sm" onClick={() => setShowQR(false)}>
          Hide
        </Button>
      </div>

      <div className="space-y-4">
        <div className="flex justify-center p-4 bg-white rounded-lg border border-gray-200">
          {isLoading ? (
            <div className="w-64 h-64 flex items-center justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : qrCodeBlobUrl ? (
            <img
              src={qrCodeBlobUrl}
              alt="Watch QR Code"
              className="w-64 h-64"
            />
          ) : (
            <div className="w-64 h-64 flex items-center justify-center text-gray-400">
              Failed to load QR code
            </div>
          )}
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
          Scan this QR code to view watch details on any device
        </p>

        <div className="flex gap-3 justify-center">
          <Button onClick={handleDownload} variant="secondary" disabled={!qrCodeBlobUrl || isLoading}>
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
          <Button onClick={handlePrint} variant="secondary" disabled={!qrCodeBlobUrl || isLoading}>
            <Printer className="h-4 w-4 mr-2" />
            Print
          </Button>
        </div>
      </div>
    </div>
  )
}
