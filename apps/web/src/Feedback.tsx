import {useEffect, useState} from 'react'
import type {FormEvent} from 'react'
import {ApiError, labels, request} from './api'
import type {components, paths} from './generated-api'

type State = components['schemas']['FeedbackState']
type Input = paths['/api/v1/drafts/{id}/feedback']['post']['requestBody']['content']['application/json']
type Category = NonNullable<components['schemas']['DraftView']['category']>
type Props = {draftId: string} & (
  | {show: 'analysis'; jobId: string; predicted?: Category; refreshDraft: () => Promise<void>}
  | {show: 'experience'}
)

export default function Feedback(props: Props) {
  const url = `/drafts/${props.draftId}/feedback`
  const expectedJob = props.show === 'analysis' ? props.jobId : undefined
  const [state, setState] = useState<State>()
  const [attempt, setAttempt] = useState(0)
  const [loadError, setLoadError] = useState(false)
  const [stale, setStale] = useState(false)
  const [pending, setPending] = useState<Input['kind']>()
  const [failure, setFailure] = useState<{kind: Input['kind']; message: string}>()

  useEffect(() => {
    const controller = new AbortController()
    request<State>(url, {signal: controller.signal}).then(result => {
      if (controller.signal.aborted) return
      if (expectedJob !== undefined && expectedJob !== result.job_id) setStale(true)
      else setState(result)
    }).catch(() => {
      if (!controller.signal.aborted) setLoadError(true)
    })
    return () => controller.abort()
  }, [url, expectedJob, attempt])

  function reloadStatus() {
    setState(undefined)
    setLoadError(false)
    setAttempt(value => value + 1)
  }

  async function submit(input: Input) {
    if (pending) return
    setPending(input.kind)
    setFailure(undefined)
    try {
      const saved = await request<State>(url, {method: 'POST', body: JSON.stringify(input)})
      if (expectedJob !== undefined && expectedJob !== saved.job_id) setStale(true)
      else setState(saved)
    } catch (error) {
      if (error instanceof ApiError && error.code === 'feedback_target_changed') setStale(true)
      else if (error instanceof ApiError && error.code === 'feedback_already_submitted') reloadStatus()
      else setFailure({kind: input.kind, message: error instanceof ApiError ? error.message : 'Could not save feedback. Please try again.'})
    } finally {
      setPending(undefined)
    }
  }

  function status(kind: Input['kind'], savedMessage: string) {
    if (state?.[kind] === 'submitted') return <p className="feedback-status" role="status">{savedMessage}</p>
    if (failure?.kind === kind) return <p className="feedback-error" role="alert">{failure.message}</p>
  }

  const loadStatus = loadError
    ? <p className="feedback-error" role="status">Feedback status could not be loaded. <button className="text-button" onClick={reloadStatus}>Retry</button></p>
    : <p className="feedback-status" role="status">Checking feedback…</p>

  if (props.show === 'experience') return (
    <details className="feedback experience-feedback">
      <summary>Rate CivicFix</summary>
      {!state && loadStatus}
      {state?.experience === 'open' && <ExperienceForm disabled={!!pending} submit={submit}/>}
      {status('experience', 'App rating saved.')}
    </details>
  )

  if (stale) return (
    <div className="feedback">
      <p className="feedback-status" role="status">The analysis has changed.</p>
      <button className="text-button" onClick={() => void props.refreshDraft()}>Refresh suggestions</button>
    </div>
  )

  return (
    <details className="feedback">
      <summary>Rate AI suggestions</summary>
      {!state && loadStatus}
      {(state?.classification === 'open' || state?.description === 'open') &&
        <p className="hint">Feedback stays on this computer for 30 days, even if you clear the draft.</p>}
      {state?.classification === 'open' && <ClassificationForm
        jobId={props.jobId} predicted={props.predicted} disabled={!!pending} submit={submit}
      />}
      {status('classification', 'Category feedback saved.')}
      {state?.description === 'open' && (
        <fieldset disabled={!!pending}>
          <legend>How was the suggested description?</legend>
          <div className="feedback-actions">
            <button className="secondary" onClick={() => void submit({kind: 'description', job_id: props.jobId, verdict: 'helpful'})}>Helpful</button>
            <button className="secondary" onClick={() => void submit({kind: 'description', job_id: props.jobId, verdict: 'inaccurate'})}>Inaccurate</button>
          </div>
        </fieldset>
      )}
      {status('description', 'Description feedback saved.')}
    </details>
  )
}

type FormProps = {disabled: boolean; submit: (input: Input) => Promise<void>}

function ClassificationForm({jobId, predicted, disabled, submit}: FormProps & {jobId: string; predicted?: Category}) {
  const [showCorrection, setShowCorrection] = useState(false)
  const [category, setCategory] = useState<Category | ''>('')

  function sendCorrection(event: FormEvent) {
    event.preventDefault()
    void submit({kind: 'classification', job_id: jobId, verdict: 'incorrect', suggested_category: category || null})
  }

  return (
    <form onSubmit={sendCorrection}>
      <fieldset disabled={disabled}>
        <legend>Was the suggested category correct?</legend>
        <div className="feedback-actions">
          <button type="button" className="secondary" onClick={() => void submit({kind: 'classification', job_id: jobId, verdict: 'correct'})}>Correct</button>
          <button type="button" className="secondary" aria-expanded={showCorrection} onClick={() => setShowCorrection(value => !value)}>Incorrect</button>
        </div>
        {showCorrection && <>
          <label>Suggest a category <small>Optional</small>
            <select value={category} onChange={event => setCategory(event.target.value as Category | '')}>
              <option value="">Choose a category</option>
              {Object.entries(labels).filter(([id]) => id !== predicted).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
            </select>
          </label>
          <button type="submit" className="secondary">Send category feedback</button>
        </>}
      </fieldset>
    </form>
  )
}

function ExperienceForm({disabled, submit}: FormProps) {
  const [rating, setRating] = useState('')
  const [comment, setComment] = useState('')

  function sendRating(event: FormEvent) {
    event.preventDefault()
    if (rating) void submit({kind: 'experience', rating: Number(rating), comment})
  }

  return (
    <form onSubmit={sendRating}>
      <fieldset disabled={disabled}>
        <label>How was your experience?
          <select required value={rating} onChange={event => setRating(event.target.value)}>
            <option value="">Choose a rating</option>
            <option value="1">1 — Very poor</option>
            <option value="2">2 — Poor</option>
            <option value="3">3 — Okay</option>
            <option value="4">4 — Good</option>
            <option value="5">5 — Very good</option>
          </select>
        </label>
        <label>Comment <small>Optional</small>
          <textarea rows={3} maxLength={500} value={comment} onChange={event => setComment(event.target.value)} aria-describedby="feedback-privacy"/>
        </label>
        <p className="hint" id="feedback-privacy">Feedback stays on this computer for 30 days, even if you clear the draft. Leave out names, addresses, and contact details.</p>
        <button type="submit" className="secondary" disabled={!rating}>Send app rating</button>
      </fieldset>
    </form>
  )
}
