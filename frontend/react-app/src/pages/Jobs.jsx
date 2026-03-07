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

export default function Jobs() {
    const { status } = useParams() // URL is the source of truth

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
        if (status) {
            url += `?status=${status}`
        }

        const res = await request(url, { method: 'GET' })

        if (res.ok && res.data) {
            setJobs(res.data)
        } else {
            setResult(res)
        }

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
            // Optimistic update
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

    return (
        <section>
            <div
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                }}
            >
                <h2>
                    {status
                        ? `${STATUS_LABELS[status]} Jobs`
                        : 'All Jobs'}
                </h2>

                <button onClick={fetchJobs} className="btn-ghost">
                    Refresh
                </button>
            </div>

            {loading && <p>Loading jobs…</p>}

            {!loading && jobs.length === 0 && (
                <p>No jobs found.</p>
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
                                {job.company} •{' '}
                                {job.location || 'Remote'}
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
                                            job.user_status ===
                                                'irrelevant'
                                                ? '#b42318'
                                                : 'var(--accent)',
                                    }}
                                >
                                    Status:{' '}
                                    {
                                        STATUS_LABELS[
                                        job.user_status
                                        ]
                                    }
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
                            {[
                                'applied',
                                'interviewed',
                                'rejected',
                            ].map(s => (
                                <button
                                    key={s}
                                    className="btn-ghost"
                                    disabled={
                                        job.user_status === s
                                    }
                                    onClick={() =>
                                        updateJobStatus(job.id, s)
                                    }
                                >
                                    {STATUS_LABELS[s]}
                                </button>
                            ))}

                            <button
                                className="btn-danger"
                                disabled={
                                    job.user_status === 'irrelevant'
                                }
                                onClick={() =>
                                    updateJobStatus(
                                        job.id,
                                        'irrelevant'
                                    )
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