import { forwardRef } from 'react'
import { Button as UIButton, type ButtonProps as UIButtonProps } from '@/components/ui/button'

/**
 * The app's one button set. A thin wrapper over the shadcn/ui Button that
 * keeps the old variant names, so every screen gets the same three styles:
 * primary (solid gold), secondary (outline), danger (red outline).
 */
interface ButtonProps extends Omit<UIButtonProps, 'variant' | 'size'> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost' | 'link'
  size?: 'sm' | 'md' | 'lg' | 'icon'
}

const variantMap = {
  primary: 'default',
  secondary: 'secondary',
  outline: 'outline',
  danger: 'destructive',
  ghost: 'ghost',
  link: 'link',
} as const

const sizeMap = { sm: 'sm', md: 'default', lg: 'lg', icon: 'icon' } as const

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', ...props }, ref) => (
    <UIButton ref={ref} variant={variantMap[variant]} size={sizeMap[size]} {...props} />
  )
)
Button.displayName = 'Button'

export default Button
