const API_BASE = 'http://localhost:8000/api/v1'

async function request(path, { method = 'GET', body = null, auth = true } = {}) {
    const headers = {}
    let payload = null
    // Support JSON bodies, FormData and URLSearchParams (for form-encoded login)
    if (body instanceof FormData || body instanceof URLSearchParams) {
        // let fetch set appropriate Content-Type (multipart/form-data or application/x-www-form-urlencoded)
        payload = body
    } else if (body) {
        headers['Content-Type'] = 'application/json'
        payload = JSON.stringify(body)
    }
    if (auth) {
        const token = localStorage.getItem('access_token')
        if (token) headers['Authorization'] = 'Bearer ' + token
    }

    const res = await fetch(API_BASE + path, { method, headers, body: payload })
    const text = await res.text()
    try {
        return { ok: res.ok, status: res.status, data: JSON.parse(text) }
    } catch (e) {
        return { ok: res.ok, status: res.status, text }
    }
}

export { request }
