import { useCallback, useState } from 'react'

export interface UseDisclosureResult {
  isOpen: boolean
  open: () => void
  close: () => void
  toggle: () => void
}

/** Generic open/close state, reusable for modals, drawers, and popovers. */
export function useDisclosure(defaultOpen = false): UseDisclosureResult {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  const open = useCallback(() => setIsOpen(true), [])
  const close = useCallback(() => setIsOpen(false), [])
  const toggle = useCallback(() => setIsOpen((prev) => !prev), [])

  return { isOpen, open, close, toggle }
}
