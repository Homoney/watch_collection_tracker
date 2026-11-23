import { ReactNode } from 'react'
import Navbar from './Navbar'

interface AppLayoutProps {
  children: ReactNode
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />
      {/* pb-24 on phones keeps content clear of the bottom tab bar */}
      <main className="mx-auto max-w-7xl px-4 pb-24 pt-6 sm:px-6 md:pb-10 md:pt-10 lg:px-8">{children}</main>
    </div>
  )
}
