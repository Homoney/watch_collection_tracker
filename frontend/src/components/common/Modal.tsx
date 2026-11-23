import { ReactNode, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { ModalFormContext } from '@/components/common/modalForm'
import Button from '@/components/common/Button'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
  /**
   * A pop-up with a form: a click outside never closes it, and Escape, the X
   * and the form's Cancel ask "Discard changes?" when something was typed.
   */
  form?: boolean
  /** Typed changes, for a form that is not its own component (else useModalForm) */
  dirty?: boolean
}

/**
 * Gives a Cancel button inside a form pop-up the close that asks before
 * discarding typed changes: <ModalClose>{(close) => <button onClick={close} />}</ModalClose>
 */
export function ModalClose({ children }: { children: (close: () => void) => ReactNode }) {
  const ctx = useContext(ModalFormContext)
  return <>{children(ctx ? ctx.requestClose : () => undefined)}</>
}

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  form = false,
  dirty = false,
}: ModalProps) {
  const dirtyRef = useRef(false)
  const [confirming, setConfirming] = useState(false)

  const setDirty = useCallback((dirty: boolean) => {
    dirtyRef.current = dirty
  }, [])

  const requestClose = useCallback(() => {
    if (form && (dirtyRef.current || dirty)) {
      setConfirming(true)
    } else {
      onClose()
    }
  }, [form, dirty, onClose])

  const discard = () => {
    setConfirming(false)
    dirtyRef.current = false
    onClose()
  }

  useEffect(() => {
    if (!isOpen) {
      setConfirming(false)
      dirtyRef.current = false
    }
  }, [isOpen])

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      if (confirming) setConfirming(false)
      else requestClose()
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, confirming, requestClose])

  if (!isOpen) return null

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div
          className="fixed inset-0 bg-black/70 transition-opacity"
          data-testid="modal-backdrop"
          onClick={form ? undefined : onClose}
        />

        <div
          role="dialog"
          aria-modal="true"
          aria-label={title}
          className={`relative bg-card text-card-foreground border border-border rounded-sm shadow-2xl w-full ${sizeClasses[size]} max-h-[90vh] overflow-y-auto`}
        >
          <div className="flex items-center justify-between px-4 py-4 sm:px-6 border-b border-border">
            <h3 className="text-lg font-light tracking-wide text-foreground">{title}</h3>
            <button
              onClick={requestClose}
              aria-label="Close"
              className="text-muted-foreground hover:text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <ModalFormContext.Provider value={{ setDirty, requestClose }}>
            <div className="p-4 sm:p-6">{children}</div>
          </ModalFormContext.Provider>

          {confirming && (
            <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 p-4">
              <div
                role="alertdialog"
                aria-labelledby="discard-title"
                className="w-full max-w-sm rounded-sm border border-border bg-popover p-4 text-popover-foreground shadow-xl"
              >
                <p id="discard-title" className="font-medium text-foreground">
                  Discard changes?
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  What you typed in this form will be lost.
                </p>
                <div className="mt-4 flex justify-end gap-2">
                  <Button type="button" variant="secondary" size="sm" autoFocus onClick={() => setConfirming(false)}>
                    Keep editing
                  </Button>
                  <Button type="button" variant="danger" size="sm" onClick={discard}>
                    Discard
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
