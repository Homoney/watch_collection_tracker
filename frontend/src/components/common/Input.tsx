import { InputHTMLAttributes, forwardRef, useId } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', ...props }, ref) => {
    // Ties the label (and error) to the field when the caller gives no id
    const autoId = useId()
    const id = props.id ?? autoId
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={id} className="block text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground mb-1.5">
            {label}
            {props.required && <span className="text-destructive ml-1">*</span>}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${id}-error` : undefined}
          className={`
            appearance-none block w-full px-3 py-2 border border-input rounded-sm
            bg-card text-foreground placeholder:text-muted-foreground
            focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring
            disabled:opacity-60 disabled:cursor-not-allowed
            sm:text-sm
            ${error ? 'border-destructive' : ''}
            ${className}
          `}
          {...props}
        />
        {error && (
          <p id={`${id}-error`} className="mt-1 text-sm text-destructive">
            {error}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export default Input
