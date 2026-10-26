import { Slider } from '@base-ui/react/slider'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

type ScoreScaleProps = {
  lower: number
  upper: number
  onChange: (lower: number, upper: number) => void
}

export function ScoreScale({ lower, upper, onChange }: ScoreScaleProps) {
  // Clamped pair for the bar — always valid, never crossed
  const safeL = Number.isFinite(lower) ? Math.max(0, Math.min(100, lower)) : 0
  const safeU = Number.isFinite(upper) ? Math.max(0, Math.min(100, upper)) : 100
  const l = Math.max(0, Math.min(99, Math.min(safeL, safeU - 1)))
  const u = Math.max(l + 1, Math.min(100, Math.max(safeU, safeL + 1)))

  const invalid = !(lower >= 0 && lower < upper && upper <= 100)

  function handleBlurLower() {
    const v = Number.isFinite(lower) ? lower : 0
    const clamped = Math.max(0, Math.min(100, Math.round(v)))
    if (clamped !== lower) onChange(clamped, upper)
  }

  function handleBlurUpper() {
    const v = Number.isFinite(upper) ? upper : 100
    const clamped = Math.max(0, Math.min(100, Math.round(v)))
    if (clamped !== upper) onChange(lower, clamped)
  }

  return (
    <fieldset className="flex flex-col gap-4 border-0 p-0 m-0">
      <legend className="sr-only">Score cut-offs</legend>

      {/* Scale ends */}
      <div className="flex justify-between text-xs font-medium tabular-nums text-muted-foreground">
        <span>0</span>
        <span>100</span>
      </div>

      {/* Slider */}
      <Slider.Root
        min={0}
        max={100}
        step={1}
        minStepsBetweenValues={1}
        value={[l, u]}
        onValueChange={(values) => onChange(values[0], values[1])}
      >
        <Slider.Control className="relative flex items-center h-7 touch-none">
          <Slider.Track className="relative h-3 w-full rounded-full overflow-hidden ring-1 ring-foreground/10">
            {/* Rejected zone */}
            <div
              className="absolute inset-y-0 left-0 bg-zone-rejected rounded-l-full"
              style={{ width: `${l}%` }}
            />
            {/* You decide zone */}
            <div
              className="absolute inset-y-0 bg-zone-decide"
              style={{ left: `${l}%`, width: `${u - l}%` }}
            >
              <div
                className="absolute inset-0 opacity-10"
                style={{
                  backgroundImage:
                    'repeating-linear-gradient(45deg, transparent, transparent 4px, currentColor 4px, currentColor 5px)',
                }}
              />
            </div>
            {/* On your calendar zone */}
            <div
              className="absolute inset-y-0 right-0 bg-zone-calendar rounded-r-full"
              style={{ width: `${100 - u}%` }}
            />
          </Slider.Track>
          <Slider.Thumb
            index={0}
            className="absolute size-7 rounded-full bg-card border-2 border-foreground shadow-md -translate-x-1/2 hover:ring-4 hover:ring-ring/20 focus-within:ring-4 focus-within:ring-ring/40 transition-shadow duration-150"
            getAriaLabel={() => 'Auto-reject below'}
            getAriaValueText={(_formatted, value) => `${value} out of 100`}
          />
          <Slider.Thumb
            index={1}
            className="absolute size-7 rounded-full bg-card border-2 border-foreground shadow-md -translate-x-1/2 hover:ring-4 hover:ring-ring/20 focus-within:ring-4 focus-within:ring-ring/40 transition-shadow duration-150"
            getAriaLabel={() => 'Auto-accept above'}
            getAriaValueText={(_formatted, value) => `${value} out of 100`}
          />
        </Slider.Control>
      </Slider.Root>

      {/* Thumb value labels */}
      <div className="relative h-4 text-xs font-semibold tabular-nums text-foreground">
        <span
          aria-hidden="true"
          className="absolute -translate-x-1/2"
          style={{ left: `${l}%` }}
        >
          {l}
        </span>
        <span
          aria-hidden="true"
          className="absolute -translate-x-1/2"
          style={{ left: `${u}%` }}
        >
          {u}
        </span>
      </div>

      {/* Zone legend — labels keep their natural width and wrap as needed. */}
      <div className="hidden sm:flex flex-wrap gap-x-3 gap-y-1 text-[13px] font-medium">
        <span className="flex items-center gap-1 shrink-0">
          <span className="size-2 rounded-full bg-zone-rejected shrink-0" aria-hidden="true" />
          Out
        </span>
        <span className="flex items-center gap-1 shrink-0">
          <span className="size-2 rounded-full bg-zone-decide shrink-0" aria-hidden="true" />
          You decide
        </span>
        <span className="flex items-center gap-1 shrink-0">
          <span className="size-2 rounded-full bg-zone-calendar shrink-0" aria-hidden="true" />
          On your calendar
        </span>
      </div>

      {/* Zone legend — phone: vertical with swatches */}
      <div className="flex sm:hidden flex-col gap-1 text-sm">
        <div className="flex items-center gap-2">
          <span className="inline-block w-3 h-3 rounded-full bg-zone-rejected shrink-0" />
          <span>Out</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block w-3 h-3 rounded-full bg-zone-decide border border-foreground/10 shrink-0" />
          <span>You decide</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block w-3 h-3 rounded-full bg-zone-calendar shrink-0" />
          <span>On your calendar</span>
        </div>
      </div>

      {/* Number inputs */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex flex-col gap-2 flex-1">
          <Label htmlFor="auto-reject">Auto-reject below</Label>
          <Input
            id="auto-reject"
            type="number"
            inputMode="numeric"
            min={0}
            max={upper - 1}
            step={1}
            className="w-24 tabular-nums"
            value={lower}
            onChange={(e) => onChange(Number(e.target.value), upper)}
            onBlur={handleBlurLower}
          />
        </div>
        <div className="flex flex-col gap-2 flex-1">
          <Label htmlFor="auto-accept">Auto-accept above</Label>
          <Input
            id="auto-accept"
            type="number"
            inputMode="numeric"
            min={lower + 1}
            max={100}
            step={1}
            className="w-24 tabular-nums"
            value={upper}
            onChange={(e) => onChange(lower, Number(e.target.value))}
            onBlur={handleBlurUpper}
          />
        </div>
      </div>

      {/* Validation line */}
      {invalid && (
        <p role="alert" className="text-sm text-destructive">
          The auto-accept line must be higher than the auto-reject line.
        </p>
      )}
    </fieldset>
  )
}
