import React, { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import type { DueDiligenceReport, Project, NGO } from '../../types'
import { Search, ShieldAlert, Shield, CheckCircle2, XCircle, Building2 } from 'lucide-react'

export const DueDiligence: React.FC = () => {
    const { data: ngos } = useQuery<NGO[]>({
        queryKey: ['ngos'],
        queryFn: () => apiClient.get<NGO[]>('/ngos'),
    })

    const { data: projects } = useQuery<Project[]>({
        queryKey: ['projects'],
        queryFn: () => apiClient.get<Project[]>('/projects'),
    })

    const firstNgoId = ngos && ngos.length > 0 ? ngos[0].id : (projects && projects.length > 0 ? projects[0].ngo_id : "")
    const [searchId, setSearchId] = useState("")
    const [activeId, setActiveId] = useState("")

    const currentNgoId = activeId || searchId.trim() || firstNgoId

    const { data: report, isLoading, error } = useQuery<DueDiligenceReport>({
        queryKey: ['dueDiligence', currentNgoId],
        queryFn: async () => {
            try {
                return await apiClient.get<DueDiligenceReport>(`/due-diligence/${currentNgoId}`)
            } catch (err: any) {
                // If report not found (404), auto-evaluate report via POST /evaluate
                if (err.message?.includes('404') || err.message?.includes('not found') || err.code === 'RESOURCE_NOT_FOUND') {
                    return await apiClient.post<DueDiligenceReport>(`/due-diligence/${currentNgoId}/evaluate`)
                }
                throw err
            }
        },
        enabled: Boolean(currentNgoId && currentNgoId.includes('-')),
    })

    const evaluateMutation = useMutation({
        mutationFn: async (ngoId: string) => {
            return await apiClient.post<DueDiligenceReport>(`/due-diligence/${ngoId}/evaluate`)
        },
        onSuccess: (data) => {
            setActiveId(data.ngo_id)
        }
    })

    const handleSearch = () => {
        const targetId = searchId.trim() || firstNgoId
        if (targetId) {
            setActiveId(targetId)
            evaluateMutation.mutate(targetId)
        }
    }

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            <div>
                <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                    COMPLIANCE & RISK
                </p>
                <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                    NGO Due Diligence Evaluation
                </h1>
                <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                    AI-assisted due diligence, statutory checks, and risk evaluation layer.
                </p>
                <div className="mt-4 inline-flex items-center space-x-2 rounded-full bg-amber-500/10 px-3 py-1.5 font-label-md text-xs font-semibold text-amber-700 border border-amber-500/30">
                    <Shield className="h-4 w-4" />
                    <span>This report is an evidence and risk-assessment layer and does not constitute legal or regulatory certification.</span>
                </div>
            </div>

            {/* Search / Select Bar */}
            <div className="flex flex-col md:flex-row space-y-3 md:space-y-0 md:space-x-4 rounded-xl border border-outline-variant/50 bg-surface-container-lowest p-space-lg shadow-sm">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-on-surface-variant" />
                    <input
                        type="text"
                        placeholder={firstNgoId ? `Enter NGO UUID (e.g. ${firstNgoId})...` : "Enter NGO UUID..."}
                        value={searchId}
                        onChange={(e) => setSearchId(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        className="block w-full rounded border border-outline-variant bg-surface-container-low py-2.5 pl-10 pr-3 font-body-md text-sm text-on-surface focus:border-secondary focus:outline-none font-mono"
                    />
                </div>

                {((ngos && ngos.length > 0) || (projects && projects.length > 0)) && (
                    <div className="flex items-center space-x-2">
                        <Building2 className="w-4 h-4 text-secondary shrink-0" />
                        <select
                            value={currentNgoId}
                            onChange={(e) => setActiveId(e.target.value)}
                            className="px-3 py-2.5 rounded border border-outline-variant bg-surface-container-low text-xs font-mono"
                        >
                            {ngos && ngos.length > 0
                                ? ngos.map(n => (
                                    <option key={n.id} value={n.id}>
                                        {n.name} ({n.registration_number || n.external_id || n.id})
                                    </option>
                                ))
                                : Array.from(new Set((projects || []).map(p => p.ngo_id))).map(ngoId => (
                                    <option key={ngoId} value={ngoId}>
                                        Seeded NGO ({ngoId})
                                    </option>
                                ))}
                        </select>
                    </div>
                )}

                <button
                    onClick={handleSearch}
                    disabled={evaluateMutation.isPending}
                    className="flex items-center justify-center space-x-2 rounded bg-secondary px-6 py-2.5 font-label-md text-sm font-semibold text-on-secondary shadow-sm hover:bg-on-secondary-container transition"
                >
                    <Search className="h-4 w-4" />
                    <span>{evaluateMutation.isPending ? 'Evaluating...' : 'Evaluate NGO'}</span>
                </button>
            </div>

            {/* Content */}
            <div className="min-h-[300px]">
                {isLoading && (
                    <div className="p-12 text-center text-on-surface-variant font-body-md">Running AI due diligence checks...</div>
                )}

                {error && !report && (
                    <div className="p-12 text-center text-rose-600 font-body-md space-y-2">
                        <ShieldAlert className="w-8 h-8 mx-auto" />
                        <p className="font-bold">Due Diligence Report Unavailable</p>
                        <p className="text-xs text-on-surface-variant">{(error as any)?.message || "Click 'Evaluate NGO' above to trigger an automated statutory evaluation."}</p>
                    </div>
                )}

                {report && (
                    <div className="space-y-space-lg">
                        <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm space-y-4">
                            <div className="flex items-center justify-between border-b border-outline-variant/30 pb-3">
                                <div>
                                    <span className="font-mono text-xs text-on-surface-variant">Report ID: <strong className="text-on-surface">{report.report_id}</strong></span>
                                    <h2 className="font-headline-md text-headline-md font-bold text-on-surface mt-0.5">NGO UUID: {report.ngo_id}</h2>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <span className="px-2.5 py-1 rounded bg-surface-container text-xs font-mono font-semibold text-on-surface-variant border border-outline-variant/30">
                                        Risk: {report.risk_level}
                                    </span>
                                    <span className={`px-3 py-1 rounded font-label-caps text-xs font-bold ${
                                        report.overall_status === 'VERIFIED'
                                            ? 'bg-emerald-500/20 text-emerald-700 border border-emerald-500/30'
                                            : 'bg-amber-500/20 text-amber-700 border border-amber-500/30'
                                    }`}>
                                        {report.overall_status}
                                    </span>
                                </div>
                            </div>

                            <div className="space-y-3">
                                <h3 className="font-headline-sm text-sm font-semibold text-on-surface">Statutory Verification Checks ({report.checks.length})</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {report.checks.map((chk, idx) => (
                                        <div key={idx} className="p-3 rounded-lg bg-surface-container-low border border-outline-variant/30 flex items-center justify-between text-xs">
                                            <div className="flex items-center space-x-2">
                                                {chk.status === 'VERIFIED' ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> : <XCircle className="w-4 h-4 text-rose-600 shrink-0" />}
                                                <span className="font-semibold text-on-surface uppercase">{chk.check_name}</span>
                                            </div>
                                            <span className={`font-mono text-[10px] font-bold ${chk.status === 'VERIFIED' ? 'text-emerald-700' : 'text-rose-700'}`}>
                                                {chk.status} ({(chk.confidence * 100).toFixed(0)}%)
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default DueDiligence
