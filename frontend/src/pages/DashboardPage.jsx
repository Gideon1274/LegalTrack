import { useEffect, useState } from 'react'
import { apiFetch } from '../lib/api.js'
import { Link } from 'react-router-dom'

export default function DashboardPage() {
    const [items, setItems] = useState([])
    const [error, setError] = useState(null)

    useEffect(() => {
        apiFetch('/api/cases/?limit=20')
            .then((d) => setItems(d.results ?? []))
            .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
    }, [])

    return (
        <div className="space-y-4">
            <h1 className="text-xl font-semibold text-slate-900">Dashboard</h1>
            {error && <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

            <div className="rounded-lg border border-slate-200 bg-white">
                <div className="border-b border-slate-200 px-4 py-3 text-sm font-medium text-slate-900">Recent cases</div>
                <div className="divide-y divide-slate-100">
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
                    {items.length === 0 && <div className="px-4 py-6 text-sm text-slate-600">No cases found.</div>}
                </div>
            </div>
        </div>
    )
}
