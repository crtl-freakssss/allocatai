import React from 'react'
import { useQueryClient, useQuery } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import type { OptimizationResult } from '../../types'
import { formatPaise } from '../../utils/money'
import { LayoutList } from 'lucide-react'
import { Link } from 'react-router-dom'

export const Allocations: React.FC = () => {
    const queryClient = useQueryClient()
    const cachedResult = queryClient.getQueryData<OptimizationResult>(['lastOptimizationRun'])

    const { data: runs } = useQuery<any[]>({
        queryKey: ['optimizationRuns'],
        queryFn: () => apiClient.get<any[]>('/optimization/runs'),
        enabled: !cachedResult,
    })

    const latestRunId = runs && runs.length > 0 ? runs[runs.length - 1].run_id : ''

    const { data: fetchedRun } = useQuery<any>({
        queryKey: ['optimizationRunDetail', latestRunId],
        queryFn: () => apiClient.get<any>(`/optimization/runs/${latestRunId}`),
        enabled: !cachedResult && Boolean(latestRunId),
    })

    const result: OptimizationResult | null = cachedResult || (fetchedRun ? {
        run_id: fetchedRun.run_id,
        status: fetchedRun.status,
        budget_paise: fetchedRun.budget_paise,
        allocated_paise: fetchedRun.result_snapshot?.allocated_paise || fetchedRun.budget_paise,
        unallocated_paise: fetchedRun.result_snapshot?.unallocated_paise || 0,
        total_predicted_impact: fetchedRun.total_predicted_impact || 0,
        average_saturation: fetchedRun.result_snapshot?.average_saturation || 0,
        underserved_region_allocation_share: fetchedRun.result_snapshot?.underserved_region_allocation_share || 0,
        weights: fetchedRun.input_snapshot?.weights || { need: 0.3, marginal_impact: 0.3, cost_efficiency: 0.2, evidence: 0.1, scalability: 0.05, equity: 0.03, risk_penalty: 0.02 },
        constraints: fetchedRun.input_snapshot?.constraints || { regional_equity_enabled: true },
        calculation_versions: fetchedRun.result_snapshot?.calculation_versions || { solver: 'scipy-milp-v1' },
        allocations: (fetchedRun.allocations || []).map((a: any) => ({
            project_id: a.project_id,
            state: a.state || 'India',
            allocated_amount_paise: a.allocated_amount_paise,
            marginal_impact_score: a.marginal_score,
            base_score: a.base_score,
            saturation_index: a.saturation_index,
            rank: a.rank,
            status: a.status,
            reason_codes: a.reason_codes,
        })),
        created_at: fetchedRun.created_at || new Date().toISOString(),
    } : null)

    if (!result) {
        return (
            <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4 rounded-xl bg-surface-container-lowest p-space-xl shadow-sm border border-outline-variant/30 text-center">
                <LayoutList className="h-10 w-10 text-on-surface-variant/50" />
                <h2 className="font-headline-sm text-headline-sm text-on-surface font-semibold">No Allocations Run Generated Yet</h2>
                <p className="font-body-sm text-body-sm text-on-surface-variant max-w-md">Run the SciPy MILP solver from the Budget Optimizer screen to view optimal portfolio allocations.</p>
                <Link to="/optimization" className="rounded bg-secondary px-4 py-2 font-label-md text-xs font-semibold text-on-secondary shadow-sm hover:bg-on-secondary-container transition">
                    Go to Budget Optimizer →
                </Link>
            </div>
        )
    }

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            {/* Header Hero */}
            <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-space-lg lg:p-space-xl shadow-sm border border-outline-variant/30">
                <div className="relative z-10 flex flex-col xl:flex-row xl:items-center justify-between gap-space-lg">
                    <div className="space-y-space-xs max-w-2xl">
                        <div className="inline-flex items-center gap-2 rounded-full bg-secondary/10 px-space-sm py-1 font-label-caps text-label-caps uppercase tracking-wider text-secondary">
                            <span className="h-2 w-2 animate-pulse rounded-full bg-secondary"></span>
                            <span>DECISION ENGINE RESULT · RUN #{result.run_id}</span>
                        </div>
                        <h1 className="font-display text-display tracking-tight text-on-surface">
                            Optimal Allocation Vector
                        </h1>
                        <p className="font-body-lg text-body-lg text-on-surface-variant">
                            Algorithmic frontier generated across vetted candidate projects. Linear programming solved subject to thematic allocations and safeguards.
                        </p>
                    </div>
                </div>

                {/* Metrics Grid */}
                <div className="mt-space-xl grid grid-cols-2 gap-space-md rounded-xl bg-surface-container-low/70 p-space-md md:grid-cols-4 border border-outline-variant/20">
                    <div className="flex flex-col">
                        <span className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Total Pool</span>
                        <span className="mt-0.5 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                            {formatPaise(result.budget_paise)}
                        </span>
                    </div>
                    <div className="flex flex-col">
                        <span className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Programs Selected</span>
                        <span className="mt-0.5 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                            {result.allocations.length}
                        </span>
                    </div>
                    <div className="flex flex-col">
                        <span className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Total Allocated</span>
                        <span className="mt-0.5 font-tabular-stat text-tabular-stat font-semibold text-secondary">
                            {formatPaise(result.allocated_paise)}
                        </span>
                    </div>
                    <div className="flex flex-col">
                        <span className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Unallocated Capital</span>
                        <span className="mt-0.5 font-tabular-stat text-tabular-stat font-semibold text-on-surface-variant">
                            {formatPaise(result.unallocated_paise)}
                        </span>
                    </div>
                </div>
            </div>

            {/* Allocations Table */}
            <div className="rounded-xl bg-surface-container-lowest shadow-sm border border-outline-variant/30">
                <div className="border-b border-outline-variant/30 px-space-md py-space-sm">
                    <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                        Program Allocation Vector
                    </h2>
                </div>
                <div className="overflow-x-auto p-space-md">
                    <table className="w-full text-left font-body-md text-body-md">
                        <thead className="bg-surface-container-low font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                            <tr>
                                <th className="px-space-md py-2.5">Project ID</th>
                                <th className="px-space-md py-2.5">State</th>
                                <th className="px-space-md py-2.5">Allocated Amount</th>
                                <th className="px-space-md py-2.5">Marginal Impact Score</th>
                                <th className="px-space-md py-2.5">Reason Codes</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-outline-variant/20">
                            {result.allocations.map((alloc) => (
                                <tr key={alloc.project_id} className="hover:bg-surface-container-low/50">
                                    <td className="px-space-md py-3 font-mono text-xs font-bold text-on-surface">{alloc.project_id}</td>
                                    <td className="px-space-md py-3 text-on-surface-variant">{alloc.state}</td>
                                    <td className="px-space-md py-3 font-semibold text-secondary">{formatPaise(alloc.allocated_amount_paise)}</td>
                                    <td className="px-space-md py-3 font-mono text-xs text-on-surface-variant">{alloc.marginal_impact_score.toFixed(3)}</td>
                                    <td className="px-space-md py-3">
                                        <div className="flex flex-wrap gap-1">
                                            {alloc.reason_codes.map((rc) => (
                                                <span key={rc} className="px-1.5 py-0.5 rounded bg-surface-container text-[10px] font-mono text-on-surface-variant">
                                                    {rc}
                                                </span>
                                            ))}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}

export default Allocations
