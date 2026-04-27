import React, { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { request } from '../api'

const CONTENT_TYPES = {
    pdf: 'application/pdf',
    docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    txt: 'text/plain',
}

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
    const [error, setError] = useState('')
    const [filterJob, setFilterJob] = useState(null)
    const [showFilterModal, setShowFilterModal] = useState(false)
    const [filterStep, setFilterStep] = useState('choice') // 'choice' | 'keyword'
    const [keywordsInput, setKeywordsInput] = useState('')
    const [savingFilter, setSavingFilter] = useState(false)

    // CV Tips state
    const [cvs, setCvs] = useState([])
    const [tipsJob, setTipsJob] = useState(null)
    const [selectedCvId, setSelectedCvId] = useState('')
    const [tips, setTips] = useState('')
    const [tipsLoading, setTipsLoading] = useState(false)
    const [tipsError, setTipsError] = useState('')
    const [jobDescription, setJobDescription] = useState('')
    const [descLoading, setDescLoading] = useState(false)

    // Attach CV state
    const [attachCvJob, setAttachCvJob] = useState(null)
    const [attachCvName, setAttachCvName] = useState('')
    const [attachCvFile, setAttachCvFile] = useState(null)
    const [attachCvUploading, setAttachCvUploading] = useState(false)
    const [attachCvError, setAttachCvError] = useState('')
    const [attachCvSuccess, setAttachCvSuccess] = useState('')
    const attachCvFileRef = useRef()

    useEffect(() => {
        fetchJobs()
        fetchCVs()
    }, [status])

    async function fetchCVs() {
        const res = await request('/cvs', { method: 'GET' })
        if (res.ok && res.data) setCvs(res.data)
    }

    async function fetchJobs() {
        setLoading(true)
        setError('')

        let url = '/jobs'
        if (status) url += `?status=${status}`

        const res = await request(url, { method: 'GET' })

        if (res.ok && res.data) setJobs(res.data)
        else setError(res.data?.detail || 'Failed to load jobs.')

        setLoading(false)
    }
    async function fetchNewJobs() {
        setLoading(true)
        setError('')

        const res = await request('/jobs/fetch-new', { method: 'POST' })

        if (!res.ok) {
            setError(res.data?.detail || 'Failed to trigger job fetch.')
            setLoading(false)
            return
        }

        // Give scraper some time to insert jobs
        setTimeout(fetchJobs, 3000)

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
                        ? { ...job, user_status: newStatus, user_job_id: res.data.id }
                        : job
                )
            )
        } else {
            setError(res.data?.detail || 'Failed to update job status.')
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
            setError(res.data?.detail || 'Failed to mark job as irrelevant.')
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
            setError(res.data?.detail || 'Failed to save filter.')
        }

        setSavingFilter(false)
        closeFilterModal()
    }

    async function handleKeywordFilter() {
        if (!filterJob) return

        const trimmed = keywordsInput.trim()
        if (!trimmed) return

        setSavingFilter(true)

        const list = trimmed.split(',').map(k => k.trim()).filter(Boolean)

        for (const keyword of list) {
            const res = await request('/user-job-preferences', {
                method: 'POST',
                body: { keyword, is_excluded: true },
            })

            if (!res.ok) {
                setError(res.data?.detail || 'Failed to save filter.')
                break
            }
        }

        setSavingFilter(false)
        closeFilterModal()
    }

    function openAttachCvModal(job) {
        setAttachCvJob(job)
        setAttachCvName('')
        setAttachCvFile(null)
        setAttachCvError('')
        setAttachCvSuccess('')
    }

    function closeAttachCvModal() {
        setAttachCvJob(null)
        setAttachCvName('')
        setAttachCvFile(null)
        setAttachCvError('')
        setAttachCvSuccess('')
        setAttachCvUploading(false)
        if (attachCvFileRef.current) attachCvFileRef.current.value = ''
    }

    async function handleAttachCv(e) {
        e.preventDefault()
        if (!attachCvFile || !attachCvJob) return
        setAttachCvUploading(true)
        setAttachCvError('')
        setAttachCvSuccess('')

        const ext = attachCvFile.name.split('.').pop().toLowerCase()
        const contentType = CONTENT_TYPES[ext] || 'application/octet-stream'

        const urlRes = await request(
            `/cvs/upload-url?filename=${encodeURIComponent(attachCvFile.name)}&content_type=${encodeURIComponent(contentType)}`,
            { method: 'GET' }
        )
        if (!urlRes.ok) {
            setAttachCvError(urlRes.data?.detail || 'Failed to get upload URL.')
            setAttachCvUploading(false)
            return
        }
        const { upload_url, gcs_path } = urlRes.data

        try {
            const gcsRes = await fetch(upload_url, {
                method: 'PUT',
                headers: { 'Content-Type': contentType },
                body: attachCvFile,
            })
            if (!gcsRes.ok) throw new Error(`GCS upload failed: ${gcsRes.status}`)
        } catch (err) {
            setAttachCvError(`Upload to storage failed: ${err.message}`)
            setAttachCvUploading(false)
            return
        }

        const res = await request('/cvs', {
            method: 'POST',
            body: { name: attachCvName, gcs_path, user_job_id: attachCvJob.user_job_id },
        })
        if (res.ok) {
            setAttachCvSuccess('CV attached successfully.')
            await fetchCVs()
            setTimeout(closeAttachCvModal, 1500)
        } else {
            setAttachCvError(res.data?.detail || 'Failed to attach CV.')
        }
        setAttachCvUploading(false)
    }

    async function openTipsModal(job) {
        setTipsJob(job)
        setSelectedCvId(cvs.length > 0 ? String(cvs[0].id) : '')
        setTips('')
        setTipsError('')
        setJobDescription('')
        setDescLoading(true)
        const res = await request(`/jobs/${job.id}/description`, { method: 'GET' })
        if (res.ok) setJobDescription(res.data?.description || '')
        setDescLoading(false)
    }

    function closeTipsModal() {
        setTipsJob(null)
        setTips('')
        setTipsError('')
        setTipsLoading(false)
        setJobDescription('')
        setDescLoading(false)
    }

    async function handleGetTips() {
        if (!selectedCvId) return
        setTipsLoading(true)
        setTipsError('')
        setTips('')

        const provider = localStorage.getItem('llm_provider') || 'groq'
        const llmKey = localStorage.getItem('llm_key') || ''

        const res = await request(`/cvs/${selectedCvId}/tips/${tipsJob.id}`, {
            method: 'POST',
            body: null,
            auth: true,
            extraHeaders: {
                'x-llm-provider': provider,
                'x-llm-key': llmKey,
            },
        })

        if (res.ok && res.data?.tips) {
            setTips(res.data.tips)
        } else {
            setTipsError(res.data?.detail || 'Failed to get CV tips.')
        }
        setTipsLoading(false)
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

                {cvs.length > 0 && (
                    <button
                        className="btn-tips"
                        onClick={() => openTipsModal(job)}
                    >
                        CV Tips
                    </button>
                )}

                {job.user_job_id && (
                    <button
                        className="btn-secondary"
                        onClick={() => openAttachCvModal(job)}
                    >
                        Attach CV
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

            <div className="jobs-header-actions">
                {!status && (
                    <button onClick={fetchNewJobs} className="btn-fetch-new">
                        Fetch New
                    </button>
                )}

                <button onClick={fetchJobs} className="btn-refresh">
                    Refresh
                </button>
            </div>
        </div>

            {loading && <p className="state-msg">Loading jobs…</p>}

            {!loading && jobs.length === 0 && (
                <p className="state-msg">No jobs found.</p>
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

                            {!status && job.is_new && (
                                <span className="job-new-badge">
                                    NEW
                                </span>
                            )}
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

            {error && <p className="msg-error">{error}</p>}

            {/* CV Tips modal */}
            {tipsJob && (
                <div className="modal-backdrop">
                    <div className="modal" style={{ maxWidth: 600, maxHeight: '85vh', overflowY: 'auto' }}>
                        <h3>CV Tips for {tipsJob.title}</h3>
                        <p style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 12 }}>{tipsJob.company}</p>

                        {/* Job description */}
                        <div style={{ marginBottom: 16 }}>
                            <label style={{ fontSize: 13, fontWeight: 600 }}>Job Description</label>
                            {descLoading
                                ? <p style={{ fontSize: 13, color: 'var(--muted)' }}>Fetching description…</p>
                                : jobDescription
                                    ? (
                                        <div style={{
                                            marginTop: 6,
                                            padding: '10px 12px',
                                            background: 'var(--surface, #f5f5f5)',
                                            borderRadius: 6,
                                            fontSize: 13,
                                            whiteSpace: 'pre-wrap',
                                            maxHeight: 200,
                                            overflowY: 'auto',
                                        }}>
                                            {jobDescription}
                                        </div>
                                    )
                                    : <p style={{ fontSize: 13, color: 'var(--muted)' }}>No description available for this source.</p>
                            }
                        </div>

                        {!tips && (
                            <>
                                <label style={{ fontSize: 13, fontWeight: 600 }}>Select CV</label>
                                <select
                                    value={selectedCvId}
                                    onChange={e => setSelectedCvId(e.target.value)}
                                    style={{ marginTop: 6 }}
                                >
                                    {cvs.map(cv => (
                                        <option key={cv.id} value={cv.id}>{cv.name}</option>
                                    ))}
                                </select>
                                {tipsError && <p className="msg-error">{tipsError}</p>}
                                <div className="modal-actions" style={{ marginTop: 16, display: 'flex', gap: 8 }}>
                                    <button onClick={handleGetTips} disabled={tipsLoading || !selectedCvId}>
                                        {tipsLoading ? 'Generating…' : 'Get Tips'}
                                    </button>
                                    <button className="btn-secondary" onClick={closeTipsModal}>Cancel</button>
                                </div>
                            </>
                        )}

                        {tips && (
                            <>
                                <label style={{ fontSize: 13, fontWeight: 600 }}>Tips</label>
                                <div className="tips-content" style={{ marginTop: 6 }}>
                                    {tips.split('\n').filter(Boolean).map((line, i) => (
                                        <p key={i} style={{ margin: '6px 0', fontSize: 14 }}>{line}</p>
                                    ))}
                                </div>
                                <div className="modal-actions" style={{ marginTop: 16, display: 'flex', gap: 8 }}>
                                    <button className="btn-secondary" onClick={() => setTips('')}>Try another CV</button>
                                    <button className="btn-secondary" onClick={closeTipsModal}>Close</button>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}

            {/* Attach CV modal */}
            {attachCvJob && (
                <div className="modal-backdrop">
                    <div className="modal" style={{ maxWidth: 480 }}>
                        <h3>Attach CV to {attachCvJob.title}</h3>
                        <p style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 12 }}>{attachCvJob.company}</p>
                        {attachCvSuccess
                            ? <p className="msg-success">{attachCvSuccess}</p>
                            : (
                                <form onSubmit={handleAttachCv}>
                                    <input
                                        value={attachCvName}
                                        onChange={e => setAttachCvName(e.target.value)}
                                        placeholder="CV name (e.g. Amazon Backend Application)"
                                        required
                                    />
                                    <input
                                        ref={attachCvFileRef}
                                        type="file"
                                        accept=".pdf,.docx,.txt"
                                        onChange={e => setAttachCvFile(e.target.files[0])}
                                        required
                                    />
                                    {attachCvError && <p className="msg-error">{attachCvError}</p>}
                                    <div className="modal-actions" style={{ marginTop: 16, display: 'flex', gap: 8 }}>
                                        <button type="submit" disabled={attachCvUploading}>
                                            {attachCvUploading ? 'Uploading…' : 'Upload & Attach'}
                                        </button>
                                        <button type="button" className="btn-secondary" onClick={closeAttachCvModal}>
                                            Cancel
                                        </button>
                                    </div>
                                </form>
                            )
                        }
                    </div>
                </div>
            )}

        </section>
    )
}