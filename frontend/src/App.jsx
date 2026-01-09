import { Route, Routes, Navigate } from 'react-router-dom'
import Shell from './components/Shell.jsx'
import LoginPage from './pages/LoginPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import SubmissionsPage from './pages/SubmissionsPage.jsx'
import CaseDetailPage from './pages/CaseDetailPage.jsx'
import SubmitWizardPage from './pages/SubmitWizardPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import PublicTrackPage from './pages/PublicTrackPage.jsx'

export default function App() {
    return (
        <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/track" element={<PublicTrackPage />} />

            <Route element={<Shell />}>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/submissions" element={<SubmissionsPage />} />
                <Route path="/submit" element={<SubmitWizardPage />} />
                <Route path="/cases/:trackingId" element={<CaseDetailPage />} />
                <Route path="/profile" element={<ProfilePage />} />
            </Route>

            <Route path="*" element={<div className="p-6">Not found</div>} />
        </Routes>
    )
}
