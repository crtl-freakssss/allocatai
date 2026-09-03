import { Routes, Route, Navigate } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'

import Dashboard from '../features/dashboard/Dashboard'
import Proposals from '../features/proposals/Proposals'
import ProposalUpload from '../features/proposals/ProposalUpload'
import ProposalReview from '../features/proposals/ProposalReview'
import Projects from '../features/projects/Projects'
import ImpactDNA from '../features/projects/ImpactDNA'
import Saturation from '../features/saturation/Saturation'
import Optimization from '../features/optimization/Optimization'
import Allocations from '../features/allocations/Allocations'
import Reallocation from '../features/reallocation/Reallocation'
import DueDiligence from '../features/due-diligence/DueDiligence'
import Explainability from '../features/explainability/Explainability'
import Audit from '../features/audit/Audit'
import Settings from '../features/settings/Settings'

export default function AppRouter() {
    return (
        <Routes>
            <Route element={<AppShell />}>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />

                <Route path="/proposals" element={<Proposals />} />
                <Route path="/proposals/upload" element={<ProposalUpload />} />
                <Route path="/proposals/:id" element={<ProposalReview />} />

                <Route path="/projects" element={<Projects />} />
                <Route path="/projects/:id/impact-dna" element={<ImpactDNA />} />

                <Route path="/saturation" element={<Saturation />} />

                <Route path="/optimization" element={<Optimization />} />
                <Route path="/allocations" element={<Allocations />} />

                <Route path="/reallocation" element={<Reallocation />} />

                <Route path="/due-diligence" element={<DueDiligence />} />

                <Route path="/explainability" element={<Explainability />} />

                <Route path="/audit" element={<Audit />} />

                <Route path="/settings" element={<Settings />} />
            </Route>
        </Routes>
    )
}
