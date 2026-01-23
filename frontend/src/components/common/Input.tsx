import { InputHTMLAttributes, forwardRef } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-ink-medium text-sm mb-2 font-body">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`
            ink-input
            ${error ? 'border-vermilion focus:border-vermilion' : ''}
            ${className}
          `}
          {...props}
        />
        {error && (
          <p className="mt-1 text-sm text-vermilion">{error}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export default Input
