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
                        onClick={() => updateJobStatus(job.id, 'irrelevant')}
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

            {result && (
                <pre className="result">
                    {JSON.stringify(result, null, 2)}
                </pre>
            )}

        </section>
    )
}