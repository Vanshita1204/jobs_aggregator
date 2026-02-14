import React, { useState } from 'react'
import { request } from '../api'

export default function Login() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [result, setResult] = useState(null)

    async function submit(e) {
        e.preventDefault()
        const params = new URLSearchParams()
        params.append('username', username)
        params.append('password', password)
        // oauth2 password form expects form-encoded data
        const res = await request('/auth/login', { method: 'POST', body: params, auth: false })
        if (res.ok && res.data && res.data.access_token) {
            localStorage.setItem('access_token', res.data.access_token)
            setResult({ ok: true, token: res.data.access_token })
        } else {
            setResult(res)
        }
    }

    return (
        <section>
            <h2>Login</h2>
            <form onSubmit={submit}>
                <input value={username} onChange={e => setUsername(e.target.value)} placeholder="email" required />
                <input value={password} onChange={e => setPassword(e.target.value)} placeholder="password" type="password" required />
                <button type="submit">Login</button>
            </form>
            <div>
                <button onClick={() => { localStorage.removeItem('access_token'); setResult({ ok: true, message: 'Logged out' }) }}>Logout</button>
            </div>
            <pre className="result">{result && JSON.stringify(result, null, 2)}</pre>
        </section>
    )
}
