import React, { useEffect, useRef, useState } from 'react'
import { request } from '../api'

const ACCEPTED = '.pdf,.docx,.txt'
const CONTENT_TYPES = {
    pdf: 'application/pdf',
    docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    txt: 'text/plain',
}

export default function CVManager() {
    const [cvs, setCvs] = useState([])
    const [name, setName] = useState('')
    const [file, setFile] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [error, setError] = useState('')
    const [success, setSuccess] = useState('')
    const fileRef = useRef()

    useEffect(() => { fetchCVs() }, [])

    async function fetchCVs() {
        const res = await request('/cvs', { method: 'GET' })
        if (res.ok && res.data) setCvs(res.data)
    }

    async function handleUpload(e) {
        e.preventDefault()
        if (!file) return
        setError('')
        setSuccess('')
        setUploading(true)

        const ext = file.name.rsplit ? file.name.split('.').pop() : file.name.split('.').pop()
        const contentType = CONTENT_TYPES[ext] || 'application/octet-stream'

        // 1. Get signed upload URL
        const urlRes = await request(
            `/cvs/upload-url?filename=${encodeURIComponent(file.name)}&content_type=${encodeURIComponent(contentType)}`,
            { method: 'GET' }
        )
        if (!urlRes.ok) {
            setError(urlRes.data?.detail || 'Failed to get upload URL.')
            setUploading(false)
            return
        }
        const { upload_url, gcs_path } = urlRes.data

        // 2. Upload directly to GCS (no auth header)
        try {
            const gcsRes = await fetch(upload_url, {
                method: 'PUT',
                headers: { 'Content-Type': contentType },
                body: file,
            })
            if (!gcsRes.ok) throw new Error(`GCS upload failed: ${gcsRes.status}`)
        } catch (err) {
            setError(`Upload to storage failed. This may be a CORS issue — check browser console. (${err.message})`)
            setUploading(false)
            return
        }

        // 3. Register with backend
        const res = await request('/cvs', {
            method: 'POST',
            body: { name, gcs_path },
        })
        if (res.ok) {
            setSuccess(`"${name}" uploaded successfully.`)
            setName('')
            setFile(null)
            if (fileRef.current) fileRef.current.value = ''
            await fetchCVs()
        } else {
            setError(res.data?.detail || 'Upload failed. Please try again.')
        }
        setUploading(false)
    }

    async function handleDelete(cvId, cvName) {
        setError('')
        const res = await request(`/cvs/${cvId}`, { method: 'DELETE' })
        if (res.ok) {
            setCvs(prev => prev.filter(c => c.id !== cvId))
            setSuccess(`"${cvName}" deleted.`)
        } else {
            setError(res.data?.detail || 'Failed to delete CV.')
        }
    }

    async function handleDownload(cvId) {
        setError('')
        const res = await request(`/cvs/${cvId}/download`, { method: 'GET' })
        if (res.ok && res.data?.download_url) {
            window.open(res.data.download_url, '_blank')
        } else {
            setError('Failed to get download link.')
        }
    }

    const generalCvs = cvs.filter(c => !c.user_job_id)
    const jobCvs = cvs.filter(c => c.user_job_id)

    return (
        <section>
            <h2>CV Manager</h2>

            <form onSubmit={handleUpload}>
                <input
                    value={name}
                    onChange={e => setName(e.target.value)}
                    placeholder="CV name (e.g. General Backend, Amazon Application)"
                    required
                />
                <input
                    ref={fileRef}
                    type="file"
                    accept={ACCEPTED}
                    onChange={e => setFile(e.target.files[0])}
                    required
                />
                <button type="submit" disabled={uploading}>
                    {uploading ? 'Uploading…' : 'Upload CV'}
                </button>
            </form>

            {error && <p className="msg-error">{error}</p>}
            {success && <p className="msg-success">{success}</p>}

            <h3>General CVs</h3>
            {generalCvs.length === 0
                ? <p className="state-msg">No general CVs yet.</p>
                : (
                    <ul>
                        {generalCvs.map(cv => (
                            <li key={cv.id}>
                                <span>{cv.name}</span>
                                <div style={{ display: 'flex', gap: 8 }}>
                                    <button className="btn-secondary" onClick={() => handleDownload(cv.id)}>Download</button>
                                    <button className="btn-danger" onClick={() => handleDelete(cv.id, cv.name)}>Delete</button>
                                </div>
                            </li>
                        ))}
                    </ul>
                )
            }

            {jobCvs.length > 0 && (
                <>
                    <h3>Job-Specific CVs</h3>
                    <ul>
                        {jobCvs.map(cv => (
                            <li key={cv.id}>
                                <span>
                                    {cv.name}
                                    <span style={{ color: 'var(--muted)', fontSize: 12 }}>
                                        {cv.job_title
                                            ? ` · ${cv.job_title}${cv.job_company ? ` @ ${cv.job_company}` : ''}`
                                            : ` · Job #${cv.user_job_id}`}
                                    </span>
                                </span>
                                <div style={{ display: 'flex', gap: 8 }}>
                                    <button className="btn-secondary" onClick={() => handleDownload(cv.id)}>Download</button>
                                    <button className="btn-danger" onClick={() => handleDelete(cv.id, cv.name)}>Delete</button>
                                </div>
                            </li>
                        ))}
                    </ul>
                </>
            )}
        </section>
    )
}
