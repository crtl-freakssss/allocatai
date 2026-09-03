import React from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import type { Proposal } from '../../types'
import { ArrowRight } from 'lucide-react'

export const Proposals: React.FC = () => {
    const { data: proposals, isLoading } = useQuery<Proposal[]>({
        queryKey: ['proposals'],
        queryFn: () => apiClient.get<Proposal[]>('/proposals'),
    })

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            {/* Header */}
            <div className="flex items-end justify-between">
                <div>
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        PROPOSAL MANAGEMENT
                    </p>
                    <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                        CSR Proposals
                    </h1>
                    <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                        Review, analyze and prioritize incoming CSR proposals backed by PostgreSQL.
                    </p>
                </div>

                <Link
                    to="/proposals/upload"
                    className="rounded bg-secondary px-5 py-3 font-label-md text-sm font-semibold text-on-secondary shadow-sm hover:bg-on-secondary-container transition"
                >
                    + Upload Proposal
                </Link>
            </div>

            {/* Summary cards */}
            <div className="grid gap-space-md md:grid-cols-3">
                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Total Proposals</p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                        {proposals?.length || 0}
                    </p>
                </div>

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Extracted Proposals</p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-secondary">
                        {proposals?.filter((p) => p.status === 'EXTRACTED').length || 0}
                    </p>
                </div>

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Uploaded</p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                        {proposals?.filter((p) => p.status === 'UPLOADED').length || 0}
                    </p>
                </div>
            </div>

            {/* Proposal table */}
            <div className="rounded-xl bg-surface-container-lowest shadow-sm border border-outline-variant/30">
                <div className="border-b border-outline-variant/30 px-space-md py-space-sm">
                    <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                        Submitted Proposals
                    </h2>
                </div>

                <div className="overflow-x-auto p-space-md">
                    {isLoading ? (
                        <div className="p-8 text-center text-on-surface-variant">Loading proposals...</div>
                    ) : (
                        <table className="w-full text-left font-body-md text-body-md">
                            <thead className="bg-surface-container-low font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                                <tr>
                                    <th className="rounded-l px-space-md py-2.5">Proposal ID</th>
                                    <th className="px-space-md py-2.5">Title</th>
                                    <th className="px-space-md py-2.5">NGO ID</th>
                                    <th className="px-space-md py-2.5">Status</th>
                                    <th className="px-space-md py-2.5">Created At</th>
                                    <th className="rounded-r px-space-md py-2.5">Action</th>
                                </tr>
                            </thead>

                            <tbody className="divide-y divide-outline-variant/20">
                                {proposals?.map((proposal) => (
                                    <tr key={proposal.proposal_id} className="transition-colors hover:bg-surface-container-low/50">
                                        <td className="px-space-md py-space-md font-mono text-xs font-bold text-on-surface-variant">
                                            {proposal.proposal_id}
                                        </td>
                                        <td className="px-space-md py-space-md font-semibold text-on-surface">
                                            {proposal.title}
                                        </td>
                                        <td className="px-space-md py-space-md font-mono text-xs text-on-surface-variant">
                                            {proposal.ngo_id}
                                        </td>
                                        <td className="px-space-md py-space-md">
                                            <span className={`inline-flex items-center gap-1 rounded px-2 py-0.5 font-label-caps text-[10px] uppercase font-semibold ${
                                                proposal.status === 'EXTRACTED'
                                                    ? 'bg-emerald-500/20 text-emerald-700 border border-emerald-500/30'
                                                    : 'bg-amber-500/20 text-amber-700 border border-amber-500/30'
                                            }`}>
                                                {proposal.status}
                                            </span>
                                        </td>
                                        <td className="px-space-md py-space-md text-xs text-on-surface-variant">
                                            {new Date(proposal.created_at).toLocaleDateString()}
                                        </td>
                                        <td className="px-space-md py-space-md">
                                            <Link
                                                to={`/proposals/${proposal.proposal_id}`}
                                                className="text-secondary hover:text-on-secondary-container font-label-md text-xs font-semibold flex items-center gap-1"
                                            >
                                                Review Proposal <ArrowRight className="w-3.5 h-3.5" />
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

export default Proposals
