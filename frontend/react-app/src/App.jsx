import React, { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Link, NavLink } from 'react-router-dom'
import Register from './pages/Register'
import Login from './pages/Login'
import Designations from './pages/Designations'
import UserDesignation from './pages/UserDesignation'
import Jobs from './pages/Jobs'
import CVManager from './pages/CVManager'
import Settings from './pages/Settings'


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
                                    <NavLink to="/register">Register</NavLink>
                                    <NavLink to="/login">Login</NavLink>
                                </div>
                            )}
                            {loggedIn && (
                                <>
                                    <div className="nav-group">
                                        <NavLink to="/jobs" end>All Jobs</NavLink>
                                        <NavLink to="/jobs/saved">Saved</NavLink>
                                        <NavLink to="/jobs/applied">Applied</NavLink>
                                        <NavLink to="/jobs/interviewed">Interviewed</NavLink>
                                        <NavLink to="/jobs/rejected">Rejected</NavLink>
                                        <NavLink to="/jobs/irrelevant">Irrelevant</NavLink>
                                    </div>
                                    <div className="nav-divider" />
                                    <div className="nav-group">
                                        <NavLink to="/designations">Designations</NavLink>
                                        <NavLink to="/cvs">CVs</NavLink>
                                        <NavLink to="/settings">Settings</NavLink>
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
                        <Route path="/cvs" element={<CVManager />} />
                        <Route path="/settings" element={<Settings />} />
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
