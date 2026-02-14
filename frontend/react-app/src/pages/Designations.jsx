import React, { useEffect, useState } from 'react'
import { request } from '../api'

export default function Designations() {
    const [designations, setDesignations] = useState([])
    const [title, setTitle] = useState('')
    const [result, setResult] = useState(null)
    const [user, setUser] = useState(null)
    const [addedIds, setAddedIds] = useState(new Set())

    useEffect(() => {
        fetchData()
        fetchCurrentUser()
    }, [])

    async function fetchData() {
        // backend exposes POST /designation/list which returns list[DesignationRead]
        const res = await request('/designation/list', { method: 'POST', auth: false })
        if (res.ok && res.data) setDesignations(res.data)
        else setDesignations([])
    }

    async function fetchCurrentUser() {
        const res = await request('/auth/users/me', { method: 'GET' })
        if (res.ok && res.data) setUser(res.data)
    }

    async function createDesignation(e) {
        e.preventDefault()
        setResult(null)
        const res = await request('/designation/add', { method: 'POST', body: { title }, auth: true })
        setResult(res)
        if (res.ok && res.data && res.data.id) {
            // automatically add designation to current user
            if (user && user.id) {
                await addDesignationToUser(res.data.id)
            }
            await fetchData()
            setTitle('')
        }
    }

    async function addDesignationToUser(designationId) {
        const res = await request('/user-designation/add', { method: 'POST', body: { designation_id: designationId } })
        if (res.ok) {
            setAddedIds(prev => new Set(prev).add(designationId))
        }
        return res
    }

    async function handleAddClick(designationId) {
        if (!user || !user.id) {
            setResult({ ok: false, status: 401, text: 'Not logged in' })
            return
        }
        const res = await addDesignationToUser(designationId)
        setResult(res)
    }

    return (
        <section>
            <h2>Designations</h2>

            <form onSubmit={createDesignation}>
                <input value={title} onChange={e => setTitle(e.target.value)} placeholder="new designation title" required />
                <button type="submit">Create + Add to me</button>
            </form>

            <h3>Available designations</h3>
            <ul>
                {designations.map(d => (
                    <li key={d.id} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span>{d.title}</span>
                        <button onClick={() => handleAddClick(d.id)} disabled={addedIds.has(d.id)} style={{ marginLeft: 8 }}>
                            {addedIds.has(d.id) ? 'Added' : 'Add'}
                        </button>
                    </li>
                ))}
            </ul>

            <pre className="result">{result && JSON.stringify(result, null, 2)}</pre>
        </section>
    )
}
