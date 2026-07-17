import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { addIncidentNote, closeIncident, escalateIncident } from '../services/incidentService'
import type { Incident, IncidentClassification, IncidentSeverity } from '../types/incident'
import { incidentClassificationLabel } from '../utils/incidentDisplay'

const CLASSIFICATIONS: IncidentClassification[] = [
  'operational_episode',
  'near_miss',
  'safety_incident',
  'reportable_incident',
]
const SEVERITIES: IncidentSeverity[] = ['negligible', 'minor', 'serious', 'major', 'catastrophic']

const textareaClass =
  'w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:border-accent'
const selectClass =
  'h-9 rounded-md border border-border bg-surface px-3 text-sm text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent'

export interface IncidentActionsPanelProps {
  incident: Incident
  onChange: (updated: Incident) => void
}

/** The narrow set of things a human can do to an incident that isn't already closed: leave a
 * note, reclassify it, or close it out. Notes surface later as timeline events — there's no
 * separate "notes" field to render here. */
export function IncidentActionsPanel({ incident, onChange }: IncidentActionsPanelProps) {
  const [noteText, setNoteText] = useState('')
  const [isAddingNote, setIsAddingNote] = useState(false)

  const [classification, setClassification] = useState<IncidentClassification>(incident.classification)
  const [isEscalating, setIsEscalating] = useState(false)

  const [rootCause, setRootCause] = useState('')
  const [correctiveActionsText, setCorrectiveActionsText] = useState('')
  const [incidentSeverity, setIncidentSeverity] = useState<IncidentSeverity | ''>('')
  const [isClosing, setIsClosing] = useState(false)
  const [closeError, setCloseError] = useState<string | null>(null)

  const requiresRootCause = incident.classification === 'reportable_incident'

  async function handleAddNote() {
    if (!noteText.trim()) return
    setIsAddingNote(true)
    try {
      const updated = await addIncidentNote(incident.id, { noteText: noteText.trim() })
      onChange(updated)
      setNoteText('')
    } finally {
      setIsAddingNote(false)
    }
  }

  async function handleEscalate() {
    if (classification === incident.classification) return
    setIsEscalating(true)
    try {
      const updated = await escalateIncident(incident.id, { classification })
      onChange(updated)
    } finally {
      setIsEscalating(false)
    }
  }

  async function handleClose() {
    setCloseError(null)
    if (requiresRootCause && (!rootCause.trim() || !incidentSeverity)) {
      setCloseError('A reportable incident needs a root cause and an impact severity before it can be closed.')
      return
    }
    setIsClosing(true)
    try {
      const updated = await closeIncident(incident.id, {
        rootCause: rootCause.trim() || undefined,
        incidentSeverity: incidentSeverity || undefined,
        correctiveActions: correctiveActionsText
          .split('\n')
          .map((line) => line.trim())
          .filter(Boolean),
      })
      onChange(updated)
    } catch (err) {
      setCloseError(err instanceof Error ? err.message : 'Could not close this incident.')
    } finally {
      setIsClosing(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Add a note</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <textarea
            value={noteText}
            onChange={(event) => setNoteText(event.target.value)}
            placeholder="What did you observe or do about this?"
            rows={3}
            className={textareaClass}
          />
          <Button
            size="sm"
            onClick={handleAddNote}
            isLoading={isAddingNote}
            disabled={!noteText.trim()}
            className="self-start"
          >
            Add note
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Reclassify</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-3">
          <select
            value={classification}
            onChange={(event) => setClassification(event.target.value as IncidentClassification)}
            className={selectClass}
          >
            {CLASSIFICATIONS.map((value) => (
              <option key={value} value={value}>
                {incidentClassificationLabel(value)}
              </option>
            ))}
          </select>
          <Button
            size="sm"
            variant="secondary"
            onClick={handleEscalate}
            isLoading={isEscalating}
            disabled={classification === incident.classification}
          >
            Update classification
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Close incident</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {requiresRootCause && (
            <p className="text-xs text-text-muted">
              Reportable incidents need a root cause and an impact severity before they can close.
            </p>
          )}
          <textarea
            value={rootCause}
            onChange={(event) => setRootCause(event.target.value)}
            placeholder="Root cause (required for reportable incidents)"
            rows={2}
            className={textareaClass}
          />
          <textarea
            value={correctiveActionsText}
            onChange={(event) => setCorrectiveActionsText(event.target.value)}
            placeholder="Corrective actions, one per line"
            rows={2}
            className={textareaClass}
          />
          <select
            value={incidentSeverity}
            onChange={(event) => setIncidentSeverity(event.target.value as IncidentSeverity | '')}
            className={`${selectClass} w-fit`}
          >
            <option value="">Actual impact (optional)</option>
            {SEVERITIES.map((value) => (
              <option key={value} value={value}>
                {value[0].toUpperCase() + value.slice(1)}
              </option>
            ))}
          </select>
          {closeError && <p className="text-xs text-danger">{closeError}</p>}
          <Button size="sm" variant="destructive" onClick={handleClose} isLoading={isClosing} className="self-start">
            Close incident
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
