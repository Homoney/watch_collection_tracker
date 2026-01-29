import { useEffect, useState } from 'react'
import { useAtomicTime } from '@/hooks/useMovementAccuracy'
import { Clock, AlertTriangle } from 'lucide-react'

interface AtomicClockProps {
  onSecondMarkSelect: (seconds: 0 | 15 | 30 | 45) => void
  selectedMark?: 0 | 15 | 30 | 45 | null
  timezone?: string
}

export function AtomicClock({ onSecondMarkSelect, selectedMark = null, timezone = 'UTC' }: AtomicClockProps) {
  const { data: atomicTime, isLoading } = useAtomicTime(timezone)
  const [currentTime, setCurrentTime] = useState<Date | null>(null)

  // Update local time based on atomic time response
  useEffect(() => {
    if (atomicTime) {
      setCurrentTime(new Date(atomicTime.current_time))
    }
  }, [atomicTime])

  // Local time progression (updates every 100ms for smooth second hand)
  useEffect(() => {
    if (!currentTime) return

    const interval = setInterval(() => {
      setCurrentTime(prevTime => {
        if (!prevTime) return null
        return new Date(prevTime.getTime() + 100)
      })
    }, 100)

    return () => clearInterval(interval)
  }, [currentTime])

  if (isLoading || !currentTime) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const seconds = currentTime.getSeconds()
  const milliseconds = currentTime.getMilliseconds()
  const minutes = currentTime.getMinutes()
  const hours = currentTime.getHours()

  // Calculate rotation angles
  const secondAngle = (seconds + milliseconds / 1000) * 6 // 360/60 = 6 degrees per second
  const minuteAngle = (minutes + seconds / 60) * 6
  const hourAngle = ((hours % 12) + minutes / 60) * 30 // 360/12 = 30 degrees per hour

  const marks: Array<0 | 15 | 30 | 45> = [0, 15, 30, 45]

  return (
    <div className="space-y-6">
      {/* Warning if not atomic source */}
      {atomicTime && !atomicTime.is_atomic_source && (
        <div className="flex items-center gap-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
          <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0" />
          <p className="text-sm text-yellow-800 dark:text-yellow-200">
            Atomic time source unavailable. Using server time as fallback.
          </p>
        </div>
      )}

      {/* Analog Clock */}
      <div className="flex justify-center">
        <div className="relative w-64 h-64">
          {/* Clock face */}
          <div className="absolute inset-0 rounded-full border-4 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 shadow-lg">
            {/* Hour markers */}
            {[...Array(12)].map((_, i) => {
              const angle = i * 30
              const isQuarter = i % 3 === 0
              return (
                <div
                  key={i}
                  className="absolute top-1/2 left-1/2 origin-top-left"
                  style={{
                    transform: `rotate(${angle}deg) translate(110px, -50%)`,
                  }}
                >
                  <div
                    className={`${
                      isQuarter
                        ? 'w-1 h-4 bg-gray-800 dark:bg-gray-200'
                        : 'w-0.5 h-2 bg-gray-400 dark:bg-gray-500'
                    }`}
                  />
                </div>
              )
            })}

            {/* Second marks (0, 15, 30, 45) */}
            {marks.map(mark => {
              const angle = mark * 6
              const isSelected = selectedMark === mark
              return (
                <div
                  key={mark}
                  className="absolute top-1/2 left-1/2 origin-top-left"
                  style={{
                    transform: `rotate(${angle}deg) translate(95px, -50%)`,
                  }}
                >
                  <div
                    className={`w-3 h-3 rounded-full ${
                      isSelected
                        ? 'bg-blue-600 dark:bg-blue-400 ring-2 ring-blue-300 dark:ring-blue-600'
                        : 'bg-blue-400 dark:bg-blue-500'
                    }`}
                  />
                </div>
              )
            })}

            {/* Hour hand */}
            <div
              className="absolute top-1/2 left-1/2 origin-bottom bg-gray-800 dark:bg-gray-200 rounded-full shadow-md"
              style={{
                width: '6px',
                height: '50px',
                transform: `translate(-50%, -100%) rotate(${hourAngle}deg)`,
                transition: 'transform 0.3s ease-out',
              }}
            />

            {/* Minute hand */}
            <div
              className="absolute top-1/2 left-1/2 origin-bottom bg-gray-700 dark:bg-gray-300 rounded-full shadow-md"
              style={{
                width: '4px',
                height: '70px',
                transform: `translate(-50%, -100%) rotate(${minuteAngle}deg)`,
                transition: 'transform 0.3s ease-out',
              }}
            />

            {/* Second hand */}
            <div
              className="absolute top-1/2 left-1/2 origin-bottom bg-red-500 rounded-full shadow-md"
              style={{
                width: '2px',
                height: '85px',
                transform: `translate(-50%, -100%) rotate(${secondAngle}deg)`,
              }}
            />

            {/* Center dot */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-gray-800 dark:bg-gray-200 shadow-md" />
          </div>
        </div>
      </div>

      {/* Digital time display */}
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <Clock className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          <span className="text-2xl font-mono font-semibold text-gray-900 dark:text-white">
            {currentTime.toLocaleTimeString('en-US', {
              hour12: false,
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            })}
          </span>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
          {currentTime.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </p>
      </div>

      {/* Second mark buttons */}
      <div className="space-y-3">
        <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
          Click when your watch's second hand aligns with one of these marks:
        </p>
        <div className="grid grid-cols-4 gap-3">
          {marks.map(mark => (
            <button
              key={mark}
              type="button"
              onClick={() => onSecondMarkSelect(mark)}
              className={`py-3 px-4 rounded-lg font-semibold transition-all ${
                selectedMark === mark
                  ? 'bg-blue-600 text-white shadow-lg scale-105'
                  : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border-2 border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500 hover:scale-105'
              }`}
            >
              :{mark.toString().padStart(2, '0')}
            </button>
          ))}
        </div>
        {selectedMark !== null && (
          <p className="text-sm text-center text-blue-600 dark:text-blue-400 font-medium">
            Selected: {selectedMark} seconds past the minute
          </p>
        )}
      </div>
    </div>
  )
}
