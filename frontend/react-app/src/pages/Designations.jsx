import React, { useEffect, useState } from 'react'
import { request } from '../api'

export default function Designations() {
    const [designations, setDesignations] = useState([])
    const [userDesignations, setUserDesignations] = useState([])
    const [title, setTitle] = useState('')
    const [error, setError] = useState('')
    const [success, setSuccess] = useState('')
    const [titleError, setTitleError] = useState('')

    const userDesignationIds = new Set(userDesignations.map(ud => ud.designation_id))

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

        if (userRes.ok && userRes.data) setUserDesignations(userRes.data)
        else setUserDesignations([])
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
        if (res.ok) await fetchData()
        return res
    }

    async function removeDesignation(userDesignationId) {
        setError('')
        const res = await request(`/user-designation?user_designation_id=${userDesignationId}`, { method: 'DELETE' })
        if (res.ok) setUserDesignations(prev => prev.filter(ud => ud.id !== userDesignationId))
        else setError(res.data?.detail || 'Failed to remove designation.')
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

            <h3>Your designations</h3>
            {userDesignations.length === 0
                ? <p className="state-msg" style={{ padding: '12px 0' }}>None added yet.</p>
                : (
                    <ul>
                        {userDesignations.map(ud => {
                            const d = designations.find(x => x.id === ud.designation_id)
                            return (
                                <li key={ud.id}>
                                    <span>{d ? d.title : `#${ud.designation_id}`}</span>
                                    <button className="btn-danger" onClick={() => removeDesignation(ud.id)}>Remove</button>
                                </li>
                            )
                        })}
                    </ul>
                )
            }

            <h3>Available designations</h3>
            {availableDesignations.length === 0
                ? <p className="state-msg" style={{ padding: '12px 0' }}>All designations already added.</p>
                : (
                    <ul>
                        {availableDesignations.map(d => (
                            <li key={d.id}>
                                <span>{d.title}</span>
                                <button className="btn-secondary" onClick={() => handleAddClick(d.id)}>Add</button>
                            </li>
                        ))}
                    </ul>
                )
            }

            {error && <p className="msg-error">{error}</p>}
            {success && <p className="msg-success">{success}</p>}
        </section>
    )
}
