import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import type { Project, ImpactDNA as ImpactDNAType } from '../../types'
import { formatScore } from '../../utils/money'
import { ArrowLeft, Dna } from 'lucide-react'

export const ImpactDNA: React.FC = () => {
    const { id } = useParams<{ id: string }>()

    const { data: project } = useQuery<Project>({
        queryKey: ['project', id],
        queryFn: () => apiClient.get<Project>(`/projects/${id}`),
        enabled: Boolean(id),
    })

    const { data: dna, isLoading, error } = useQuery<ImpactDNAType>({
        queryKey: ['impactDna', id],
        queryFn: () => apiClient.get<ImpactDNAType>(`/projects/${id}/dna`),
        enabled: Boolean(id),
    })

    const signals = [
        { label: 'Socioeconomic Need', value: dna?.need_score ?? 0.85 },
        { label: 'Expected Impact', value: dna?.expected_impact_score ?? 0.82 },
        { label: 'Cost Efficiency', value: dna?.cost_efficiency_score ?? 0.88 },
        { label: 'Evidence Strength', value: dna?.evidence_strength_score ?? 0.90 },
        { label: 'Scalability', value: dna?.scalability_score ?? 0.80 },
        { label: 'Implementation Risk', value: dna?.implementation_risk_score ?? 0.25 },
    ]

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-secondary/10 px-space-sm py-1 font-label-caps text-label-caps uppercase tracking-wider text-secondary">
                        <Dna className="w-3.5 h-3.5" />
                        <span>PROJECT INTELLIGENCE</span>
                    </div>
                    <h1 className="mt-2 font-display text-display tracking-tight text-on-surface">
                        Impact DNA Vector
                    </h1>
                    <p className="mt-1 font-body-lg text-body-lg text-on-surface-variant">
                        {project ? project.name : `Project ID: ${id}`} · State: {project?.geographies[0]?.state || 'India'}
                    </p>
                </div>
                <Link
                    to="/projects"
                    className="rounded border border-outline-variant px-4 py-2 font-label-md text-label-md font-medium text-on-surface transition hover:bg-surface-container-low flex items-center gap-1"
                >
                    <ArrowLeft className="w-4 h-4" /> Back to Projects
                </Link>
            </div>

            {isLoading ? (
                <div className="p-8 text-center text-on-surface-variant">Loading Impact DNA vector...</div>
            ) : error || !dna ? (
                <div className="p-8 text-center text-rose-500 font-body-md">
                    Impact DNA vector for project {id} is unavailable or failed to load.
                </div>
            ) : (
                <>
                    {/* Main insight */}
                    <div className="rounded-xl border border-outline-variant/50 bg-surface-container-low p-space-lg shadow-sm">
                        <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                            Impact Profile & Metadata
                        </p>

                        <div className="mt-space-md flex flex-col justify-between gap-space-lg md:flex-row md:items-end">
                            <div>
                                <h2 className="font-headline-lg text-headline-lg font-semibold text-on-surface">
                                    Multidimensional AI Impact Vector
                                </h2>
                                <p className="mt-2 max-w-2xl font-body-md text-body-md text-on-surface-variant">
                                    Derived via AI extraction engine ({dna.model_name}). Evaluates baseline need, scalability, evidence strength, and risk discounts.
                                </p>
                            </div>

                            <div className="text-left md:text-right">
                                <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                                    Extraction Confidence
                                </p>
                                <p className="mt-1 font-headline-lg text-headline-lg font-semibold text-secondary">
                                    {formatScore(dna.extraction_confidence)}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Signal cards */}
                    <div className="rounded-xl bg-surface-container-lowest p-space-lg shadow-sm border border-outline-variant/30">
                        <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface mb-4">
                            Normalized Impact Dimension Signals
                        </h2>

                        <div className="grid gap-space-md md:grid-cols-2 lg:grid-cols-3">
                            {signals.map((signal) => (
                                <div
                                    key={signal.label}
                                    className="rounded-lg border border-outline-variant/30 bg-surface-container-low p-space-md"
                                >
                                    <div className="flex items-center justify-between">
                                        <p className="font-body-sm text-body-sm text-on-surface-variant">
                                            {signal.label}
                                        </p>
                                        <p className="font-tabular-stat text-headline-sm font-semibold text-on-surface">
                                            {formatScore(signal.value)}
                                        </p>
                                    </div>

                                    <div className="mt-space-sm h-2 overflow-hidden rounded-full bg-surface-container-highest">
                                        <div
                                            className={`h-full rounded-full ${
                                                signal.label === 'Implementation Risk'
                                                    ? 'bg-amber-500'
                                                    : 'bg-secondary'
                                            }`}
                                            style={{ width: `${Math.min(signal.value * 100, 100)}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

export default ImpactDNA
