import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { request } from '../api'

export default function Login() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const navigate = useNavigate()

    async function submit(e) {
        e.preventDefault()
        setError('')
        const params = new URLSearchParams()
        params.append('username', username)
        params.append('password', password)
        const res = await request('/auth/login', { method: 'POST', body: params, auth: false })
        if (res.ok && res.data?.access_token) {
            localStorage.setItem('access_token', res.data.access_token)
            window.dispatchEvent(new Event('authchange'))
            navigate('/jobs')
        } else {
            setError(res.data?.detail || 'Login failed. Please check your credentials.')
        }
    }

    return (
        <section>
            <h2>Login</h2>
            <form onSubmit={submit}>
                <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Email" required />
                <input value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" type="password" required />
                <button type="submit">Login</button>
            </form>
            {error && <p className="msg-error">{error}</p>}
        </section>
    )
}
