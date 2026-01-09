import { useEffect, useState } from 'react'
import { me } from '../lib/auth.js'

export default function ProfilePage() {
    const [user, setUser] = useState(null)
    const [error, setError] = useState(null)

    useEffect(() => {
        me()
            .then(setUser)
            .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
    }, [])

    if (error) return <div className="text-sm text-red-700">{error}</div>
    if (!user) return <div className="text-sm text-slate-600">Loading…</div>

    return (
        <div className="space-y-4">
            <h1 className="text-xl font-semibold text-slate-900">Profile</h1>
            <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div>
                        <div className="text-xs text-slate-600">Name</div>
                        <div className="text-sm text-slate-900">{user.full_name || '—'}</div>
                    </div>
                    <div>
                        <div className="text-xs text-slate-600">Role</div>
                        <div className="text-sm text-slate-900">{user.role_label}</div>
                    </div>
                    <div>
                        <div className="text-xs text-slate-600">Email</div>
                        <div className="text-sm text-slate-900">{user.email}</div>
                    </div>
                    <div>
                        <div className="text-xs text-slate-600">Staff ID</div>
                        <div className="text-sm text-slate-900">{user.username}</div>
                    </div>
                </div>
                <div className="mt-4 text-sm text-slate-700">
                    Edit profile & password changes are handled in Django at <span className="font-medium">/profile</span>.
                </div>
            </div>
        </div>
    )
}
