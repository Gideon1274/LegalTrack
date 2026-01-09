export default function PublicTrackPage() {
    return (
        <div className="min-h-screen bg-slate-50">
            <div className="mx-auto max-w-xl px-4 py-12">
                <h1 className="text-2xl font-semibold text-slate-900">Track a Case</h1>
                <p className="mt-2 text-sm text-slate-600">
                    This page can call a public endpoint (e.g. <span className="font-medium">/api/public/track</span>) to show simplified status.
                </p>
                <div className="mt-6 rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-700">
                    For now, use the Django tracker at <span className="font-medium">/track</span>.
                </div>
            </div>
        </div>
    )
}
