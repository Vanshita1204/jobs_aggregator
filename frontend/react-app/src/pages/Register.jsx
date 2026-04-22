import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { request } from '../api'

export default function Register() {
    const [email, setEmail] = useState('')
    const [fullName, setFullName] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [success, setSuccess] = useState('')
    const navigate = useNavigate()

    async function submit(e) {
        e.preventDefault()
        setError('')
        setSuccess('')
        const res = await request('/auth/register', { method: 'POST', body: { email, full_name: fullName, password }, auth: false })
        if (res.ok) {
            setSuccess('Account created successfully. Redirecting to login…')
            setTimeout(() => navigate('/login'), 1500)
        } else {
            setError(res.data?.detail || 'Registration failed. Please try again.')
        }
    }

    return (
        <section>
            <h2>Register</h2>
            <form onSubmit={submit}>
                <input value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" required />
                <input value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Full name" required />
                <input value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" type="password" required />
                <button type="submit">Create account</button>
            </form>
            {error && <p className="msg-error">{error}</p>}
            {success && <p className="msg-success">{success}</p>}
        </section>
    )
}
