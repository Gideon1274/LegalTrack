import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Button from '../components/Button.jsx'
import { login } from '../lib/auth.js'

export default function LoginPage() {
    const [identifier, setIdentifier] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState(null)
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    async function onSubmit(e) {
        e.preventDefault()
        setError(null)
        setLoading(true)
        try {
            await login(identifier, password)
            navigate('/dashboard')
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Login failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-slate-50">
            <div className="mx-auto flex max-w-md flex-col gap-4 px-4 py-12">
                <h1 className="text-2xl font-semibold text-slate-900">Sign in</h1>
                <p className="text-sm text-slate-600">Use Staff ID (or admin email) + password.</p>

                <form onSubmit={onSubmit} className="rounded-lg border border-slate-200 bg-white p-4">
                    <label className="block text-sm font-medium text-slate-800">Staff ID / Email</label>
                    <input
                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                        autoComplete="username"
                        value={identifier}
                        onChange={(e) => setIdentifier(e.target.value)}
                        required
                    />

                    <label className="mt-3 block text-sm font-medium text-slate-800">Password</label>
                    <input
                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                        type="password"
                        autoComplete="current-password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />

                    {error && <div className="mt-3 text-sm text-red-700">{error}</div>}

                    <div className="mt-4 flex items-center justify-end">
                        <Button type="submit" disabled={loading}>
                            {loading ? 'Signing in…' : 'Sign in'}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    )
}
