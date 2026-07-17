import { useEffect, useState } from 'react'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { fetchPlantState } from '@/features/plant/services/plantService'
import type { Zone } from '@/features/plant'
import { createIncident } from '../services/incidentService'
import type { Incident, IncidentClassification } from '../types/incident'
import { incidentClassificationLabel } from '../utils/incidentDisplay'

const CLASSIFICATIONS: IncidentClassification[] = [
  'safety_incident',
  'near_miss',
  'reportable_incident',
  'operational_episode',
]

export interface ManualIncidentModalProps {
  isOpen: boolean
  onClose: () => void
  onCreated: (incident: Incident) => void
}

/** The path for incidents the sensors never saw at all — an operator logging something like a
 * slip-and-fall that no risk rule could ever have triggered. */
export function ManualIncidentModal({ isOpen, onClose, onCreated }: ManualIncidentModalProps) {
  const [zones, setZones] = useState<Zone[]>([])
  const [zoneId, setZoneId] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [classification, setClassification] = useState<IncidentClassification>('safety_incident')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isOpen) return
    fetchPlantState().then((state) => {
      const zoneList = state.zones.map((entry) => entry.zone)
      setZones(zoneList)
      setZoneId((current) => current || zoneList[0]?.id || '')
    })
  }, [isOpen])

  function reset() {
    setTitle('')
    setDescription('')
    setClassification('safety_incident')
    setError(null)
  }

  function handleClose() {
    reset()
    onClose()
  }

  async function handleSubmit() {
    if (!zoneId || !title.trim() || !description.trim()) {
      setError('A zone, a title, and a description are all required.')
      return
    }
    setIsSubmitting(true)
    setError(null)
    try {
      const incident = await createIncident({
        primaryZoneId: zoneId,
        title: title.trim(),
        description: description.trim(),
        classification,
      })
      onCreated(incident)
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create the incident.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Log an incident"
      description="For anything the sensors never saw — an injury, a near miss, a spill."
      footer={
        <div className="flex items-center justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={handleClose}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleSubmit} isLoading={isSubmitting}>
            Log incident
          </Button>
        </div>
      }
    >
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-text-primary" htmlFor="incident-zone">
            Zone
          </label>
          <select
            id="incident-zone"
            value={zoneId}
            onChange={(event) => setZoneId(event.target.value)}
            className="h-9 rounded-md border border-border bg-surface px-3 text-sm text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            {zones.map((zone) => (
              <option key={zone.id} value={zone.id}>
                {zone.name}
              </option>
            ))}
          </select>
        </div>

        <Input
          label="Title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Worker slipped near Tank 4"
        />

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-text-primary" htmlFor="incident-description">
            What happened
          </label>
          <textarea
            id="incident-description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            rows={3}
            className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-text-primary" htmlFor="incident-classification">
            Classification
          </label>
          <select
            id="incident-classification"
            value={classification}
            onChange={(event) => setClassification(event.target.value as IncidentClassification)}
            className="h-9 rounded-md border border-border bg-surface px-3 text-sm text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            {CLASSIFICATIONS.map((value) => (
              <option key={value} value={value}>
                {incidentClassificationLabel(value)}
              </option>
            ))}
          </select>
        </div>

        {error && <p className="text-xs text-danger">{error}</p>}
      </div>
    </Modal>
  )
}
