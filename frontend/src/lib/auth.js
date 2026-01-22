import { apiFetch } from './api'

export async function ensureCsrf() {
    await apiFetch('/api/csrf/', { method: 'GET' })
}

export async function login(identifier, password) {
    await ensureCsrf()
    return apiFetch('/api/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier, password }),
    })
}

export async function logout() {
    await ensureCsrf()
    await apiFetch('/api/auth/logout/', { method: 'POST' })
}

export async function me() {
    return apiFetch('/api/me/', { method: 'GET' })
}
