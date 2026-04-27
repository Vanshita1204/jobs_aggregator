import React, { useEffect, useState } from 'react'

const PROVIDERS = ['groq', 'openai', 'anthropic', 'gemini']

const PROVIDER_LABELS = {
    groq: 'Groq (free default)',
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    gemini: 'Google Gemini',
}

export default function Settings() {
    const [provider, setProvider] = useState('groq')
    const [apiKey, setApiKey] = useState('')
    const [saved, setSaved] = useState(false)

    useEffect(() => {
        const storedProvider = localStorage.getItem('llm_provider') || 'groq'
        const storedKey = localStorage.getItem('llm_key') || ''
        setProvider(storedProvider)
        setApiKey(storedKey)
    }, [])

    function handleSave(e) {
        e.preventDefault()
        localStorage.setItem('llm_provider', provider)
        localStorage.setItem('llm_key', apiKey)
        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
    }

    function handleClear() {
        localStorage.removeItem('llm_provider')
        localStorage.removeItem('llm_key')
        setProvider('groq')
        setApiKey('')
        setSaved(false)
    }

    return (
        <section>
            <h2>Settings</h2>
            <h3>LLM Provider for CV Tips</h3>
            <p style={{ color: 'var(--muted)', fontSize: 14, marginBottom: 16 }}>
                Your API key is stored only in your browser and never sent to our servers.
                Leave blank to use the default Groq key.
            </p>
            <form onSubmit={handleSave}>
                <select value={provider} onChange={e => setProvider(e.target.value)}>
                    {PROVIDERS.map(p => (
                        <option key={p} value={p}>{PROVIDER_LABELS[p]}</option>
                    ))}
                </select>
                <input
                    type="password"
                    value={apiKey}
                    onChange={e => setApiKey(e.target.value)}
                    placeholder={provider === 'groq' ? 'Optional — leave blank to use default' : 'Paste your API key'}
                />
                <div style={{ display: 'flex', gap: 8 }}>
                    <button type="submit">Save</button>
                    <button type="button" className="btn-secondary" onClick={handleClear}>Clear</button>
                </div>
            </form>
            {saved && <p className="msg-success">Settings saved.</p>}
        </section>
    )
}
