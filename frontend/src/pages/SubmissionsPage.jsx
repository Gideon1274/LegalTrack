import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../lib/api.js'

export default function SubmissionsPage() {
    const [q, setQ] = useState('')
    const [items, setItems] = useState([])
    const [error, setError] = useState(null)

    useEffect(() => {
        const qs = new URLSearchParams()
        if (q.trim()) qs.set('q', q.trim())

        apiFetch(`/api/cases/?${qs.toString()}`)
            .then((d) => setItems(d.results ?? []))
            .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
    }, [q])

    return (
        <div className="space-y-4">
            <div className="flex items-end justify-between gap-3">
                <div>
                    <h1 className="text-xl font-semibold text-slate-900">Submissions</h1>
                    <p className="text-sm text-slate-600">Search by tracking ID, client, email, or number.</p>
                </div>
                <input
                    className="w-full max-w-sm rounded-md border border-slate-300 px-3 py-2"
                    placeholder="Search…"
                    value={q}
                    onChange={(e) => setQ(e.target.value)}
                />
            </div>

            {error && <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

            <div className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
                {items.map((c) => (
                    <Link
                        key={c.tracking_id}
                        to={`/cases/${encodeURIComponent(c.tracking_id)}`}
                        className="block px-4 py-3 hover:bg-slate-50"
                    >
                        <div className="flex items-center justify-between">
                            <div className="text-sm font-medium text-slate-900">{c.tracking_id}</div>
                            <div className="text-xs text-slate-600">{c.status_label}</div>
                        </div>
                        <div className="text-sm text-slate-700">{c.client_display_name}</div>
                        <div className="text-xs text-slate-500">{c.case_type_label}</div>
                    </Link>
                ))}
                {items.length === 0 && <div className="px-4 py-6 text-sm text-slate-600">No matches.</div>}
            </div>
        </div>
    )
}
