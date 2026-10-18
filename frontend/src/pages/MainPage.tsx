import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { ScoreScale } from '@/components/ScoreScale'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { ConfirmAction } from '@/components/ConfirmAction'
import {
  getCriteria,
  saveCriteria,
  getThresholds,
  saveThresholds,
  runSearch,
  getCalendarUrl,
  rotateCalendarUrl,
} from '@/services/api'

type MainPageProps = {
  onSearchComplete: () => Promise<number>
}

export function MainPage({ onSearchComplete }: MainPageProps) {
  const [criteriaText, setCriteriaText] = useState('')
  const [criteriaSaved, setCriteriaSaved] = useState(false)
  const [criteriaError, setCriteriaError] = useState('')
  const [criteriaSaving, setCriteriaSaving] = useState(false)

  const [lower, setLower] = useState(0)
  const [upper, setUpper] = useState(100)
  const [scoringSaved, setScoringSaved] = useState(false)
  const [scoringError, setScoringError] = useState('')
  const [scoringSaving, setScoringSaving] = useState(false)

  const [searching, setSearching] = useState(false)
  const [searchResultText, setSearchResultText] = useState('')
  const [searchIsError, setSearchIsError] = useState(false)

  const [calendarUrl, setCalendarUrl] = useState('')
  const [copied, setCopied] = useState(false)

  const thresholdInvalid = !(lower >= 0 && lower < upper && upper <= 100)

  useEffect(() => {
    getCriteria().then((c) => setCriteriaText(c.text))
    getThresholds().then((t) => {
      setLower(t.lowerThreshold)
      setUpper(t.upperThreshold)
    })
    getCalendarUrl().then((r) => setCalendarUrl(r.url))
  }, [])

  function showCriteriaSaved() {
    setCriteriaSaved(true)
    setTimeout(() => setCriteriaSaved(false), 2000)
  }

  async function handleSaveCriteria() {
    setCriteriaSaving(true)
    setCriteriaSaved(false)
    setCriteriaError('')
    try {
      const saved = await saveCriteria(criteriaText)
      setCriteriaText(saved.text)
      showCriteriaSaved()
    } catch {
      setCriteriaError("Couldn't save. Try again.")
    } finally {
      setCriteriaSaving(false)
    }
  }

  async function handleSaveScoring() {
    if (thresholdInvalid) return
    setScoringSaving(true)
    setScoringSaved(false)
    setScoringError('')
    try {
      const saved = await saveThresholds({
        lowerThreshold: lower,
        upperThreshold: upper,
      })
      setLower(saved.lowerThreshold)
      setUpper(saved.upperThreshold)
      setScoringSaved(true)
      setTimeout(() => setScoringSaved(false), 2000)
    } catch {
      setScoringError("Couldn't save. Try again.")
    } finally {
      setScoringSaving(false)
    }
  }

  async function handleSearch() {
    setSearching(true)
    setSearchResultText('')
    setSearchIsError(false)

    // Save criteria draft first (decision 11)
    setCriteriaSaved(false)
    setCriteriaError('')
    try {
      const saved = await saveCriteria(criteriaText)
      setCriteriaText(saved.text)
      showCriteriaSaved()
    } catch {
      setCriteriaError("Couldn't save. Try again.")
      setSearching(false)
      return
    }

    try {
      const result = await runSearch()
      const queueCount = await onSearchComplete()

      if (result.eventsFound === 0) {
        setSearchResultText('Found no events. Try broader criteria.')
      } else {
        let msg = `Found ${result.eventsFound} events, ${result.eventsNew} new.`
        if (queueCount > 0) {
          msg += ` ${queueCount} waiting for you in the Queue.`
        }
        setSearchResultText(msg)
      }
    } catch {
      setSearchResultText('Search failed. Try again.')
      setSearchIsError(true)
    } finally {
      setSearching(false)
    }
  }

  async function handleCopyCalendarUrl() {
    try {
      await navigator.clipboard.writeText(calendarUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // clipboard API unavailable (e.g. test environments)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Criteria card */}
      <Card data-testid="criteria-card">
        <CardHeader>
          <CardTitle>What I&apos;m looking for</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Textarea
            aria-label="What I'm looking for"
            placeholder="e.g. jazz or folk concerts near Paris on weekends, under 40 EUR"
            value={criteriaText}
            onChange={(e) => setCriteriaText(e.target.value)}
            rows={4}
          />
          <div className="flex items-center gap-2">
            <Button
              aria-label="Save criteria"
              disabled={criteriaSaving}
              onClick={handleSaveCriteria}
            >
              Save
            </Button>
            {criteriaSaved && (
              <span role="status" className="text-sm">Saved.</span>
            )}
            {criteriaError && (
              <span className="text-sm text-destructive">{criteriaError}</span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Scoring card */}
      <Card data-testid="scoring-card">
        <CardHeader>
          <CardTitle>How scoring works</CardTitle>
          <CardDescription>
            Every event gets a match score from 0 to 100 against what you wrote
            above. Events in between wait for you in the Queue tab.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <ScoreScale
            lower={lower}
            upper={upper}
            onChange={(l, u) => { setLower(l); setUpper(u) }}
          />
          <div className="flex items-center gap-2">
            <Button
              aria-label="Save scoring"
              disabled={thresholdInvalid || scoringSaving}
              onClick={handleSaveScoring}
            >
              Save
            </Button>
            {scoringSaved && (
              <span role="status" className="text-sm">Saved.</span>
            )}
            {scoringError && (
              <span className="text-sm text-destructive">{scoringError}</span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Search card */}
      <Card data-testid="search-card">
        <CardHeader>
          <CardTitle>Search now</CardTitle>
          <CardDescription>
            The app also searches automatically every hour.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {!criteriaText.trim() && (
            <p className="text-sm text-muted-foreground">
              Write what you&apos;re looking for, then press Search now.
            </p>
          )}
          <Button
            disabled={!criteriaText.trim() || searching}
            onClick={handleSearch}
          >
            {searching ? 'Searching…' : 'Search now'}
          </Button>
          {searchResultText && (
            <p
              data-testid="search-result"
              role="status"
              className={searchIsError ? 'text-sm text-destructive' : 'text-sm'}
            >
              {searchResultText}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Calendar card */}
      {calendarUrl && (
        <Card data-testid="calendar-card">
          <CardHeader>
            <CardTitle>Your calendar feed</CardTitle>
            <CardDescription>
              Paste this link into your calendar app. Accepted events will appear
              there.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-wrap gap-2">
              <Input
                readOnly
                value={calendarUrl}
                data-testid="calendar-url"
                aria-label="Calendar feed URL"
                className="flex-1 min-w-0"
              />
              <Button onClick={handleCopyCalendarUrl} data-testid="copy-calendar-url">
                {copied ? 'Copied' : 'Copy'}
              </Button>
              <ConfirmAction
                label="Reset link"
                prompt="This will break any existing subscription. Reset?"
                confirmLabel="Reset"
                errorText="Couldn't reset the link. Try again."
                onConfirm={async () => {
                  const r = await rotateCalendarUrl()
                  setCalendarUrl(r.url)
                }}
                testId="rotate-calendar-url"
                confirmTestId="rotate-confirm"
              />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
