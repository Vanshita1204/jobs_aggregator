import React, { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Register from './pages/Register'
import Login from './pages/Login'
import Designations from './pages/Designations'
import UserDesignation from './pages/UserDesignation'


export default function App() {
    const [loggedIn, setLoggedIn] = useState(!!localStorage.getItem('access_token'))

    useEffect(() => {
        function onAuthChange() {
            setLoggedIn(!!localStorage.getItem('access_token'))
        }
        window.addEventListener('authchange', onAuthChange)
        return () => window.removeEventListener('authchange', onAuthChange)
    }, [])

    return (
        <BrowserRouter>
            <div className="app">
                <header>
                    <h1>Jobs Aggregator</h1>
                    <nav>
                        <Link to="/">Home</Link>
                        {!loggedIn && (
                            <>
                                | <Link to="/register">Register</Link> |{' '}
                                <Link to="/login">Login</Link>
                            </>
                        )}
                        {loggedIn && (
                            <>
                                {' '}| <Link to="/designations">Add Designation</Link> |{' '}
                                <Link to="/user-designation">Manage User Designation</Link> |{' '}
                                <Link to="/jobs">List Jobs</Link>
                                | <button onClick={() => { localStorage.removeItem('access_token'); setLoggedIn(false); window.dispatchEvent(new Event('authchange')) }}>Logout</button>
                            </>
                        )}
                    </nav>
                </header>
                <main>
                    <Routes>
                        <Route path="/" element={<Home />} />
                        <Route path="/register" element={<Register />} />
                        <Route path="/login" element={<Login />} />
                        <Route path="/designations" element={<Designations />} />
                        <Route path="/user-designation" element={<UserDesignation />} />
                    </Routes>
                </main>
            </div>
        </BrowserRouter>
    )
}

function Home() {
    return <p>Use the nav to register/login and call protected endpoints.</p>
}
