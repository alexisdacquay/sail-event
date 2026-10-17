import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  getCriteria,
  saveCriteria,
  getThresholds,
  saveThresholds,
  runSearch,
  getCalendarUrl,
  rotateCalendarUrl,
} from '@/services/api'
import type { SearchResult } from '@/services/api'
import { useAuth } from '@/contexts/AuthContext'

type MainPageProps = {
  embedded?: boolean
}

export function MainPage({ embedded }: MainPageProps) {
  const { auth, logout } = useAuth()

  const [criteriaText, setCriteriaText] = useState('')
  const [lower, setLower] = useState(0)
  const [upper, setUpper] = useState(100)
  const [thresholdError, setThresholdError] = useState('')
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null)
  const [calendarUrl, setCalendarUrl] = useState('')
  const [copied, setCopied] = useState(false)
  const [rotateConfirm, setRotateConfirm] = useState(false)

  useEffect(() => {
    getCriteria().then((c) => setCriteriaText(c.text))
    getThresholds().then((t) => {
      setLower(t.lowerThreshold)
      setUpper(t.upperThreshold)
    })
    getCalendarUrl().then((r) => setCalendarUrl(r.url))
  }, [])

  async function handleSaveCriteria() {
    const saved = await saveCriteria(criteriaText)
    setCriteriaText(saved.text)
  }

  function validateThresholds(l: number, u: number): boolean {
    if (l >= u) {
      setThresholdError('Lower threshold must be less than upper threshold')
      return false
    }
    setThresholdError('')
    return true
  }

  async function handleSaveThresholds() {
    if (!validateThresholds(lower, upper)) return
    const saved = await saveThresholds({
      lowerThreshold: lower,
      upperThreshold: upper,
    })
    setLower(saved.lowerThreshold)
    setUpper(saved.upperThreshold)
  }

  async function handleSearch() {
    const result = await runSearch()
    setSearchResult(result)
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
    <div className={embedded ? 'flex flex-col gap-6' : 'min-h-screen p-8 max-w-2xl mx-auto flex flex-col gap-6'}>
      {!embedded && (
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Sail Event</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              {auth?.username}
            </span>
            <Button variant="outline" size="sm" onClick={logout}>
              Logout
            </Button>
          </div>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Search Criteria</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Textarea
            aria-label="Criteria"
            value={criteriaText}
            onChange={(e) => setCriteriaText(e.target.value)}
            rows={4}
          />
          <Button onClick={handleSaveCriteria}>Save Criteria</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Thresholds</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex gap-4">
            <div className="flex flex-col gap-2 flex-1">
              <Label htmlFor="lower">Lower Threshold</Label>
              <Input
                id="lower"
                type="number"
                value={lower}
                onChange={(e) => setLower(Number(e.target.value))}
              />
            </div>
            <div className="flex flex-col gap-2 flex-1">
              <Label htmlFor="upper">Upper Threshold</Label>
              <Input
                id="upper"
                type="number"
                value={upper}
                onChange={(e) => setUpper(Number(e.target.value))}
              />
            </div>
          </div>
          {thresholdError && (
            <p className="text-sm text-destructive">{thresholdError}</p>
          )}
          <Button onClick={handleSaveThresholds}>Save Thresholds</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Search</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Button onClick={handleSearch}>Search now</Button>
          {searchResult && (
            <p data-testid="search-result">
              Search complete: {searchResult.eventsFound} events found,{' '}
              {searchResult.eventsNew} new
            </p>
          )}
        </CardContent>
      </Card>

      {calendarUrl && (
        <Card>
          <CardHeader>
            <CardTitle>Calendar Feed</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="text-sm text-muted-foreground">
              Subscribe from your calendar app
            </p>
            <div className="flex gap-2">
              <Input
                readOnly
                value={calendarUrl}
                data-testid="calendar-url"
                aria-label="Calendar feed URL"
              />
              <Button onClick={handleCopyCalendarUrl} data-testid="copy-calendar-url">
                {copied ? 'Copied' : 'Copy'}
              </Button>
              {!rotateConfirm ? (
                <Button
                  variant="outline"
                  onClick={() => setRotateConfirm(true)}
                  data-testid="rotate-calendar-url"
                >
                  Rotate link
                </Button>
              ) : (
                <span className="inline-flex items-center gap-1 text-sm" data-testid="rotate-confirm">
                  Are you sure?
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={async () => {
                      const r = await rotateCalendarUrl()
                      setCalendarUrl(r.url)
                      setRotateConfirm(false)
                    }}
                    data-testid="rotate-confirm-yes"
                  >
                    Confirm
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setRotateConfirm(false)}
                    data-testid="rotate-confirm-cancel"
                  >
                    Cancel
                  </Button>
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
