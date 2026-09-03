import React, { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import type { ReallocationResult, OptimizationResult, Project } from '../../types'
import { formatPaise, rupeesToPaise } from '../../utils/money'
import { RefreshCw, Loader2, AlertCircle, ArrowRightLeft } from 'lucide-react'

export const Reallocation: React.FC = () => {
    const queryClient = useQueryClient()
    const lastOpt = queryClient.getQueryData<OptimizationResult>(['lastOptimizationRun'])

    const { data: projects } = useQuery<Project[]>({
        queryKey: ['projects'],
        queryFn: () => apiClient.get<Project[]>('/projects'),
    })

    const [budgetRupees, setBudgetRupees] = useState<number>(20_00_00_000)
    const [progressVelocity, setProgressVelocity] = useState<number>(0.85) // 85% progress velocity
    const [reallocResult, setReallocResult] = useState<ReallocationResult | null>(null)
    const [errorMsg, setErrorMsg] = useState<string | null>(null)

    const reallocMutation = useMutation({
        mutationFn: async () => {
            setErrorMsg(null)
            const runId = lastOpt?.run_id || 'OPT-0001'
            const activeProjects = projects || []
            const projectIds = activeProjects.map(p => p.project_id)

            const updates = projectIds.map(pid => ({
                project_id: pid,
                progress_percent: progressVelocity * 100,
                actual_spend_paise: Math.round(rupeesToPaise(5_00_000)),
            }))

            const res = await apiClient.post<ReallocationResult>('/reallocation/runs', {
                previous_run_id: runId,
                budget_paise: Math.round(rupeesToPaise(budgetRupees)),
                performance_updates: updates,
                weights: {
                    need: 0.30,
                    marginal_impact: 0.30,
                    cost_efficiency: 0.20,
                    evidence: 0.10,
                    scalability: 0.05,
                    equity: 0.03,
                    risk_penalty: 0.02,
                },
                constraints: {
                    regional_equity_enabled: true,
                },
            })
            return res
        },
        onSuccess: (res) => {
            setReallocResult(res)
            setErrorMsg(null)
            queryClient.invalidateQueries({ queryKey: ['auditEvents'] })
        },
        onError: (err: any) => {
            setErrorMsg(err.message || 'Reallocation run failed')
        },
    })

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            {/* Header Hero */}
            <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-space-lg lg:p-space-xl shadow-sm border border-outline-variant/30">
                <div className="relative z-10 flex flex-col xl:flex-row xl:items-center justify-between gap-space-lg">
                    <div className="space-y-space-xs max-w-2xl">
                        <div className="inline-flex items-center gap-2 rounded-full bg-secondary/10 px-space-sm py-1 font-label-caps text-label-caps uppercase tracking-wider text-secondary">
                            <RefreshCw className="w-3.5 h-3.5" />
                            <span>MID-TERM REALLOCATION ENGINE</span>
                        </div>
                        <h1 className="font-display text-display tracking-tight text-on-surface">
                            Dynamic Portfolio Reallocation
                        </h1>
                        <p className="font-body-lg text-body-lg text-on-surface-variant">
                            Re-balance portfolio capital based on live project execution velocity ($&lt;40\%$ vs $\ge 75\%$) and regional saturation updates.
                        </p>
                    </div>
                </div>
            </div>

            {errorMsg && (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center space-x-3 text-rose-700 text-xs">
                    <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
                    <div>
                        <p className="font-semibold">Reallocation Error</p>
                        <p>{errorMsg}</p>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 gap-space-lg lg:grid-cols-3">
                {/* Controls */}
                <div className="space-y-space-lg rounded-xl bg-surface-container-lowest p-space-lg shadow-sm border border-outline-variant/30 lg:col-span-1">
                    <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface border-b border-outline-variant/30 pb-3">Reallocation Parameters</h2>

                    <div className="space-y-2">
                        <label className="block font-label-md text-xs font-medium text-on-surface-variant flex justify-between">
                            <span>Base Run ID</span>
                            <span className="font-mono font-bold text-secondary">{lastOpt?.run_id || 'OPT-0001'}</span>
                        </label>
                    </div>

                    <div className="space-y-2">
                        <label className="block font-label-md text-xs font-medium text-on-surface-variant flex justify-between">
                            <span>Adjusted Budget</span>
                            <span className="font-bold text-on-surface">{formatPaise(rupeesToPaise(budgetRupees))}</span>
                        </label>
                        <input
                            type="range"
                            min={1_00_00_000}
                            max={50_00_00_000}
                            step={1_00_00_000}
                            value={budgetRupees}
                            onChange={(e) => setBudgetRupees(Number(e.target.value))}
                            className="w-full accent-secondary"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="block font-label-md text-xs font-medium text-on-surface-variant flex justify-between">
                            <span>Project Progress Velocity</span>
                            <span className="font-mono font-bold text-secondary">{(progressVelocity * 100).toFixed(0)}%</span>
                        </label>
                        <input
                            type="range"
                            min={0.10}
                            max={1.00}
                            step={0.05}
                            value={progressVelocity}
                            onChange={(e) => setProgressVelocity(Number(e.target.value))}
                            className="w-full accent-secondary"
                        />
                    </div>

                    <button
                        onClick={() => reallocMutation.mutate()}
                        disabled={reallocMutation.isPending}
                        className="flex w-full items-center justify-center gap-2 rounded bg-secondary px-space-md py-3 font-label-md text-sm font-semibold text-on-secondary shadow-md transition hover:bg-on-secondary-container disabled:opacity-50"
                    >
                        {reallocMutation.isPending ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <ArrowRightLeft className="h-4 w-4" />
                        )}
                        <span>{reallocMutation.isPending ? 'Executing Reallocation...' : 'Run Portfolio Reallocation'}</span>
                    </button>
                </div>

                {/* Results Area */}
                <div className="flex min-h-[300px] flex-col overflow-hidden rounded-xl bg-surface-container-lowest p-space-lg shadow-sm border border-outline-variant/30 lg:col-span-2">
                    {!reallocResult && !reallocMutation.isPending && (
                        <div className="flex h-full flex-col items-center justify-center space-y-4 text-center p-12">
                            <RefreshCw className="h-12 w-12 text-on-surface-variant/30" />
                            <div>
                                <p className="font-headline-sm text-headline-sm font-semibold text-on-surface">Ready for Mid-Term Reallocation</p>
                                <p className="mt-1 font-body-sm text-body-sm text-on-surface-variant">Adjust progress velocity on the left to compute updated tranche allocations.</p>
                            </div>
                        </div>
                    )}

                    {reallocMutation.isPending && (
                        <div className="flex h-full flex-col items-center justify-center space-y-4 text-center p-12">
                            <Loader2 className="h-12 w-12 animate-spin text-secondary" />
                            <p className="font-headline-sm text-headline-sm font-semibold text-on-surface">Reallocation Engine Active</p>
                        </div>
                    )}

                    {reallocResult && (
                        <div className="space-y-space-md">
                            <div className="flex items-center justify-between border-b border-outline-variant/30 pb-3">
                                <div>
                                    <span className="font-mono text-xs text-on-surface-variant">Reallocation ID: <strong className="text-secondary">{reallocResult.run_id}</strong></span>
                                    <h3 className="font-headline-sm text-base font-bold text-on-surface mt-0.5">Reallocated Tranche Vector</h3>
                                </div>
                                <span className="px-3 py-1 rounded bg-emerald-500/20 text-emerald-700 font-label-caps text-xs font-bold border border-emerald-500/30">
                                    Shifted {formatPaise(reallocResult.total_budget_shifted_paise)}
                                </span>
                            </div>

                            <div className="overflow-x-auto pt-2">
                                <table className="w-full text-left font-body-md text-body-md">
                                    <thead className="bg-surface-container-low font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                                        <tr>
                                            <th className="px-space-md py-2.5">Project ID</th>
                                            <th className="px-space-md py-2.5">State</th>
                                            <th className="px-space-md py-2.5">Updated Allocation</th>
                                            <th className="px-space-md py-2.5">Reason Codes</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-outline-variant/20">
                                        {reallocResult.new_allocations.map((alloc) => (
                                            <tr key={alloc.project_id} className="hover:bg-surface-container-low/50">
                                                <td className="px-space-md py-3 font-mono text-xs font-bold text-on-surface">{alloc.project_id}</td>
                                                <td className="px-space-md py-3 text-on-surface-variant">{alloc.state}</td>
                                                <td className="px-space-md py-3 font-semibold text-secondary">{formatPaise(alloc.allocated_amount_paise)}</td>
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
                    )}
                </div>
            </div>
        </div>
    )
}

export default Reallocation
