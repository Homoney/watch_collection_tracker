import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useAuth } from '@/contexts/AuthContext'
import { useAdminSignup } from '@/hooks/useSetupStatus'
import type { LoginRequest } from '@/types'

export default function LoginPage() {
  const { login } = useAuth()
  const adminSignup = useAdminSignup()
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginRequest>()

  const onSubmit = async (data: LoginRequest) => {
    setError(null)
    setIsLoading(true)

    try {
      await login(data)
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      setError(error.response?.data?.detail || 'Login failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-light tracking-wide text-foreground">
            Watch Collection Tracker
          </h2>
          <p className="mt-2 text-center text-sm text-muted-foreground">
            {adminSignup ? 'Create the admin account' : 'Sign in to your account'}
          </p>
        </div>

        {adminSignup && (
          <div className="space-y-3 rounded-sm border border-border bg-muted p-4" role="status">
            <p className="text-sm text-foreground">
              No accounts exist yet, so there is no password to sign in with. Sign up with the
              email address set in <code className="font-mono">INITIAL_ADMIN_EMAIL</code> and
              choose your password. That first account becomes the administrator.
            </p>
            <Link
              to="/register"
              className="w-full inline-flex h-10 items-center justify-center gap-2 rounded-sm border border-primary bg-primary px-5 text-[11px] font-medium uppercase tracking-[0.18em] text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            >
              Create the admin account
            </Link>
          </div>
        )}

        {!adminSignup && (
          <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
            {error && (
              <div className="rounded-sm border border-destructive/40 bg-destructive/10 p-4">
                <div className="text-sm text-destructive">{error}</div>
              </div>
            )}

            <div className="rounded-md shadow-sm -space-y-px">
              <div>
                <label htmlFor="email" className="sr-only">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  className="appearance-none relative focus:z-10 block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
                  placeholder="Email address"
                  {...register('email', { required: 'Email is required' })}
                />
                {errors.email && (
                  <p className="mt-1 text-sm text-destructive">{errors.email.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="password" className="sr-only">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  className="appearance-none relative focus:z-10 block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
                  placeholder="Password"
                  {...register('password', { required: 'Password is required' })}
                />
                {errors.password && (
                  <p className="mt-1 text-sm text-destructive">{errors.password.message}</p>
                )}
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="group relative w-full inline-flex h-10 items-center justify-center gap-2 rounded-sm border border-primary bg-primary px-5 text-[11px] font-medium uppercase tracking-[0.18em] text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isLoading ? 'Signing in...' : 'Sign in'}
              </button>
            </div>

            <div className="text-center">
              <Link
                to="/register"
                className="font-medium text-gold underline-offset-2 hover:underline"
              >
                Don't have an account? Sign up
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
