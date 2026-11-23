import { SelectHTMLAttributes, forwardRef, useId } from 'react'

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
  options: Array<{ value: string; label: string }>
  placeholder?: string
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, options, placeholder, className = '', ...props }, ref) => {
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
        <select
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
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {error && (
          <p id={`${id}-error`} className="mt-1 text-sm text-destructive">
            {error}
          </p>
        )}
      </div>
    )
  }
)

Select.displayName = 'Select'

export default Select
