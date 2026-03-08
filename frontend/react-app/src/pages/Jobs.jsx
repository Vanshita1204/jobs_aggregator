import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { request } from '../api'

const STATUS_LABELS = {
    applied: 'Applied',
    interviewed: 'Interviewed',
    rejected: 'Rejected',
    irrelevant: 'Irrelevant',
    saved: 'Saved',
}

const ACTION_STATUSES = [
    'applied',
    'interviewed',
    'rejected'
]

export default function Jobs() {
    const { status } = useParams()

    const [jobs, setJobs] = useState([])
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)
    const [filterJob, setFilterJob] = useState(null)
    const [showFilterModal, setShowFilterModal] = useState(false)
    const [filterStep, setFilterStep] = useState('choice') // 'choice' | 'keyword'
    const [keywordsInput, setKeywordsInput] = useState('')
    const [savingFilter, setSavingFilter] = useState(false)

    useEffect(() => {
        fetchJobs()
    }, [status])

    async function fetchJobs() {
        setLoading(true)
        setResult(null)

        let url = '/jobs'
        if (status) url += `?status=${status}`

        const res = await request(url, { method: 'GET' })

        if (res.ok && res.data) setJobs(res.data)
        else setResult(res)

        setLoading(false)
    }

    async function updateJobStatus(jobId, newStatus) {
        const res = await request('/user-jobs', {
            method: 'POST',
            body: {
                job_id: jobId,
                status: newStatus,
            },
        })

        if (res.ok) {
            setJobs(prev =>
                prev.map(job =>
                    job.id === jobId
                        ? { ...job, user_status: newStatus }
                        : job
                )
            )
        } else {
            setResult(res)
        }
    }
    async function handleIrrelevant(job) {

        // Step 1: mark job irrelevant
        const res = await request('/user-jobs', {
            method: 'POST',
            body: {
                job_id: job.id,
                status: 'irrelevant'
            }
        })

        if (!res.ok) {
            setResult(res)
            return
        }

        // optimistic UI update
        setJobs(prev =>
            prev.map(j =>
                j.id === job.id ? { ...j, user_status: 'irrelevant' } : j
            )
        )

        // Step 2: open filter modal to choose how to hide similar jobs
        setFilterJob(job)
        setFilterStep('choice')
        setKeywordsInput('')
        setShowFilterModal(true)
    }

    function closeFilterModal() {
        setShowFilterModal(false)
        setFilterJob(null)
        setFilterStep('choice')
        setKeywordsInput('')
        setSavingFilter(false)
    }

    async function handleTitleFilter() {
        if (!filterJob) return

        setSavingFilter(true)

        const res = await request('/user-job-preferences', {
            method: 'POST',
            body: {
                keyword: filterJob.title,
                is_excluded: true,
            },
        })

        if (!res.ok) {
            setResult(res)
        }

        setSavingFilter(false)
        closeFilterModal()
    }

    async function handleKeywordFilter() {
        if (!filterJob) return

        const trimmed = keywordsInput.trim()
        if (!trimmed) {
            return
        }

        setSavingFilter(true)

        const list = trimmed.split(',').map(k => k.trim()).filter(Boolean)

        for (const keyword of list) {
            const res = await request('/user-job-preferences', {
                method: 'POST',
                body: { keyword, is_excluded: true },
            })

            if (!res.ok) {
                setResult(res)
                // stop on first error
                break
            }
        }

        setSavingFilter(false)
        closeFilterModal()
    }

    function renderActions(job) {
        return (
            <div className="job-actions">

                {ACTION_STATUSES
                    .filter(s => s !== status) // hide action for current page
                    .map(s => (
                        <button
                            key={s}
                            className="btn-action"
                            disabled={job.user_status === s}
                            onClick={() => updateJobStatus(job.id, s)}
                        >
                            {STATUS_LABELS[s]}
                        </button>
                    ))}

                {status !== 'saved' && (
                    <button
                        className="btn-save"
                        onClick={() => updateJobStatus(job.id, 'saved')}
                    >
                        Save
                    </button>
                )}

                {status !== 'irrelevant' && (
                    <button
                        className="btn-danger"
                        onClick={() => handleIrrelevant(job)}
                    >
                        Irrelevant
                    </button>
                )}
            </div>
        )
    }

    return (
        <section>

            <div className="jobs-header">
                <h2>
                    {status
                        ? `${STATUS_LABELS[status]} Jobs`
                        : 'All Jobs'}
                </h2>

                <button onClick={fetchJobs} className="btn-refresh">
                    Refresh
                </button>
            </div>

            {loading && <p>Loading jobs…</p>}

            {!loading && jobs.length === 0 && (
                <p>No jobs found.</p>
            )}

            <ul className="jobs-list">

                {jobs.map(job => (
                    <li key={job.id} className="job-card">

                        <a
                            href={job.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="job-info"
                        >

                            <div className="job-title">
                                {job.title}
                            </div>

                            <div className="job-meta">
                                {job.company} • {job.location || 'Remote'}
                            </div>

                            <div className="job-source">
                                {job.source}
                            </div>

                            {job.user_status && (
                                <div className="job-status">
                                    {STATUS_LABELS[job.user_status]}
                                </div>
                            )}

                        </a>

                        {renderActions(job)}

                    </li>
                ))}

            </ul>

            {showFilterModal && filterJob && (
                <div
                    className="modal-backdrop"
                    style={{
                        position: 'fixed',
                        inset: 0,
                        background: 'transparent',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 1000,
                    }}
                >
                    <div
                        className="modal"
                        style={{
                            background: '#fff',
                            padding: '1.5rem 2rem',
                            borderRadius: '8px',
                            maxWidth: '480px',
                            width: '100%',
                            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.15)',
                        }}
                    >
                        <h3>Hide similar jobs?</h3>

                        {filterStep === 'choice' && (
                            <>
                                <p>Do you want to filter similar jobs in the future?</p>
                                <div
                                    className="modal-actions"
                                    style={{
                                        marginTop: '1rem',
                                        display: 'flex',
                                        gap: '0.75rem',
                                        flexWrap: 'wrap',
                                    }}
                                >
                                    <button
                                        className="btn-action"
                                        onClick={handleTitleFilter}
                                        disabled={savingFilter}
                                    >
                                        Hide jobs with this title
                                    </button>
                                    <button
                                        className="btn-action"
                                        onClick={() => setFilterStep('keyword')}
                                        disabled={savingFilter}
                                    >
                                        Use keywords instead
                                    </button>
                                    <button
                                        className="btn-secondary"
                                        onClick={closeFilterModal}
                                        disabled={savingFilter}
                                    >
                                        Skip
                                    </button>
                                </div>
                            </>
                        )}

                        {filterStep === 'keyword' && (
                            <>
                                <p>Enter keywords separated by commas to hide future jobs containing them.</p>
                                <input
                                    type="text"
                                    value={keywordsInput}
                                    onChange={e => setKeywordsInput(e.target.value)}
                                    placeholder="e.g. senior, manager, backend"
                                />
                                <div
                                    className="modal-actions"
                                    style={{
                                        marginTop: '1rem',
                                        display: 'flex',
                                        gap: '0.75rem',
                                        flexWrap: 'wrap',
                                    }}
                                >
                                    <button
                                        className="btn-action"
                                        onClick={handleKeywordFilter}
                                        disabled={savingFilter || !keywordsInput.trim()}
                                    >
                                        Save filters
                                    </button>
                                    <button
                                        className="btn-secondary"
                                        onClick={closeFilterModal}
                                        disabled={savingFilter}
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}

            {result && (
                <pre className="result">
                    {JSON.stringify(result, null, 2)}
                </pre>
            )}

        </section>
    )
}