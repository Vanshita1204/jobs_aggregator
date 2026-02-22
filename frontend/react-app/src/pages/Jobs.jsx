import React, { useEffect, useState } from 'react'
import { request } from '../api'

const STATUS_LABELS = {
    applied: 'Applied',
    interviewed: 'Interviewed',
    rejected: 'Rejected',
    irrelevant: 'Irrelevant',
}

export default function Jobs() {
    const [jobs, setJobs] = useState([])
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)

    useEffect(() => {
        fetchJobs()
    }, [])

    async function fetchJobs() {
        setLoading(true)
        setResult(null)

        const res = await request('/jobs/list', { method: 'GET' })
        if (res.ok && res.data) {
            setJobs(res.data)
        } else {
            setResult(res)
        }

        setLoading(false)
    }

    async function updateJobStatus(jobId, status) {
        const res = await request('/user-jobs', {
            method: 'POST',
            body: {
                job_id: jobId,
                status,
            },
        })

        if (res.ok) {
            // optimistic update
            setJobs(prev =>
                prev.map(job =>
                    job.id === jobId
                        ? { ...job, user_status: status }
                        : job
                )
            )
        } else {
            setResult(res)
        }
    }

    return (
        <section>
            <div
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                }}
            >
                <h2>Jobs</h2>
                <button onClick={fetchJobs} className="btn-ghost">
                    Refresh
                </button>
            </div>

            {loading && <p>Loading jobs…</p>}

            {!loading && jobs.length === 0 && (
                <p>No jobs found for your designations.</p>
            )}

            <ul style={{ listStyle: 'none', padding: 0 }}>
                {jobs.map(job => (
                    <li
                        key={job.id}
                        style={{
                            display: 'flex',
                            gap: 16,
                            padding: 12,
                            borderBottom: '1px solid var(--border)',
                        }}
                    >
                        {/* Job info */}
                        <a
                            href={job.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                                flex: 1,
                                textDecoration: 'none',
                                color: 'inherit',
                            }}
                        >
                            <div style={{ fontWeight: 600 }}>
                                {job.title}
                            </div>

                            <div
                                style={{
                                    color: 'var(--muted)',
                                    marginTop: 6,
                                }}
                            >
                                {job.company} • {job.location || 'Remote'}
                            </div>

                            <div
                                style={{
                                    fontSize: 12,
                                    marginTop: 4,
                                    color: 'var(--muted)',
                                }}
                            >
                                {job.source}
                            </div>

                            {job.user_status && (
                                <div
                                    style={{
                                        marginTop: 6,
                                        fontSize: 12,
                                        fontWeight: 500,
                                        color:
                                            job.user_status === 'irrelevant'
                                                ? '#b42318'
                                                : 'var(--accent)',
                                    }}
                                >
                                    Status: {STATUS_LABELS[job.user_status]}
                                </div>
                            )}
                        </a>

                        {/* Status actions */}
                        <div
                            style={{
                                display: 'flex',
                                flexDirection: 'column',
                                gap: 6,
                                minWidth: 120,
                            }}
                        >
                            {['applied', 'interviewed', 'rejected'].map(
                                status => (
                                    <button
                                        key={status}
                                        className="btn-ghost"
                                        disabled={
                                            job.user_status === status
                                        }
                                        onClick={() =>
                                            updateJobStatus(job.id, status)
                                        }
                                    >
                                        {STATUS_LABELS[status]}
                                    </button>
                                )
                            )}

                            <button
                                className="btn-danger"
                                disabled={job.user_status === 'irrelevant'}
                                onClick={() =>
                                    updateJobStatus(job.id, 'irrelevant')
                                }
                            >
                                Irrelevant
                            </button>
                        </div>
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