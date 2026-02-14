import React, { useEffect, useState } from 'react'
import { request } from '../api'

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
        if (res.ok && res.data) setJobs(res.data)
        else setResult(res)
        setLoading(false)
    }

    return (
        <section>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2>Jobs</h2>
                <div>
                    <button onClick={fetchJobs} className="btn-ghost">Refresh</button>
                </div>
            </div>

            {loading && <p>Loading jobs…</p>}

            {!loading && jobs.length === 0 && <p>No jobs found for your designations.</p>}

            <ul>
                {jobs.map(job => (
                    <li key={job.id}>
                        <a href={job.source_url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: 'inherit', display: 'flex', gap: 12, alignItems: 'center', width: '100%' }}>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontWeight: 600 }}>{job.title}</div>
                                <div style={{ color: 'var(--muted)', marginTop: 6 }}>{job.company} • {job.location || 'Remote'}</div>
                            </div>
                            <div style={{ textAlign: 'right', minWidth: 120 }}>
                                <div style={{ fontSize: 12, color: 'var(--muted)' }}>{job.source}</div>
                                <div style={{ marginTop: 6 }}><button className="btn-ghost">Open</button></div>
                            </div>
                        </a>
                    </li>
                ))}
            </ul>

            <pre className="result">{result && JSON.stringify(result, null, 2)}</pre>
        </section>
    )
}
