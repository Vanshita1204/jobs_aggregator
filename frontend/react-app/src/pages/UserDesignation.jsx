import React, { useEffect, useState } from 'react'
import { request } from '../api'

export default function UserDesignation() {
    const [designationId, setDesignationId] = useState('')
    const [result, setResult] = useState(null)
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
        // backend expects user_designation_id as a query parameter, not in the JSON body
        const res = await request(`/user-designation?user_designation_id=${userDesignationId}`, { method: 'DELETE' })
        setResult(res)
        if (res.ok) setUserDesignations(prev => prev.filter(u => u.id !== userDesignationId))
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

            <pre className="result">{result && JSON.stringify(result, null, 2)}</pre>
        </section>
    )
}
