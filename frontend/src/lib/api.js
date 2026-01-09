function getCookie(name) {
    const value = `; ${document.cookie}`
    const parts = value.split(`; ${name}=`)
    if (parts.length === 2) return parts.pop().split(';').shift() ?? null
    return null
}

export async function apiFetch(path, init) {
    const baseUrl = import.meta.env.VITE_API_BASE_URL ?? ''
    const url = `${baseUrl}${path}`

    const headers = new Headers(init?.headers)
    headers.set('Accept', 'application/json')

    const method = (init?.method ?? 'GET').toUpperCase()
    const isWrite = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)
    if (isWrite) {
        const csrf = getCookie('csrftoken')
        if (csrf) headers.set('X-CSRFToken', csrf)
    }

    const res = await fetch(url, {
        credentials: 'include',
        ...init,
        headers,
    })

    if (!res.ok) {
        let message = `${res.status} ${res.statusText}`
        try {
            const data = await res.json()
            if (data?.detail) message = data.detail
        } catch {
            // ignore
        }
        throw new Error(message)
    }

    return await res.json()
}
