export default function SubmitWizardPage() {
    return (
        <div className="space-y-3">
            <h1 className="text-xl font-semibold text-slate-900">New Request</h1>
            <p className="text-sm text-slate-600">
                This React wizard is wired for the new API layer; next step is adding POST endpoints to create cases and upload documents.
            </p>
            <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-700">
                For now, you can continue using the Django form at <span className="font-medium">/submit</span>.
            </div>
        </div>
    )
}
