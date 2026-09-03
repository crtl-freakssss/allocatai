import React from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import type { Proposal, Project, AuditEvent } from '../../types'
import { formatPaise } from '../../utils/money'
import { ArrowRight, MapPin, Building2 } from 'lucide-react'

export const Dashboard: React.FC = () => {
    const { data: proposals } = useQuery<Proposal[]>({
        queryKey: ['proposals'],
        queryFn: () => apiClient.get<Proposal[]>('/proposals'),
    })

    const { data: projects } = useQuery<Project[]>({
        queryKey: ['projects'],
        queryFn: () => apiClient.get<Project[]>('/projects'),
    })

    const { data: auditEvents } = useQuery<AuditEvent[]>({
        queryKey: ['auditEvents'],
        queryFn: () => apiClient.get<AuditEvent[]>('/audit/events'),
    })

    const totalRequestedPaise = projects?.reduce(
        (sum, p) => sum + (p.financials?.requested_amount_paise || 0),
        0
    ) || 0

    const topProject = projects && projects.length > 0 ? projects[0] : null
    const statesCount = new Set(
        projects?.flatMap((p) => p.geographies.map((g) => g.state)) || []
    ).size

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            {/* Header Hero */}
            <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-space-lg shadow-sm border border-outline-variant/30">
                <div className="relative z-10 flex flex-col xl:flex-row xl:items-start justify-between gap-space-lg">
                    <div className="space-y-space-xs max-w-2xl">
                        <div className="inline-flex items-center gap-2 font-label-caps text-label-caps uppercase tracking-wider text-secondary">
                            <span>AllocateAI / CSR Decision Platform</span>
                        </div>
                        <h1 className="font-display text-display tracking-tight text-on-surface">
                            Good morning, Admin
                        </h1>
                        <p className="font-body-lg text-body-lg text-on-surface-variant">
                            See where your next ₹1 lakh can create the greatest additional impact.
                        </p>
                    </div>
                    <div className="flex items-center gap-2 rounded bg-emerald-500/10 px-3 py-1 border border-emerald-500/30">
                        <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                        <span className="font-label-caps text-[11px] uppercase text-emerald-700 font-semibold">PostgreSQL & Decision Engine Connected</span>
                    </div>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 gap-space-md md:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-xl bg-surface-container-lowest p-space-md shadow-sm border border-outline-variant/30">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        Total Capital Demand
                    </p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                        {formatPaise(totalRequestedPaise)}
                    </p>
                    <p className="mt-1 font-body-sm text-[11px] text-on-surface-variant">
                        Requested across candidate proposals
                    </p>
                </div>

                <div className="rounded-xl bg-surface-container-lowest p-space-md shadow-sm border border-outline-variant/30">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        Projects Evaluated
                    </p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                        {projects?.length || 0}
                    </p>
                    <p className="mt-1 font-body-sm text-[11px] text-on-surface-variant">
                        Vetted candidate programs
                    </p>
                </div>

                <div className="rounded-xl bg-surface-container-lowest p-space-md shadow-sm border border-outline-variant/30">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        Active Proposals
                    </p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-secondary">
                        {proposals?.length || 0}
                    </p>
                    <p className="mt-1 font-body-sm text-[11px] text-on-surface-variant">
                        Ingested PDF submissions
                    </p>
                </div>

                <div className="rounded-xl bg-surface-container-lowest p-space-md shadow-sm border border-outline-variant/30">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        Geographic Coverage
                    </p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                        {statesCount} States
                    </p>
                    <p className="mt-1 font-body-sm text-[11px] text-on-surface-variant">
                        Target intervention regions
                    </p>
                </div>
            </div>

            {/* Main Dashboard Layout */}
            <div className="grid grid-cols-1 gap-space-lg xl:grid-cols-3">
                {/* Left Column */}
                <div className="flex flex-col gap-space-lg xl:col-span-2">
                    {/* PRIMARY OPPORTUNITY */}
                    <div className="rounded-xl bg-surface-container-lowest p-space-lg shadow-sm border border-outline-variant/30">
                        <div className="flex items-center justify-between border-b border-outline-variant/30 pb-space-sm mb-space-md">
                            <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                                Top Funding Opportunity
                            </h2>
                            {topProject && (
                                <Link to={`/projects/${topProject.project_id}/impact-dna`} className="text-secondary hover:text-on-secondary-container font-label-md text-sm font-medium flex items-center gap-1 transition-colors">
                                    View Impact DNA <ArrowRight className="w-4 h-4" />
                                </Link>
                            )}
                        </div>

                        {topProject ? (
                            <div className="flex flex-col md:flex-row gap-space-xl">
                                <div className="flex-1 space-y-space-md">
                                    <div>
                                        <h3 className="font-headline-lg text-headline-lg font-bold text-on-surface">
                                            {topProject.name}
                                        </h3>
                                        <p className="mt-1 font-body-md text-body-md text-on-surface-variant flex items-center gap-2">
                                            <Building2 className="w-4 h-4 text-on-surface-variant" />
                                            <span>NGO ID: {topProject.ngo_id}</span>
                                            <span>•</span>
                                            <MapPin className="w-4 h-4 text-on-surface-variant" />
                                            <span>{topProject.geographies[0]?.state || 'India'}</span>
                                        </p>
                                    </div>
                                    <div className="grid grid-cols-2 gap-3 pt-2">
                                        <div className="p-3 rounded-lg bg-surface-container-low border border-outline-variant/30">
                                            <span className="font-label-caps text-[10px] uppercase text-on-surface-variant">Sector</span>
                                            <p className="font-headline-sm text-sm font-semibold text-on-surface mt-0.5">{topProject.sector}</p>
                                        </div>
                                        <div className="p-3 rounded-lg bg-surface-container-low border border-outline-variant/30">
                                            <span className="font-label-caps text-[10px] uppercase text-on-surface-variant">Requested Budget</span>
                                            <p className="font-headline-sm text-sm font-semibold text-secondary mt-0.5">{formatPaise(topProject.financials.requested_amount_paise)}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="p-8 text-center text-on-surface-variant/60 font-body-md">
                                No candidate projects registered yet. Upload a proposal to begin.
                            </div>
                        )}
                    </div>

                    {/* RECENT PROJECTS TABLE */}
                    <div className="rounded-xl bg-surface-container-lowest shadow-sm border border-outline-variant/30">
                        <div className="border-b border-outline-variant/30 px-space-md py-space-sm flex items-center justify-between">
                            <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                                Candidate Projects
                            </h2>
                            <Link to="/projects" className="text-secondary font-label-md text-xs font-semibold hover:underline">
                                View All ({projects?.length || 0})
                            </Link>
                        </div>
                        <div className="overflow-x-auto p-space-md">
                            <table className="w-full text-left font-body-md text-body-md">
                                <thead className="bg-surface-container-low font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                                    <tr>
                                        <th className="px-space-md py-2.5">ID</th>
                                        <th className="px-space-md py-2.5">Project Name</th>
                                        <th className="px-space-md py-2.5">Sector</th>
                                        <th className="px-space-md py-2.5">State</th>
                                        <th className="px-space-md py-2.5">Budget</th>
                                        <th className="px-space-md py-2.5">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-outline-variant/20">
                                    {projects?.slice(0, 5).map((proj) => (
                                        <tr key={proj.project_id} className="hover:bg-surface-container-low/50 transition-colors">
                                            <td className="px-space-md py-3 font-mono text-xs font-bold text-on-surface-variant">{proj.project_id}</td>
                                            <td className="px-space-md py-3 font-semibold text-on-surface">{proj.name}</td>
                                            <td className="px-space-md py-3 text-on-surface-variant">{proj.sector}</td>
                                            <td className="px-space-md py-3 text-on-surface-variant">{proj.geographies[0]?.state || 'N/A'}</td>
                                            <td className="px-space-md py-3 font-semibold text-secondary">{formatPaise(proj.financials.requested_amount_paise)}</td>
                                            <td className="px-space-md py-3">
                                                <Link to={`/projects/${proj.project_id}/impact-dna`} className="text-secondary font-label-md text-xs font-semibold hover:underline">
                                                    Impact DNA →
                                                </Link>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* Right Column */}
                <div className="space-y-space-lg xl:col-span-1">
                    {/* QUICK ACTIONS */}
                    <div className="rounded-xl bg-surface-container-lowest p-space-lg shadow-sm border border-outline-variant/30 space-y-3">
                        <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Quick Actions</h2>
                        <Link to="/proposals/upload" className="flex items-center justify-between p-3 rounded-lg bg-surface-container-low hover:bg-surface-container transition border border-outline-variant/30 group">
                            <span className="font-body-md text-sm font-medium text-on-surface">Upload Proposal PDF</span>
                            <ArrowRight className="w-4 h-4 text-secondary group-hover:translate-x-1 transition-transform" />
                        </Link>
                        <Link to="/optimization" className="flex items-center justify-between p-3 rounded-lg bg-surface-container-low hover:bg-surface-container transition border border-outline-variant/30 group">
                            <span className="font-body-md text-sm font-medium text-on-surface">Execute MILP Optimizer</span>
                            <ArrowRight className="w-4 h-4 text-secondary group-hover:translate-x-1 transition-transform" />
                        </Link>
                    </div>

                    {/* RECENT AUDIT EVENTS */}
                    <div className="rounded-xl bg-surface-container-lowest p-space-lg shadow-sm border border-outline-variant/30 space-y-3">
                        <div className="flex items-center justify-between border-b border-outline-variant/30 pb-2">
                            <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">System Audit Trail</h2>
                            <Link to="/audit" className="text-secondary font-label-md text-xs font-semibold hover:underline">View All</Link>
                        </div>
                        <div className="space-y-3 text-xs">
                            {auditEvents?.slice(0, 4).map((evt) => {
                                const id = evt.public_id || (evt as any).event_id
                                const timestamp = evt.created_at || (evt as any).timestamp

                                return (
                                    <div key={id} className="p-2.5 rounded bg-surface-container-low border border-outline-variant/20 space-y-1">
                                        <div className="flex justify-between font-mono text-[10px] text-on-surface-variant">
                                            <span className="font-bold text-secondary">{evt.event_type}</span>
                                            <span>{timestamp ? new Date(timestamp).toLocaleTimeString() : ''}</span>
                                        </div>
                                        <p className="font-body-sm text-[11px] text-on-surface truncate">Entity: {evt.entity_type} ({evt.entity_id || 'N/A'})</p>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Dashboard
