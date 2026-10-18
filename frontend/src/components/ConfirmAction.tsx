import { useState } from 'react'
import { Button } from '@/components/ui/button'

type ConfirmActionProps = {
  label: string
  prompt: string
  confirmLabel: string
  confirmingLabel?: string
  errorText?: string
  onConfirm: () => Promise<void>
  testId?: string
  /** When set, the confirm container gets this testid, confirm button gets `${confirmTestId}-yes`, cancel gets `${confirmTestId}-cancel` */
  confirmTestId?: string
}

export function ConfirmAction({
  label,
  prompt,
  confirmLabel,
  confirmingLabel,
  errorText = 'Something went wrong. Try again.',
  onConfirm,
  testId,
  confirmTestId,
}: ConfirmActionProps) {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  if (!open) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen(true)}
        data-testid={testId}
      >
        {label}
      </Button>
    )
  }

  async function handleConfirm() {
    setBusy(true)
    setError('')
    try {
      await onConfirm()
      setOpen(false)
    } catch {
      setError(errorText)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2" data-testid={confirmTestId}>
      <span className="text-sm">{prompt}</span>
      <Button
        size="sm"
        variant="destructive"
        disabled={busy}
        onClick={handleConfirm}
        data-testid={confirmTestId ? `${confirmTestId}-yes` : undefined}
      >
        {busy ? (confirmingLabel ?? confirmLabel) : confirmLabel}
      </Button>
      <Button
        size="sm"
        variant="outline"
        disabled={busy}
        onClick={() => {
          setOpen(false)
          setError('')
        }}
        data-testid={confirmTestId ? `${confirmTestId}-cancel` : undefined}
      >
        Cancel
      </Button>
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  )
}
