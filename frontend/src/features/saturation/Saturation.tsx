import React from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import type { Project } from '../../types'
import { MapPin } from 'lucide-react'

const stateBenchmarks: Record<string, { benchmarkCr: number; status: string }> = {
    Bihar: { benchmarkCr: 120, status: 'HIGH_NEED_LOW_SATURATION' },
    Jharkhand: { benchmarkCr: 150, status: 'UNDERSERVED' },
    Rajasthan: { benchmarkCr: 200, status: 'BALANCED' },
    Odisha: { benchmarkCr: 180, status: 'UNDERSERVED' },
    'Madhya Pradesh': { benchmarkCr: 210, status: 'BALANCED' },
    Assam: { benchmarkCr: 140, status: 'UNDERSERVED' },
}

export const Saturation: React.FC = () => {
    const { data: projects } = useQuery<Project[]>({
        queryKey: ['projects'],
        queryFn: () => apiClient.get<Project[]>('/projects'),
    })

    const states = Array.from(
        new Set(projects?.flatMap((p) => p.geographies.map((g) => g.state)) || ['Bihar', 'Jharkhand', 'Rajasthan', 'Odisha'])
    )

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            {/* Header */}
            <div className="flex items-end justify-between">
                <div>
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        GEOGRAPHIC INTELLIGENCE
                    </p>
                    <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                        State CSR Saturation Map (`sat-v1`)
                    </h1>
                    <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                        Identify state interventions where CSR funding density is concentrated or underserved.
                    </p>
                </div>

                <Link
                    to="/optimization"
                    className="rounded bg-secondary px-5 py-3 font-label-md text-sm font-semibold text-on-secondary shadow-sm hover:bg-on-secondary-container transition"
                >
                    Continue to Optimizer →
                </Link>
            </div>

            {/* Key insight */}
            <div className="rounded-xl border border-outline-variant/50 bg-surface-container-lowest p-6 shadow-sm">
                <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                    Saturation Decay Insight
                </p>
                <h2 className="mt-2 font-headline-lg text-headline-lg font-semibold text-on-surface">
                    Bihar & Jharkhand show high-need, low-saturation opportunities
                </h2>
                <p className="mt-2 max-w-3xl font-body-md text-body-md text-on-surface-variant">
                    The backend saturation engine scales marginal impact by exponential saturation decay ($\exp(-\lambda \cdot S)$), giving higher priority to underserved regions.
                </p>
            </div>

            {/* State Grid */}
            <div className="grid gap-space-md md:grid-cols-2 lg:grid-cols-3">
                {states.map((st) => {
                    const info = stateBenchmarks[st] || { benchmarkCr: 150, status: 'UNDERSERVED' }
                    const projCount = projects?.filter((p) => p.geographies.some((g) => g.state === st)).length || 0

                    return (
                        <div key={st} className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm space-y-3">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-2">
                                    <MapPin className="w-4 h-4 text-secondary" />
                                    <h3 className="font-headline-sm text-sm font-semibold text-on-surface">{st}</h3>
                                </div>
                                <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-700 font-label-caps text-[10px] font-bold border border-emerald-500/30">
                                    {info.status}
                                </span>
                            </div>

                            <div className="grid grid-cols-2 gap-2 text-xs">
                                <div className="p-2 rounded bg-surface-container-low">
                                    <span className="font-label-caps text-[10px] text-on-surface-variant">CSR Benchmark</span>
                                    <p className="font-bold text-on-surface mt-0.5">₹{info.benchmarkCr} Cr</p>
                                </div>
                                <div className="p-2 rounded bg-surface-container-low">
                                    <span className="font-label-caps text-[10px] text-on-surface-variant">Candidate Projects</span>
                                    <p className="font-bold text-secondary mt-0.5">{projCount} Program(s)</p>
                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

export default Saturation
