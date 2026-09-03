import React from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import type { Project } from '../../types'
import { formatPaise } from '../../utils/money'
import { ArrowRight } from 'lucide-react'

export const Projects: React.FC = () => {
    const { data: projects, isLoading } = useQuery<Project[]>({
        queryKey: ['projects'],
        queryFn: () => apiClient.get<Project[]>('/projects'),
    })

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            {/* Header Hero */}
            <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-space-lg lg:p-space-xl shadow-sm border border-outline-variant/30">
                <div className="relative z-10 flex flex-col xl:flex-row xl:items-center justify-between gap-space-lg">
                    <div className="space-y-space-xs max-w-2xl">
                        <div className="inline-flex items-center gap-2 rounded-full bg-secondary/10 px-space-sm py-1 font-label-caps text-label-caps uppercase tracking-wider text-secondary">
                            <span>DECISION ENGINE</span>
                        </div>
                        <h1 className="font-display text-display tracking-tight text-on-surface">
                            Candidate Projects Portfolio
                        </h1>
                        <p className="font-body-lg text-body-lg text-on-surface-variant">
                            Compare candidate CSR programs by sector, state, requested capital, and multidimensional Impact DNA.
                        </p>
                    </div>
                </div>
            </div>

            {/* Key insight */}
            <div className="rounded-xl border border-outline-variant/50 bg-surface-container-low p-space-lg">
                <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                    Allocation Insight
                </p>
                <h2 className="mt-2 font-headline-md text-headline-md font-semibold text-on-surface">
                    Where will the next ₹1 lakh create the most impact?
                </h2>
                <p className="mt-2 max-w-3xl font-body-md text-body-md text-on-surface-variant">
                    The ranking combines project impact signals with marginal impact to identify opportunities where additional CSR funding creates the greatest incremental value.
                </p>
            </div>

            {/* Ranking table */}
            <div className="rounded-xl bg-surface-container-lowest shadow-sm border border-outline-variant/30">
                <div className="border-b border-outline-variant/30 px-space-md py-space-sm">
                    <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                        Evaluated Candidate Projects ({projects?.length || 0})
                    </h2>
                </div>

                <div className="overflow-x-auto p-space-md">
                    {isLoading ? (
                        <div className="p-8 text-center text-on-surface-variant">Loading projects from PostgreSQL...</div>
                    ) : (
                        <table className="w-full text-left font-body-md text-body-md">
                            <thead className="bg-surface-container-low font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                                <tr>
                                    <th className="px-space-md py-2.5">Project ID</th>
                                    <th className="px-space-md py-2.5">Project Name</th>
                                    <th className="px-space-md py-2.5">NGO ID</th>
                                    <th className="px-space-md py-2.5">Sector</th>
                                    <th className="px-space-md py-2.5">State</th>
                                    <th className="px-space-md py-2.5">Requested Capital</th>
                                    <th className="px-space-md py-2.5">Action</th>
                                </tr>
                            </thead>

                            <tbody className="divide-y divide-outline-variant/20">
                                {projects?.map((proj) => (
                                    <tr key={proj.project_id} className="transition-colors hover:bg-surface-container-low/50">
                                        <td className="px-space-md py-space-md font-mono text-xs font-bold text-on-surface-variant">
                                            {proj.project_id}
                                        </td>
                                        <td className="px-space-md py-space-md font-semibold text-on-surface">
                                            {proj.name}
                                        </td>
                                        <td className="px-space-md py-space-md font-mono text-xs text-on-surface-variant">
                                            {proj.ngo_id}
                                        </td>
                                        <td className="px-space-md py-space-md text-on-surface-variant">
                                            {proj.sector}
                                        </td>
                                        <td className="px-space-md py-space-md text-on-surface-variant">
                                            {proj.geographies[0]?.state || 'India'}
                                        </td>
                                        <td className="px-space-md py-space-md font-semibold text-secondary">
                                            {formatPaise(proj.financials.requested_amount_paise)}
                                        </td>
                                        <td className="px-space-md py-space-md">
                                            <Link
                                                to={`/projects/${proj.project_id}/impact-dna`}
                                                className="text-secondary hover:text-on-secondary-container font-label-md text-xs font-semibold flex items-center gap-1"
                                            >
                                                Impact DNA <ArrowRight className="w-3.5 h-3.5" />
                                            </Link>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    )
}

export default Projects
