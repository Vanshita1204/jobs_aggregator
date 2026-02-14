import React from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Register from './pages/Register'
import Login from './pages/Login'


export default function App() {
    return (
        <BrowserRouter>
            <div className="app">
                <header>
                    <h1>Jobs Aggregator</h1>
                    <nav>
                        <Link to="/">Home</Link> | <Link to="/register">Register</Link> |{' '}
                        <Link to="/login">Login</Link>
                    </nav>
                </header>
                <main>
                    <Routes>
                        <Route path="/" element={<Home />} />
                        <Route path="/register" element={<Register />} />
                        <Route path="/login" element={<Login />} />
                    </Routes>
                </main>
            </div>
        </BrowserRouter>
    )
}

function Home() {
    return <p>Use the nav to register/login and call protected endpoints.</p>
}
