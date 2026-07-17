# Enterprise Operational Timeline — Architecture Review (Rev. 2)

**Pipeline today:** Simulation → Operational State → Compound Risk Engine (CRE-v1.0.0) → Recommendation Engine (REC-v1.0.0) → Frontend
**Rev 1:** 2026-07-15 · **Rev 2 (enhancement review):** 2026-07-16
**Grounded against:** `backend/app/models/event.py`, `services/risk.py`, `services/recommendation.py`, `models/recommendation.py`, `models/risk_snapshot.py`, `risk_engine/engine/confidence.py`, `risk_engine/engine/explain.py`

---

## R2. Enhancement review — eight proposals, evaluated

Priority throughout: **Enterprise Product > AI Demo.** Every "MVP" verdict below is either free (data already computed, just not persisted), a correction to a smell in Rev. 1's own design, or a direct reuse of a pattern this codebase already proved twice (CRE's pure-rules/persisted-service split, REC's template-generation/lifecycle split). Nothing here introduces a new class of engine, a new datastore, or ML.

### 1 · Alarm Layer — **RESERVED**

Real SCADA/OPC-UA alarms are point-level, stateful (ack/shelve/suppress), and independent of any aggregate risk score — a genuinely different concept from CRE's threshold rules, which today are embedded directly inside `ZoneFactsBuilder` → rule evaluation. The correct future seam is `ZoneFactsBuilder`: an alarm-aware facts builder would read from an Alarm store instead of live sensor rows, without touching CRE's rule logic at all. Nothing built today blocks that swap.

**Evidence the seam is already reserved:** `EventType.SENSOR_WARNING` / `SENSOR_CRITICAL` / `SENSOR_RECOVERED` already sit unused in the enum from a prior milestone. Leave them unwired — wiring them now would mean building per-sensor state tracking and dedup logic, which *is* a lightweight Alarm layer by another name. Document the reservation; write no code.

### 2 · Operational Story — **MVP**

Deterministic narrative generation over already-structured Incident/Event data is exactly REC's own precedent (`RULE_TEMPLATE_MAP`) and CRE's `generate_explanation()` — not a new class of engine, just a third application of a pattern already shipped twice.

**Where it fits:** an **Incident Summary**, produced by a pure function (`correlation_engine/narrative.py`, no I/O — same shape as `risk_engine/engine/explain.py`) and run at each lifecycle transition (open/escalate/resolve/close) to populate `Incident.summary`. Not a Timeline projection (would recompute identically on every read for no benefit) and not attached to individual Timeline entries (a story belongs to an incident's scope, not a page of chronological rows). Keep the template count small: a fixed three-slot structure — trigger clause (top risk contributor) + response clause (top recommendation + who acknowledged) + outcome clause (duration + resolution) — no open-ended composition.

### 3 · Incident Severity vs. Risk Severity — **MVP**

Genuinely distinct axes, worth the one-field cost. Risk Severity is a computed hazard/potential-danger metric, frozen per `RiskSnapshot`. Incident Severity is assessed real-world impact — which requires human judgment, because injury/downtime/cost data doesn't exist in this system and shouldn't be algorithmically guessed.

**Add:** `Incident.incident_severity` — an operator-set enum, required at `close` only when `classification = reportable_incident`, using the exact same required-before-close gating already designed for `root_cause`. **Explicitly reject** any automatic derivation (e.g. inferring severity from response time) — an algorithm silently downgrading how serious an incident was is precisely the wrong instinct for a compliance-facing field.

### 4 · Causal Graph — **MVP (schema correction) + RESERVED (graph store)**

Evaluating this surfaced a real smell in Rev. 1's own data model: `Incident.linked_recommendation_ids` as a denormalized array is a second source of truth that has to be kept in sync by hand — exactly the kind of embedded-list shortcut this codebase has otherwise avoided (Recommendation's own JSONB columns are used only for frozen/read-only fields, never for a live relationship).

**Fix (MVP):** flip it to `Recommendation.incident_id` (nullable FK) — a real edge, one recommendation belongs to at most one open incident. **Add (MVP):** `Recommendation.triggering_snapshot_id` (nullable FK → `risk_snapshots`) — the missing explicit edge between a specific frozen assessment and the recommendation it produced, populated from whichever snapshot is current for the zone at reconcile time (CRE only persists on meaningful change, so this is "nearest known," not always exact-tick — still a real, walkable edge). Together with the Rev. 1 `Event.incident_id`/`risk_snapshot_id`, the full chain Sensor → Rule → Snapshot → Recommendation → Incident → Operator Action becomes FK-walkable today.

**Reserved, not built:** any graph storage or graph-query layer. Ordinary foreign keys are sufficient at this data volume, and a graph store buys nothing without enough incident history to mine — same reasoning as Rev. 1 §02.

### 5 · Timeline Composer Views — **MVP (generic composer) + RESERVED (extra endpoints)**

`Event` already has `equipment_id`/`permit_id`/`recorded_by_id` — Plant/Zone/Incident were a UX priority choice for v1, never a schema limitation.

**MVP:** design `composer.py` around *one* parameterized filter (zone / incident / equipment / worker / permit all optional dimensions on the same query) instead of three hand-rolled functions. This is less code today, not more — the three v1 views are the same query with different `WHERE` clauses, so parameterizing costs nothing extra and avoids a near-certain near-term rewrite.

**Reserved:** the equipment/worker/permit *endpoints* themselves. No frontend page needs them yet, and shipping unused API surface is exactly the speculative scope this project's own conventions warn against. Adding a thin endpoint later is trivial once composer.py already supports the filter.

### 6 · Event Confidence — **REJECTED (already covered)**

`RiskAssessment`/`RiskSnapshot` already carries `confidence_score`/`confidence_label`, computed by `risk_engine/engine/confidence.py` — this reservation already exists and predates this review. Once `Event.risk_snapshot_id` exists (Rev. 1, §04), any event's confidence is one join away.

**Reject** adding a duplicate `confidence` column to `Event`, `Recommendation`, or `Incident` — that would be the identical denormalization mistake just corrected in #4. Document the existing field as the reserved seam for degraded-sensor scenarios; no schema change needed.

### 7 · Correlation Engine — **MVP (structural split) + RESERVED (merge)**

Correct, and it's the same pure-decision / stateful-persistence split this codebase already ships twice: `risk_engine` (pure rules) vs. `RiskService` (persistence); `recommendation_engine/generator.py` (pure candidates) vs. `RecommendationService` (lifecycle). Rev. 1's folder plan buried a pure `correlation.py` *inside* an `incident_manager/` wrapper package — a naming inconsistency against the sibling convention, and it under-names the part actually doing the reasoning.

**Fix:** promote it to its own top-level package, `correlation_engine/` (pure, no I/O — decides open/attach/escalate/reopen/resolve), exactly parallel to `risk_engine/` and `recommendation_engine/`. "Incident Manager" remains the right product-level name for the capability as a whole, but on disk it decomposes the same way "Recommendation Engine" already does: a pure engine package plus plain `models/services/incident.py` (no manager wrapper needed, matching that recommendations don't have a "recommendation_manager" package either).

**Reserved, not built:** `merge` as a decision type. No current scenario (single-zone simulator, no cross-zone cascading incident) needs it, and merging is genuinely complex — reassigning event ownership, reconciling conflicting severities, auditing the merge itself. Keep the schema merge-friendly (nothing today precludes a future `Incident.merged_into_id` self-FK) without building the logic.

### 8 · Operational Context Snapshot — **MVP**

Almost free. At the exact moment the Correlation Engine decides to open an incident, it already holds the `ZoneFacts`/`RiskAssessment` that drove that decision — workers, equipment, sensors, permits, contributors — in memory. The only new work is persisting it instead of discarding it.

**Add:** one JSONB column, `Incident.opened_context_snapshot`, populated directly from the already-computed assessment at open time — same JSONB precedent as `RiskSnapshot.contributors`. **Reject** a dedicated "Snapshot Service" or normalized child tables for this — that would turn a nearly-free capture into a new subsystem for no benefit at MVP scale.

---

## 00. Verdict: yes, Incident Manager belongs here — with three corrections

**Your instinct is right and matches real platforms.** Honeywell Forge, AVEVA, Maximo-adjacent CMMS, and PI Vision all separate ephemeral signals (alarms, recommendations) from a durable, ownable unit of accountability (an incident/work order). A raw event log or a bare timeline has no owner, no status, and nothing to close. Recommendations already prove this in your own system — they resolve individually and independently, but nothing represents "the zone's overall episode." That's the gap Incident Manager fills.

### 1. Timeline is not a child feature Incident Manager "owns" — it's a peer read layer

Your diagram nests Timeline under Incident Manager's bullet list. That's right for an *incident-scoped* timeline (its own chronological view), but Reports, Analytics, RAG, and RCA all need to query *across* incidents — and need to see activity from zones that never had an incident open. Model it as: Incident Manager owns write-side state (open/track/resolve/close); Timeline is an independent read/query service that composes Events, Incidents, Recommendations, and Risk snapshots into one narrative, at three zoom levels (plant, zone, incident). Full case in §02.

### 2. "Incident" is doing two jobs — split the concept, not necessarily the table

In a refinery, "incident" carries regulatory weight: OSHA-recordable, spill, injury, near-miss. What your diagram's auto-detected, algorithm-opened episodes actually are is closer to "a zone was in elevated risk from 14:02 to 14:19 and here's what happened" — most resolve uneventfully and should never reach a compliance auditor's desk. One `incidents` table, but with an `origin` (system_detected / manual) and `classification` (operational_episode / near_miss / safety_incident / reportable_incident) field, so the same lifecycle machinery serves both without inventing a second entity now. Detail in §04.

### 3. Round 2 refinement — the pure decision logic is a named engine, not a wrapper

**[MVP]** Per §R2.7: "Incident Manager" is the product-level capability. Underneath it, exactly like Risk and Recommendation before it, the reasoning lives in its own pure package — `correlation_engine/` — and the persistence/API/lifecycle shell is the thinner, plainly-named `services/incident.py` layer around it.

With that, the flow is: **Simulation → Operational State → CRE → Recommendation Engine → Correlation Engine (decides) → Incident lifecycle (persists) → Timeline (reads) → Reports / Analytics / AI**.

---

## 01. Critique of the current architecture

Grounded in the actual code, not the diagram.

### What's already right — keep it

- An `events` table already exists, and its own docstring already says the quiet part out loud: *"the future Incident Timeline module is a filtered/sorted view over this table, not a separate one."* Today's Timeline design honors that commitment rather than reinventing it.
- CRE's change-gated persistence (write a `RiskSnapshot` only when level changes or score moves >10 points) is the correct discipline for a safety event log, and Timeline inherits it rather than re-deriving its own noise filter.
- Recommendation Engine's stable `identity_key` + auto-resolve-on-reconcile pattern is a proto-incident lifecycle at the single-condition level. Correlation Engine does the same thing one level up — see §R2.7.

### What's missing — found by reading the code, not guessing

- **Risk level transitions never emit an Event.** `RiskService.evaluate()` writes a `RiskSnapshot` row on meaningful change but never touches `EventRepository`.
- **Recommendation creation never emits an Event.** `RecommendationService.reconcile()` only writes Events on `acknowledge()` and `resolve()` — no `RECOMMENDATION_CREATED`.
- **Nothing represents a bounded episode.** Recommendations resolve individually; nothing lets an operator say "that's over now" about the zone as a whole.
- **No operator-authored narrative.** Every event today is system-generated; no way to log a note or declare an incident the sensors never saw (a slip-and-fall has no risk rule behind it).

---

## 02. Better architectural alternatives

### Reframe: this is an event-sourcing read-model problem, not a "build a timeline" problem

The write-side sources of truth are `Event` (atomic facts), `RiskSnapshot` (assessments), `Recommendation` (condition lifecycle), and `Incident` (correlated lifecycle). **Timeline is a materialized read-model / projection over those streams — it has no authority of its own.** This is what makes future modules cheap: Reports is another projection; RAG embeds projected narrative chunks; RCA traverses the same stream as a causal chain; a Knowledge Graph is a later promotion of the same typed relationships, not a rewrite — reinforced in Round 2 by making those relationships explicit FKs now (§R2.4).

### Should this be a Knowledge Graph from day one instead of a timeline?

No — premature for the same reason CRE stayed deterministic instead of ML-based: a graph store pays for itself once there's enough incident history to mine cross-incident patterns, which doesn't exist yet. Build the relational version now with explicit typed foreign keys (never free text) so "promote to a graph later" is a translation, not a re-architecture.

### Is "Incident Manager" the best name, or does it undersell what's needed?

**[MVP]** Round 2 sharpened this (§R2.7): the function is a **Correlation Engine** — deciding which signals belong to the same unfolding situation, when it starts and ends — with Incident Manager as the thinner lifecycle/persistence shell around it. Same relationship as CRE's rules vs. its service, REC's generator vs. its service.

---

## 03. Timeline philosophy

**The Timeline is the platform's memory** — a deterministic, append-mostly narrative substrate that answers what happened, in what order, why, and what was done about it, at three zoom levels: plant, zone, and incident.

### The questions it must answer

| Operator question | What answers it |
|---|---|
| What's unresolved right now, and since when? | Open `Incident` rows, sorted by `opened_at` |
| What happened this shift — was it handled? | Timeline filtered to a time window, grouped by incident |
| Why is this zone in this state? | Causal chain: risk level change → recommendation created → acknowledged → action → resolved |
| What actually happened, in plain language? | **[MVP]** Incident Summary — a deterministic narrative, not just a row list (§R2.2) |
| Who acted, when, how fast? | Actor-tagged events (system vs. operator) with timestamps — substrate for future MTTA/MTTR |
| Has this happened before? | Same zone + same rule/category across closed incidents (feeds §10's Similar Incident Search) |

### Noise principle

Log **state transitions and human actions**, never raw measurements or unchanged ticks — CRE's own snapshot-gating discipline, inherited rather than reinvented.

| Tier | Examples | Treatment |
|---|---|---|
| **Permanent, high-signal** | Incident opened/escalated/resolved/closed · risk level transitions · ESD activate/clear · recommendation created/acknowledged/resolved · permit violations · operator overrides | Always logged, immutable, never sampled away |
| **Contextual, collapsed by default** | Minor score movement within the same level · routine permit issuance in a normal zone · routine equipment cycling | Logged, hidden behind "show more" — retained for analytics, not narrated by default |
| **Never logged as discrete rows** | Raw per-tick sensor readings · every scheduler tick regardless of change | Telemetry, not history — belongs in a timeseries store once real sensors replace the simulator |

### Permanent vs. ephemeral

Once written, a Timeline entry is **never edited or deleted.** Corrections are new entries that reference the one they correct — the same posture RiskSnapshot already takes. Retention/archival is an operations decision made later, not a modeling compromise made now.

---

## 04. Data model

One new table (`incidents`), targeted extensions to `events` and `recommendations`, still **no new table for the Timeline itself.**

### `Incident` — new

```
id                       uuid
primary_zone_id          fk → zones
affected_zone_ids        list[uuid]
status                   enum                # open | resolved | closed
origin                   enum                # system_detected | manual
classification           enum                # operational_episode | near_miss | safety_incident | reportable_incident
risk_severity_at_open     risk level enum      # renamed from severity_at_open — §R2.3, disambiguated from incident_severity
peak_risk_severity        risk level enum      # renamed from peak_severity — same reason
incident_severity         severity enum | null # NEW — §R2.3: operator-assessed actual impact, required at close only when classification = reportable_incident
title                    str
summary                  str                  # now populated by correlation_engine/narrative.py, not just a stub — §R2.2
opened_context_snapshot   jsonb | null         # NEW — §R2.8: ZoneFacts/RiskAssessment as already computed at open decision time
opened_at / resolved_at / closed_at   datetime | null
root_cause               str | null           # required before close, only when classification = reportable_incident
corrective_actions        list[str]
opened_by_id / closed_by_id   fk → workers | null
```

`linked_recommendation_ids` (Rev. 1) is **removed** — replaced by `Recommendation.incident_id`, a real edge instead of a synced array (§R2.4).

### Incident lifecycle

```
OPEN → RESOLVED → CLOSED
```

**OPEN → RESOLVED** is automatic, same as recommendation auto-resolve. **RESOLVED → CLOSED** is a deliberate human confirmation step, gated on `root_cause` and now `incident_severity` (Round 2) when `classification = reportable_incident` — mirrors ServiceNow's own resolved-vs-closed split. **Reserved:** a `merged_into_id` self-FK, for a future `merge` decision (§R2.7) — not built now, schema left compatible with adding it later.

**Implementation correction (post-review):** the partial unique index is still `unique on (primary_zone_id) filtered to status = 'open'`, but recurrence does **not** reopen a resolved-not-closed row — it always opens a brand-new `Incident`, exactly mirroring the Recommendation Engine's own fix for the identical problem (a resolved row can legitimately recur; the fix there was a fresh row per recurrence, never reusing the old one). An earlier draft of this design had decide() "reopen" the most recent resolved-not-closed incident for the zone; an implementation-time code review caught that this conflates causally-unrelated episodes (an unrelated equipment fault hours later would reopen an old, already-closed-in-spirit gas-hazard incident) and corrupts its `opened_at`-based duration narrative. Resolved-not-closed incidents simply sit there awaiting an operator's `close()`; a new qualifying condition, related or not, always gets its own row.

### `Recommendation` — extend (Round 2 additions)

```
incident_id             fk → incidents, nullable   # NEW — §R2.4: the real edge that replaced Incident.linked_recommendation_ids
triggering_snapshot_id  fk → risk_snapshots, nullable  # NEW — §R2.4: explicit edge from "which frozen assessment" to "which recommendation"
```

### `Event` — extend (unchanged from Rev. 1; Round 2 confirmed no further fields needed)

```
incident_id       fk → incidents, nullable
risk_snapshot_id  fk → risk_snapshots, nullable   # also now the seam that carries confidence — §R2.6, no duplicate column added
actor_type        enum: system | operator
actor_id          fk → workers, nullable
severity          enum: info|notice|warning|critical
```

---

## 05. Event model

Events remain immutable and append-only. Two Rev. 1 additions still stand unchanged after Round 2 review:

- **Actor model** — `actor_type: system | operator` distinguishes "the engine detected this" from "a person did this."
- **Correlation** — `incident_id` is nullable on purpose; not every event belongs to an incident.

**Rejected:** a per-event `confidence` column (proposed in Round 2 §R2.6) — redundant once `risk_snapshot_id` exists, since `RiskSnapshot.confidence_score` is already one join away. Adding it would duplicate a source of truth, the same mistake corrected elsewhere in this revision.

---

## 06. Event taxonomy

Reuse CRE's existing 7 categories for filtering; two cross-cutting additions for platform bookkeeping: `INCIDENT_LIFECYCLE` and `OPERATOR_ACTION`.

| Value | Fires from | Fills which gap |
|---|---|---|
| `risk_level_increased` / `risk_level_decreased` | `RiskService.evaluate()`, at its existing persist-gate | §01 — level transitions currently invisible |
| `recommendation_created` | `RecommendationService.reconcile()`, on insert | §01 — creation currently unlogged |
| `incident_opened` / `_escalated` / `_resolved` / `_closed` | Correlation Engine lifecycle decisions | The new correlation layer |
| `incident_note_added` | Operator free-text note | Operator-authored narrative, currently absent |

**Reserved, unwired:** `sensor_warning` / `sensor_critical` / `sensor_recovered` — already in the enum, deliberately left unwired per §R2.1's Alarm Layer reservation.

---

## 07. Storage strategy

- **Same Postgres instance, no new datastore** — Round 2 reinforced this twice over (rejecting both a graph store in §R2.4 and any new confidence infrastructure in §R2.6).
- JSONB precedent now covers three cases: `RiskSnapshot.contributors`, `Recommendation.expected_outcomes`, and the new `Incident.opened_context_snapshot` (§R2.8) — all frozen-at-write-time facts, never a live relationship.
- **Retention: permanent for Incidents and Tier-1 events.** Raw telemetry never enters this store, now or later.
- **Indexing**: `(zone_id, occurred_at)` and `(incident_id)` on events; partial unique index on `incidents(primary_zone_id)` where `status = 'open'` — the same tool that fixed Recommendation's real recurring-key bug.

---

## 08. API design

### Incident lifecycle (write-side)

| Endpoint | Purpose |
|---|---|
| `GET /incidents` | List, filter by zone / status / classification |
| `GET /incidents/{id}` | Detail — linked recommendations (via `Recommendation.incident_id`), its own bounded timeline, and its narrative summary |
| `POST /incidents` | Manual declare — the path for incidents the sensors never saw |
| `POST /incidents/{id}/notes` | Operator free-text note |
| `POST /incidents/{id}/escalate` | Reclassify (e.g. operational_episode → reportable_incident) |
| `POST /incidents/{id}/close` | Requires `root_cause` + `incident_severity` when classification = reportable_incident |

### Timeline (read-side)

**[MVP]** Per §R2.5: `composer.py` is one parameterized query (optional zone / incident / equipment / worker / permit filters), not three copies. Only these are exposed as endpoints in v1:

| Endpoint | Purpose |
|---|---|
| `GET /timeline/plant` | Cross-zone feed, incident-first grouping |
| `GET /timeline/zones/{id}` | Full zone chronology, Tier-2 collapsed client-side |
| `GET /timeline/incidents/{id}` | Bounded narrative for one incident, including its Incident Summary |

**Reserved:** `/timeline/equipment/{id}`, `/timeline/workers/{id}`, `/timeline/permits/{id}` — trivial to add later since `composer.py` already supports the filter; no frontend page needs them yet.

**Cursor-based pagination** (`occurred_at` + `id`), not offset — this is an append-only log under concurrent writes.

---

## 09. Frontend experience

- **Plant Timeline** — cross-zone feed, incidents surfaced first.
- **Zone Timeline** — full chronology, Tier-2 noise collapsed, severity stripes, actor icons.
- **Incident Detail** — bounded timeline, linked recommendations, resolution/root-cause fields, **plus its generated Operational Story rendered as the header narrative** (§R2.2) above the raw event rows — the human-readable summary first, the chronological detail below it.

Reuse the Recommendation Engine's existing "ACTION REQUIRED" danger-tinted card treatment for the top-priority open incident, rather than inventing a new severity vocabulary.

---

## 10. Future extensibility

| Future module | How this architecture serves it |
|---|---|
| Alarm Layer | **Reserved.** Plugs into `ZoneFactsBuilder` when real SCADA/OPC-UA replaces the simulator — §R2.1 |
| Incident merge | **Reserved.** Schema left compatible with a future `merged_into_id` self-FK — §R2.7 |
| Equipment / Worker / Permit Timeline | **Reserved.** `composer.py` already supports the filter dimension — §R2.5 |
| Incident Reports | Formal export/freeze of a `closed`, `reportable_incident` Incident — now backed by both `root_cause` and `incident_severity` (§R2.3) |
| Shift Reports | A Timeline query scoped to a time window + operator, auto-summarized |
| Weekly Analytics | Aggregation over Incident/Event tables — counts by category/zone/severity, MTTA/MTTR |
| AI Assistant / RAG | Incident Summaries (§R2.2) are the retrievable chunks — already narrative-shaped, not raw rows to re-parse |
| Similar Incident Search | Nearest-neighbor over Incident feature vectors — feasible because contributors/rules/severity are structured fields, not prose |
| Knowledge Graph | A projection of the FK edges strengthened in §R2.4, not a rewrite |
| Root Cause Analysis | Authored into `root_cause`/`corrective_actions`, informed by `opened_context_snapshot` (§R2.8) for "what did the plant look like then" |
| Compliance Audits | Filter to `reportable_incident` + `closed`, both `root_cause` and `incident_severity` enforced at close-time |

---

## 11. Folder structure

Round 2 correction: promoted the pure decision layer to its own top-level package, matching the `risk_engine/` / `recommendation_engine/` sibling convention exactly (§R2.7) — no more `incident_manager/` wrapper.

```
backend/app/
  correlation_engine/       # pure, no I/O — mirrors risk_engine/ and recommendation_engine/
    decide.py               # open / keep_open / resolve (merge: reserved, not built; recurrence always opens fresh, never reopens)
    narrative.py            # NEW — deterministic Incident Summary, same shape as risk_engine/engine/explain.py
    config.py               # thresholds

  models/incident.py
  repositories/incident.py
  services/incident.py      # calls correlation_engine.decide + narrative, persists results
  schemas/incident.py
  api/v1/endpoints/incidents.py

  models/recommendation.py  # + incident_id, triggering_snapshot_id (§R2.4)

  timeline/                 # read-only — no models.py, no new table
    composer.py             # one parameterized filter (zone/incident/equipment/worker/permit) — §R2.5
  schemas/timeline.py
  api/v1/endpoints/timeline.py

  models/event.py           # incident_id, risk_snapshot_id, actor_type, actor_id, severity
  schemas/event.py           # new EventType values
```

---

## 12. Implementation plan

**Phase 0 — Event plumbing.** New nullable columns on `events`; wire the two missing emit points from §01 — `risk_level_increased`/`_decreased` at CRE's existing persist-gate, `recommendation_created` on insert. Also lands here: `Recommendation.triggering_snapshot_id` (no dependency on the incidents table existing yet). Zero new business logic.

**Phase 1 — Correlation Engine + Incident lifecycle.** `correlation_engine/decide.py` (open on risk crossing into elevated / critical-priority recommendation / ESD activation; auto-resolve on reconcile) + `correlation_engine/narrative.py` (Incident Summary, §R2.2) + `Incident` model including `incident_severity` and `opened_context_snapshot` (§R2.3, §R2.8) + `Recommendation.incident_id` (§R2.4) + manual create/note/escalate/close endpoints.

**Phase 2 — Timeline composer.** Single parameterized read service (§R2.5) merging the four streams into `TimelineEntry` DTOs; plant/zone/incident endpoints only; cursor pagination; incident-first grouping.

**Phase 3 — Frontend.** Plant timeline feed, zone timeline tab, incident detail panel — narrative summary rendered above the raw chronology (§R2.2) — plus note/escalate/close actions.

**Later.** Reports/Analytics as further projections; RAG/RCA/Knowledge Graph once there's closed-incident history; Alarm Layer once real SCADA/OPC-UA ingestion replaces the simulator; incident `merge` if a scenario ever needs it. Explicitly not now.
