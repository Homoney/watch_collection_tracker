import { useAuth } from '@/contexts/AuthContext'

export default function DashboardPage() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">Watch Collection Tracker</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                Welcome, {user?.full_name || user?.email}
              </span>
              <button
                onClick={logout}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-4 border-dashed border-gray-200 rounded-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Welcome to Your Dashboard</h2>
            <p className="text-gray-600">
              This is the foundation of the Watch Collection Tracker. Phase 1 (Authentication) is complete!
            </p>
            <div className="mt-6 bg-blue-50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">Next Steps:</h3>
              <ul className="list-disc list-inside text-blue-800 space-y-1">
                <li>Phase 2: Watch and collection management</li>
                <li>Phase 3: Image upload and management</li>
                <li>Phase 4: Statistics and analytics</li>
                <li>Phase 5: Service history tracking</li>
                <li>Phase 6: Export and sharing features</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
