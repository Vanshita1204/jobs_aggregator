import React, { useEffect, useState } from 'react'
import { request } from '../api'

export default function UserDesignation() {
    const [error, setError] = useState('')
    const [designations, setDesignations] = useState([])
    const [userDesignations, setUserDesignations] = useState([])

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


    async function deleteById(userDesignationId) {
        setError('')
        const res = await request(`/user-designation?user_designation_id=${userDesignationId}`, { method: 'DELETE' })
        if (res.ok) {
            setUserDesignations(prev => prev.filter(u => u.id !== userDesignationId))
        } else {
            setError(res.data?.detail || 'Failed to remove designation.')
        }
    }

    return (
        <section>
            <h3>Your designations</h3>
            <ul>
                {userDesignations.map((ud, idx) => {
                    const d = designations.find(x => x.id === ud.designation_id)
                    return (
                        <li key={idx + 1} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <span>{idx + 1}: {d ? d.title : ud.designation_id}</span>
                            <button onClick={() => deleteById(ud.id)} style={{ marginLeft: 8 }}>Delete</button>
                        </li>
                    )
                })}
            </ul>

            {error && <p className="msg-error">{error}</p>}
        </section>
    )
}
