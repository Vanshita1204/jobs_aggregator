import React, { useEffect, useState } from 'react'
import { request } from '../api'

export default function Designations() {
    const [designations, setDesignations] = useState([])
    const [userDesignationIds, setUserDesignationIds] = useState(new Set())
    const [title, setTitle] = useState('')
    const [error, setError] = useState('')
    const [success, setSuccess] = useState('')
    const [titleError, setTitleError] = useState('')

    useEffect(() => {
        fetchData()
    }, [])

    async function fetchData() {
        const [allRes, userRes] = await Promise.all([
            request('/designation', { method: 'GET', auth: false }),
            request('/user-designation', { method: 'GET' }),
        ])

        if (allRes.ok && allRes.data) setDesignations(allRes.data)
        else setDesignations([])

        if (userRes.ok && userRes.data) {
            setUserDesignationIds(new Set(userRes.data.map(ud => ud.designation_id)))
        }
    }

    async function createDesignation(e) {
        e.preventDefault()
        setError('')
        setSuccess('')
        setTitleError('')

        const duplicate = designations.find(
            d => d.title.toLowerCase() === title.trim().toLowerCase()
        )
        if (duplicate) {
            setTitleError('A designation with this name already exists.')
            return
        }

        const res = await request('/designation', { method: 'POST', body: { title }, auth: true })
        if (res.ok && res.data && res.data.id) {
            await addDesignationToUser(res.data.id)
            await fetchData()
            setTitle('')
            setSuccess(`"${res.data.title}" created and added to your designations.`)
        } else {
            setError(res.data?.detail || 'Failed to create designation.')
        }
    }

    async function addDesignationToUser(designationId) {
        const res = await request('/user-designation', { method: 'POST', body: { designation_id: designationId } })
        if (res.ok) {
            setUserDesignationIds(prev => new Set(prev).add(designationId))
        }
        return res
    }

    async function handleAddClick(designationId) {
        setError('')
        setSuccess('')
        const res = await addDesignationToUser(designationId)
        if (!res.ok) {
            setError(res.data?.detail || 'Failed to add designation.')
        }
    }

    const availableDesignations = designations.filter(d => !userDesignationIds.has(d.id))

    return (
        <section>
            <h2>Designations</h2>

            <form onSubmit={createDesignation}>
                <input
                    list="designation-options"
                    value={title}
                    onChange={e => { setTitle(e.target.value); setTitleError('') }}
                    placeholder="new designation title"
                    required
                />
                <datalist id="designation-options">
                    {designations.map(d => <option key={d.id} value={d.title} />)}
                </datalist>
                <button type="submit">Create</button>
                {titleError && <span style={{ color: 'red', marginLeft: 8 }}>{titleError}</span>}
            </form>

            <h3>Available designations</h3>
            <ul>
                {availableDesignations.map(d => (
                    <li key={d.id} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span>{d.title}</span>
                        <button onClick={() => handleAddClick(d.id)} style={{ marginLeft: 8 }}>
                            Add
                        </button>
                    </li>
                ))}
            </ul>

            {error && <p className="msg-error">{error}</p>}
            {success && <p className="msg-success">{success}</p>}
        </section>
    )
}
