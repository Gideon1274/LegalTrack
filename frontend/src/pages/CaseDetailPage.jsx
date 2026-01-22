import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { apiFetch } from '../lib/api.js'

export default function CaseDetailPage() {
    const { trackingId } = useParams()
    const [data, setData] = useState(null)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (!trackingId) return
        apiFetch(`/api/cases/${encodeURIComponent(trackingId)}/`)
            .then(setData)
            .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
    }, [trackingId])

    if (error) return <div className="text-sm text-red-700">{error}</div>
    if (!data) return <div className="text-sm text-slate-600">Loading…</div>

    return (
        <div className="space-y-4">
            <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="flex items-start justify-between gap-4">
                    <div>
                        <h1 className="text-xl font-semibold text-slate-900">{data.tracking_id}</h1>
                        <div className="text-sm text-slate-700">{data.client_display_name}</div>
                        <div className="text-xs text-slate-500">{data.case_type_label}</div>
                    </div>
                    <div className="text-right">
                        <div className="text-xs text-slate-600">Status</div>
                        <div className="text-sm font-medium text-slate-900">{data.status_label}</div>
                    </div>
                </div>

                <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div className="rounded-md border border-slate-200 p-3">
                        <div className="text-xs text-slate-600">Client contact</div>
                        <div className="text-sm text-slate-900">
                            {(data.client_number || '—') + ' / ' + (data.client_email || '—')}
                        </div>
                    </div>
                    <div className="rounded-md border border-slate-200 p-3">
                        <div className="text-xs text-slate-600">Number</div>
                        <div className="text-sm text-slate-900">{data.numbering_number ?? '—'}</div>
                    </div>
                </div>

                {data.return_reason && (
                    <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-3">
                        <div className="text-xs font-medium text-amber-900">Return reason</div>
                        <div className="text-sm text-amber-900">{data.return_reason}</div>
                    </div>
                )}
            </div>

            <div className="rounded-lg border border-slate-200 bg-white">
                <div className="border-b border-slate-200 px-4 py-3 text-sm font-medium text-slate-900">Checklist</div>
                <div className="divide-y divide-slate-100">
                    {(data.checklist ?? []).map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between px-4 py-3">
                            <div className="text-sm text-slate-900">{item.doc_type}</div>
                            <div className="text-xs text-slate-600">{item.uploaded ? 'Uploaded' : 'Missing'}</div>
                        </div>
                    ))}
                    {(data.checklist ?? []).length === 0 && (
                        <div className="px-4 py-6 text-sm text-slate-600">No checklist items.</div>
                    )}
                </div>
            </div>
        </div>
    )
}
