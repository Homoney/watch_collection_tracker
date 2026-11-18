import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderWithProviders, screen } from '../test-utils'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import { authApi } from '@/lib/api'

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ login: vi.fn(), register: vi.fn() }),
}))

describe('first-admin setup', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('login page points to admin sign-up when no accounts exist', async () => {
    vi.spyOn(authApi, 'setupStatus').mockResolvedValue({ setup_required: true, admin_signup: true })
    renderWithProviders(<LoginPage />)

    const link = await screen.findByRole('link', { name: 'Create the admin account' })
    expect(link).toHaveAttribute('href', '/register')
    expect(screen.getByText(/no password to sign in with/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Sign in' })).not.toBeInTheDocument()
  })

  it('login page shows the normal sign-in form once accounts exist', async () => {
    const spy = vi.spyOn(authApi, 'setupStatus').mockResolvedValue({ setup_required: false, admin_signup: false })
    renderWithProviders(<LoginPage />)

    expect(await screen.findByRole('button', { name: 'Sign in' })).toBeInTheDocument()
    expect(spy).toHaveBeenCalled()
    expect(screen.getByText('Sign in to your account')).toBeInTheDocument()
    expect(screen.queryByText(/INITIAL_ADMIN_EMAIL/)).not.toBeInTheDocument()
  })

  it('login page falls back to the sign-in form if the check fails', async () => {
    vi.spyOn(authApi, 'setupStatus').mockRejectedValue(new Error('offline'))
    renderWithProviders(<LoginPage />)

    expect(await screen.findByRole('button', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('shows the normal pages when the first sign-up will not be admin', async () => {
    // ALLOW_REGISTRATION=true without INITIAL_ADMIN_EMAIL: first user is a plain user
    vi.spyOn(authApi, 'setupStatus').mockResolvedValue({ setup_required: true, admin_signup: false })
    renderWithProviders(<LoginPage />)
    expect(await screen.findByRole('button', { name: 'Sign in' })).toBeInTheDocument()
    expect(screen.queryByText(/admin/i)).not.toBeInTheDocument()
  })

  it('register page explains the first account becomes the admin', async () => {
    vi.spyOn(authApi, 'setupStatus').mockResolvedValue({ setup_required: true, admin_signup: true })
    renderWithProviders(<RegisterPage />)

    expect(
      await screen.findByRole('heading', { name: 'Create the admin account' })
    ).toBeInTheDocument()
    expect(screen.getByText(/becomes the administrator/i)).toBeInTheDocument()
    expect(screen.getByLabelText('Email address')).toHaveValue('')
  })

  it('register page is unchanged once accounts exist', async () => {
    vi.spyOn(authApi, 'setupStatus').mockResolvedValue({ setup_required: false, admin_signup: false })
    renderWithProviders(<RegisterPage />)

    expect(await screen.findByRole('heading', { name: 'Create your account' })).toBeInTheDocument()
    expect(screen.queryByText(/administrator/i)).not.toBeInTheDocument()
  })
})
