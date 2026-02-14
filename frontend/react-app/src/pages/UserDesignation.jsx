import React, { useState } from 'react'
import { request } from '../api'

export default function UserDesignation() {
    const [designationId, setDesignationId] = useState('')
    const [result, setResult] = useState(null)

    async function submit(e) {
        e.preventDefault()
        // backend uses the current authenticated user (from token) and expects { designation_id }
        const res = await request('/user-designation/add', { method: 'POST', body: { designation_id: Number(designationId) } })
        setResult(res)
    }

    return (
        <section>
            <h2>Add Designation to Current User</h2>
            <form onSubmit={submit}>
                <input value={designationId} onChange={e => setDesignationId(e.target.value)} placeholder="designation id" required />
                <button type="submit">Add</button>
            </form>
            <pre className="result">{result && JSON.stringify(result, null, 2)}</pre>
        </section>
    )
}
