import { useState } from 'react'
import type { RunSummary } from '@/services/api'

const time = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: false,
})

/** "18 Oct 09:00" in the browser zone. */
export function fmtStamp(iso: string): string {
  return time.format(new Date(iso)).replace(',', '')
}

function Dot({ className }: { className: string }) {
  return <i className={`inline-block size-1.5 rounded-full mx-1 ${className}`} />
}

export function EarlierRuns({ runs }: { runs: RunSummary[] }) {
  const [all, setAll] = useState(false)
  if (runs.length === 0) return null
  const shown = all ? runs : runs.slice(0, 3)
  return (
    <div className="mt-3">
      <p className="flex items-baseline justify-between text-[11px] font-semibold uppercase tracking-[.08em] text-muted-foreground">
        Earlier runs
        <span className="font-mono text-[10px] font-normal normal-case tracking-normal">
          <Dot className="bg-zone-calendar" />in calendar
          <Dot className="bg-zone-decide" />to review
          <Dot className="bg-zone-rejected" />rejected
        </span>
      </p>
      {shown.map((r) => (
        <div
          key={r.runId}
          data-testid="earlier-run"
          className="grid grid-cols-[84px_1fr] md:grid-cols-[84px_1fr_auto] gap-2.5 items-center text-[10px] font-mono text-muted-foreground whitespace-nowrap py-0.5"
        >
          <span>{fmtStamp(r.startedAt)}</span>
          <div className="h-[5px] rounded-[3px] bg-border flex overflow-hidden">
            {r.eventsFound > 0 && (
              <>
                <i className="bg-zone-calendar" style={{ width: `${(r.accepted / r.eventsFound) * 100}%` }} />
                <i className="bg-zone-decide" style={{ width: `${(r.queued / r.eventsFound) * 100}%` }} />
                <i className="bg-zone-rejected opacity-50" style={{ width: `${(r.rejected / r.eventsFound) * 100}%` }} />
              </>
            )}
          </div>
          <span className="hidden md:inline">
            {r.eventsFound} found{r.error ? ' · failed' : ''}
            <Dot className="bg-zone-calendar" />{r.accepted}
            <Dot className="bg-zone-decide" />{r.queued}
            <Dot className="bg-zone-rejected" />{r.rejected}
          </span>
        </div>
      ))}
      {!all && runs.length > 3 && (
        <div className="grid grid-cols-[84px_1fr] md:grid-cols-[84px_1fr_auto] gap-2.5 items-center text-[10px] font-mono text-muted-foreground whitespace-nowrap py-0.5">
          <button type="button" data-testid="earlier-runs-more" className="text-left hover:text-foreground" onClick={() => setAll(true)}>
            earlier ›
          </button>
          <div />
          <span className="hidden md:inline">{runs.length} runs</span>
        </div>
      )}
    </div>
  )
}
