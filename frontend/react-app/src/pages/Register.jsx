import React, { useState } from 'react'
import { request } from '../api'

export default function Register() {
    const [email, setEmail] = useState('')
    const [fullName, setFullName] = useState('')
    const [password, setPassword] = useState('')
    const [result, setResult] = useState(null)

    async function submit(e) {
        e.preventDefault()
        const res = await request('/auth/register', { method: 'POST', body: { email, full_name: fullName, password }, auth: false })
        setResult(res)
    }

    return (
        <section>
            <h2>Register</h2>
            <form onSubmit={submit}>
                <input value={email} onChange={e => setEmail(e.target.value)} placeholder="email" required />
                <input value={fullName} onChange={e => setFullName(e.target.value)} placeholder="full name" required />
                <input value={password} onChange={e => setPassword(e.target.value)} placeholder="password" type="password" required />
                <button type="submit">Register</button>
            </form>
            <pre className="result">{result && JSON.stringify(result, null, 2)}</pre>
        </section>
    )
}
