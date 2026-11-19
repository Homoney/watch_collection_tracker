import { createContext, useContext, useEffect } from 'react'

interface ModalFormContextValue {
  /** The form reports whether anything was typed */
  setDirty: (dirty: boolean) => void
  /** Close, asking first when something was typed (for a form's Cancel button) */
  requestClose: () => void
}

export const ModalFormContext = createContext<ModalFormContextValue | null>(null)

/**
 * For a form inside a form pop-up: report whether it has typed changes, and
 * get a Cancel handler that asks before discarding them. Outside a pop-up,
 * Cancel just calls `onCancel`.
 */
export function useModalForm(dirty: boolean, onCancel: () => void) {
  const ctx = useContext(ModalFormContext)
  const setDirty = ctx?.setDirty
  useEffect(() => {
    setDirty?.(dirty)
  }, [dirty, setDirty])
  return ctx ? ctx.requestClose : onCancel
}
