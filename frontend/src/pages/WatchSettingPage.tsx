import { useState, useEffect } from 'react'
import { Clock, Calendar, Moon, RotateCcw } from 'lucide-react'
import { format } from 'date-fns'
import AppLayout from '@/components/layout/AppLayout'

// Helper function to calculate leap year cycle position
function getLeapYearCycle(year: number): { position: number; isLeapYear: boolean } {
  const isLeapYear = (y: number) => (y % 4 === 0 && y % 100 !== 0) || (y % 400 === 0)

  if (isLeapYear(year)) return { position: 4, isLeapYear: true }
  if (isLeapYear(year + 1)) return { position: 3, isLeapYear: false }
  if (isLeapYear(year + 2)) return { position: 2, isLeapYear: false }
  return { position: 1, isLeapYear: false }
}

// Helper function to calculate moon phase
function getMoonPhase(date: Date): { phase: string; percentage: number; emoji: string } {
  // Known new moon: January 6, 2000 at 18:14 UTC
  const referenceNewMoon = new Date('2000-01-06T18:14:00Z').getTime()
  const currentTime = date.getTime()
  const daysSinceReference = (currentTime - referenceNewMoon) / (1000 * 60 * 60 * 24)
  const lunarCycle = 29.53058867 // average lunar cycle in days
  const phase = (daysSinceReference % lunarCycle) / lunarCycle

  // Classify into 8 phases
  if (phase < 0.0625 || phase >= 0.9375) {
    return { phase: 'New Moon', percentage: 0, emoji: '🌑' }
  }
  if (phase < 0.1875) {
    return { phase: 'Waxing Crescent', percentage: Math.round(phase * 100), emoji: '🌒' }
  }
  if (phase < 0.3125) {
    return { phase: 'First Quarter', percentage: 50, emoji: '🌓' }
  }
  if (phase < 0.4375) {
    return { phase: 'Waxing Gibbous', percentage: Math.round(phase * 100), emoji: '🌔' }
  }
  if (phase < 0.5625) {
    return { phase: 'Full Moon', percentage: 100, emoji: '🌕' }
  }
  if (phase < 0.6875) {
    return { phase: 'Waning Gibbous', percentage: Math.round((1 - phase) * 100), emoji: '🌖' }
  }
  if (phase < 0.8125) {
    return { phase: 'Last Quarter', percentage: 50, emoji: '🌗' }
  }
  return { phase: 'Waning Crescent', percentage: Math.round((1 - phase) * 100), emoji: '🌘' }
}

export default function WatchSettingPage() {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [is24Hour, setIs24Hour] = useState(true)

  // Update time every second
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  // Calculate all time-based values
  const timeFormat = is24Hour ? 'HH:mm:ss' : 'h:mm:ss a'
  const timeString = format(currentTime, timeFormat)
  const dateString = format(currentTime, 'MMMM d, yyyy')
  const dayName = format(currentTime, 'EEEE')
  const year = currentTime.getFullYear()
  const leapYearInfo = getLeapYearCycle(year)
  const moonPhaseInfo = getMoonPhase(currentTime)
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-light tracking-wide text-foreground sm:text-4xl">
              Watch Setting Tool
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Accurate time reference for setting your watches
            </p>
          </div>
          <button
            onClick={() => setIs24Hour(!is24Hour)}
            className="px-4 py-2 text-sm font-medium text-foreground bg-card border border-border rounded-sm hover:bg-accent"
          >
            {is24Hour ? '24h' : '12h'}
          </button>
        </div>

        {/* Main Clock Display */}
        <div className="p-8 bg-card border border-border rounded-sm">
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <Clock className="w-12 h-12 text-gold" />
            </div>
            <div className="mb-2 text-6xl font-mono font-bold text-foreground">
              {timeString}
            </div>
            <div className="text-lg text-muted-foreground">
              {dateString}
            </div>
          </div>
        </div>

        {/* Info Cards Grid */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {/* Day of Week Card */}
          <div className="p-6 bg-card border border-border rounded-sm">
            <div className="flex items-center justify-center mb-3">
              <Calendar className="w-6 h-6 text-gold" />
            </div>
            <h3 className="mb-2 text-xl font-light tracking-wide text-center text-foreground">
              Day of Week
            </h3>
            <p className="text-3xl font-bold text-center text-gold">
              {dayName}
            </p>
          </div>

          {/* Leap Year Cycle Card */}
          <div className="p-6 bg-card border border-border rounded-sm">
            <div className="flex items-center justify-center mb-3">
              <RotateCcw className="w-6 h-6 text-gold" />
            </div>
            <h3 className="mb-2 text-xl font-light tracking-wide text-center text-foreground">
              Leap Year Cycle
            </h3>
            <p className="text-3xl font-bold text-center text-gold">
              Year {leapYearInfo.position} of 4
            </p>
            <p className="mt-2 text-sm text-center text-muted-foreground">
              {leapYearInfo.isLeapYear ? `${year} is a Leap Year` : `${year} is a Common Year`}
            </p>
          </div>

          {/* Moon Phase Card */}
          <div className="p-6 bg-card border border-border rounded-sm">
            <div className="flex items-center justify-center mb-3">
              <Moon className="w-6 h-6 text-gold" />
            </div>
            <h3 className="mb-2 text-xl font-light tracking-wide text-center text-foreground">
              Moon Phase
            </h3>
            <div className="mb-2 text-5xl text-center">
              {moonPhaseInfo.emoji}
            </div>
            <p className="text-lg font-semibold text-center text-foreground">
              {moonPhaseInfo.phase}
            </p>
            <p className="mt-1 text-sm text-center text-muted-foreground">
              {moonPhaseInfo.percentage}% illuminated
            </p>
          </div>
        </div>

        {/* Time Zone Info */}
        <div className="p-4 text-sm text-muted-foreground bg-card border border-border rounded-sm">
          <p className="mb-1">
            <span className="font-semibold">Time Zone:</span> {timeZone}
          </p>
          <p className="text-xs">
            Note: Time is synced to your device's system clock. For best accuracy, ensure your device is set to sync with internet time servers (NTP).
          </p>
        </div>
      </div>
    </AppLayout>
  )
}
