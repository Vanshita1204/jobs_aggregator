import React, { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Register from './pages/Register'
import Login from './pages/Login'
import Designations from './pages/Designations'
import UserDesignation from './pages/UserDesignation'
import Jobs from './pages/Jobs'


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
                    <div className="header-inner">
                        <Link to="/" className="header-logo">Jobs Aggregator</Link>
                        <nav>
                            {!loggedIn && (
                                <div className="nav-group">
                                    <Link to="/register">Register</Link>
                                    <Link to="/login">Login</Link>
                                </div>
                            )}
                            {loggedIn && (
                                <>
                                    <div className="nav-group">
                                        <Link to="/designations">Add Designation</Link>
                                        <Link to="/user-designation">My Designations</Link>
                                    </div>
                                    <div className="nav-divider" />
                                    <div className="nav-group">
                                        <Link to="/jobs">All</Link>
                                        <Link to="/jobs/saved">Saved</Link>
                                        <Link to="/jobs/applied">Applied</Link>
                                        <Link to="/jobs/interviewed">Interviewed</Link>
                                        <Link to="/jobs/rejected">Rejected</Link>
                                        <Link to="/jobs/irrelevant">Irrelevant</Link>
                                    </div>
                                    <div className="nav-divider" />
                                    <button
                                        className="nav-logout"
                                        onClick={() => {
                                            localStorage.removeItem('access_token')
                                            setLoggedIn(false)
                                            window.dispatchEvent(new Event('authchange'))
                                        }}
                                    >
                                        Logout
                                    </button>
                                </>
                            )}
                        </nav>
                    </div>
                </header>
                <main>
                    <Routes>
                        <Route path="/" element={<Home />} />
                        <Route path="/register" element={<Register />} />
                        <Route path="/login" element={<Login />} />
                        <Route path="/designations" element={<Designations />} />
                        <Route path="/user-designation" element={<UserDesignation />} />
                        <Route path="/jobs" element={<Jobs />} />
                        <Route path="/jobs/:status" element={<Jobs />} />
                    </Routes>
                </main>
            </div>
        </BrowserRouter>
    )
}

function Home() {
    return (
        <div className="home-placeholder">
            <h2>Welcome to Jobs Aggregator</h2>
            <p>Login to browse and track job listings from LinkedIn and Hirist.</p>
        </div>
    )
}
