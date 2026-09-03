import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import type { Project, OptimizationResult, OptimizationWeights } from '../../types'
import { rupeesToPaise, formatPaise } from '../../utils/money'
import { Loader2, AlertCircle, Settings2, Play, Info } from 'lucide-react'

export const Optimization: React.FC = () => {
    const queryClient = useQueryClient()
    const [budgetRupees, setBudgetRupees] = useState<number>(20_00_00_000) // ₹20 Crore default
    const [maxPerProjectRupees, setMaxPerProjectRupees] = useState<number>(10_00_00_000) // ₹10 Crore cap
    const [regionalEquity, setRegionalEquity] = useState<boolean>(true)
    const [optResult, setOptResult] = useState<OptimizationResult | null>(null)
    const [errorMsg, setErrorMsg] = useState<string | null>(null)

    const [weights, setWeights] = useState<OptimizationWeights>({
        need: 0.30,
        marginal_impact: 0.30,
        cost_efficiency: 0.20,
        evidence: 0.10,
        scalability: 0.05,
        equity: 0.03,
        risk_penalty: 0.02,
    })

    const { data: projects, isLoading: projectsLoading } = useQuery<Project[]>({
        queryKey: ['projects'],
        queryFn: () => apiClient.get<Project[]>('/projects'),
    })

    const updateWeight = (key: keyof OptimizationWeights, val: number) => {
        const remainingKeys = (Object.keys(weights) as (keyof OptimizationWeights)[]).filter((k) => k !== key)
        const newRemainingTarget = 1.0 - val
        const oldRemainingSum = remainingKeys.reduce((sum, k) => sum + weights[k], 0)

        const newWeights: OptimizationWeights = { ...weights, [key]: val }

        if (oldRemainingSum > 0) {
            let currentSum = val
            for (let i = 0; i < remainingKeys.length; i++) {
                const k = remainingKeys[i]
                if (i === remainingKeys.length - 1) {
                    // Last key gets the exact remainder to ensure sum === 1.0000
                    newWeights[k] = Number((1.0 - currentSum).toFixed(4))
                } else {
                    const scaled = Number(((weights[k] / oldRemainingSum) * newRemainingTarget).toFixed(4))
                    newWeights[k] = scaled
                    currentSum += scaled
                }
            }
        }

        setWeights(newWeights)
    }

    const optimizeMutation = useMutation({
        mutationFn: async () => {
            setErrorMsg(null)
            const budgetPaise = Math.round(rupeesToPaise(budgetRupees))
            const projectIds = projects?.map((p) => p.project_id) || []

            if (projectIds.length === 0) {
                throw new Error("No candidate projects available in database for optimization.")
            }

            const res = await apiClient.post<OptimizationResult>('/optimization/runs', {
                budget_paise: budgetPaise,
                project_ids: projectIds,
                weights: weights,
                constraints: {
                    max_allocation_per_project_paise: Math.round(rupeesToPaise(maxPerProjectRupees)),
                    regional_equity_enabled: regionalEquity,
                },
            })
            return res
        },
        onSuccess: (res) => {
            setOptResult(res)
            setErrorMsg(null)
            queryClient.invalidateQueries({ queryKey: ['auditEvents'] })
            queryClient.setQueryData(['lastOptimizationRun'], res)
        },
        onError: (err: any) => {
            setErrorMsg(err.message || 'Optimization solver failed')
        },
    })

    const hasCandidateProjects = projects && projects.length > 0

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            {/* Header Hero */}
            <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-space-lg lg:p-space-xl shadow-sm border border-outline-variant/30">
                <div className="relative z-10 flex flex-col xl:flex-row xl:items-center justify-between gap-space-lg">
                    <div className="space-y-space-xs max-w-2xl">
                        <div className="inline-flex items-center gap-2 rounded-full bg-secondary/10 px-space-sm py-1 font-label-caps text-label-caps uppercase tracking-wider text-secondary">
                            <span className="h-2 w-2 animate-pulse rounded-full bg-secondary"></span>
                            <span>DECISION ENGINE CONFIGURATION</span>
                        </div>
                        <h1 className="font-display text-display tracking-tight text-on-surface">
                            MILP Budget Optimizer (`scipy-milp-v1`)
                        </h1>
                        <p className="font-body-lg text-body-lg text-on-surface-variant">
                            Configure and run SciPy Mixed-Integer Linear Programming solver maximizing concave piecewise marginal impact.
                        </p>
                    </div>
                </div>
            </div>

            {errorMsg && (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center space-x-3 text-rose-700 text-xs">
                    <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
                    <div>
                        <p className="font-semibold">Optimization Constraint Error</p>
                        <p>{errorMsg}</p>
                    </div>
                </div>
            )}

            {!projectsLoading && !hasCandidateProjects && (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center space-x-3 text-amber-800 text-xs">
                    <Info className="w-5 h-5 text-amber-600 shrink-0" />
                    <div>
                        <p className="font-semibold">No Candidate Projects Found</p>
                        <p>Upload a proposal or seed projects in PostgreSQL before running MILP optimization.</p>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 gap-space-lg lg:grid-cols-3">
                {/* Controls */}
                <div className="space-y-space-lg rounded-xl bg-surface-container-lowest p-space-lg shadow-sm border border-outline-variant/30 lg:col-span-1">
                    <div className="flex items-center gap-2 border-b border-outline-variant/30 pb-3">
                        <Settings2 className="h-5 w-5 text-secondary" />
                        <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Solver Parameters</h2>
                    </div>

                    <div className="space-y-2">
                        <label className="block font-label-md text-xs font-medium text-on-surface-variant flex justify-between">
                            <span>Total CSR Budget</span>
                            <span className="font-bold text-secondary">{formatPaise(rupeesToPaise(budgetRupees))}</span>
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
                            <span>Project Cap</span>
                            <span className="font-bold text-on-surface">{formatPaise(rupeesToPaise(maxPerProjectRupees))}</span>
                        </label>
                        <input
                            type="range"
                            min={1_00_00_000}
                            max={30_00_00_000}
                            step={1_00_00_000}
                            value={maxPerProjectRupees}
                            onChange={(e) => setMaxPerProjectRupees(Number(e.target.value))}
                            className="w-full accent-secondary"
                        />
                    </div>

                    <div className="flex items-center justify-between p-3 rounded bg-surface-container-low border border-outline-variant/30">
                        <span className="font-label-md text-xs text-on-surface font-medium">Regional Equity Floor (25% Underserved Target)</span>
                        <input
                            type="checkbox"
                            checked={regionalEquity}
                            onChange={(e) => setRegionalEquity(e.target.checked)}
                            className="w-4 h-4 rounded accent-secondary"
                        />
                    </div>

                    <div className="space-y-3 pt-2">
                        <label className="font-label-md text-xs font-semibold text-on-surface block">Objective Weights</label>

                        <div className="space-y-1 text-xs">
                            <div className="flex justify-between text-on-surface-variant">
                                <span>Marginal Social Impact</span>
                                <span className="font-mono text-on-surface font-bold">{(weights.marginal_impact * 100).toFixed(0)}%</span>
                            </div>
                            <input
                                type="range" min={0.05} max={0.60} step={0.05}
                                value={weights.marginal_impact}
                                onChange={(e) => updateWeight("marginal_impact", Number(e.target.value))}
                                className="w-full accent-secondary"
                            />
                        </div>

                        <div className="space-y-1 text-xs">
                            <div className="flex justify-between text-on-surface-variant">
                                <span>Socioeconomic Need</span>
                                <span className="font-mono text-on-surface font-bold">{(weights.need * 100).toFixed(0)}%</span>
                            </div>
                            <input
                                type="range" min={0.05} max={0.60} step={0.05}
                                value={weights.need}
                                onChange={(e) => updateWeight("need", Number(e.target.value))}
                                className="w-full accent-secondary"
                            />
                        </div>
                    </div>

                    <button
                        onClick={() => optimizeMutation.mutate()}
                        disabled={optimizeMutation.isPending || !hasCandidateProjects}
                        className="flex w-full items-center justify-center gap-2 rounded bg-secondary px-space-md py-3 font-label-md text-sm font-semibold text-on-secondary shadow-md transition hover:bg-on-secondary-container disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {optimizeMutation.isPending ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <Play className="h-4 w-4 fill-current" />
                        )}
                        <span>{optimizeMutation.isPending ? 'Running SciPy Solver...' : 'Execute MILP Optimization'}</span>
                    </button>
                </div>

                {/* Results Area */}
                <div className="flex min-h-[300px] flex-col overflow-hidden rounded-xl bg-surface-container-lowest p-space-lg shadow-sm border border-outline-variant/30 lg:col-span-2">
                    {!optResult && !optimizeMutation.isPending && (
                        <div className="flex h-full flex-col items-center justify-center space-y-4 text-center p-12">
                            <Settings2 className="h-12 w-12 text-on-surface-variant/30" />
                            <div>
                                <p className="font-headline-sm text-headline-sm font-semibold text-on-surface">Ready for Portfolio Optimization</p>
                                <p className="mt-1 font-body-sm text-body-sm text-on-surface-variant">Configure parameters on the left to compute optimal allocations across {projects?.length || 0} candidate projects.</p>
                            </div>
                        </div>
                    )}

                    {optimizeMutation.isPending && (
                        <div className="flex h-full flex-col items-center justify-center space-y-4 text-center p-12">
                            <Loader2 className="h-12 w-12 animate-spin text-secondary" />
                            <div>
                                <p className="font-headline-sm text-headline-sm font-semibold text-on-surface">SciPy MILP Decision Engine Active</p>
                                <p className="mt-1 font-body-sm text-body-sm text-on-surface-variant">Evaluating concave piecewise marginal impact across candidate projects...</p>
                            </div>
                        </div>
                    )}

                    {optResult && (
                        <div className="space-y-space-md">
                            <div className="flex items-center justify-between border-b border-outline-variant/30 pb-3">
                                <div>
                                    <span className="font-mono text-xs text-on-surface-variant">Run ID: <strong className="text-secondary">{optResult.run_id}</strong></span>
                                    <h3 className="font-headline-sm text-base font-bold text-on-surface mt-0.5">Optimal Fund Allocation Breakdown</h3>
                                </div>
                                <span className="px-3 py-1 rounded bg-emerald-500/20 text-emerald-700 font-label-caps text-xs font-bold border border-emerald-500/30">
                                    {optResult.status}
                                </span>
                            </div>

                            <div className="grid grid-cols-3 gap-3 text-xs font-mono">
                                <div className="p-3 rounded bg-surface-container-low border border-outline-variant/20">
                                    <span className="text-on-surface-variant">Total Pool</span>
                                    <p className="font-bold text-on-surface mt-0.5">{formatPaise(optResult.budget_paise)}</p>
                                </div>
                                <div className="p-3 rounded bg-surface-container-low border border-outline-variant/20">
                                    <span className="text-on-surface-variant">Allocated</span>
                                    <p className="font-bold text-secondary mt-0.5">{formatPaise(optResult.allocated_paise)}</p>
                                </div>
                                <div className="p-3 rounded bg-surface-container-low border border-outline-variant/20">
                                    <span className="text-on-surface-variant">Unallocated</span>
                                    <p className="font-bold text-on-surface-variant mt-0.5">{formatPaise(optResult.unallocated_paise)}</p>
                                </div>
                            </div>

                            <div className="overflow-x-auto pt-2">
                                <table className="w-full text-left font-body-md text-body-md">
                                    <thead className="bg-surface-container-low font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                                        <tr>
                                            <th className="px-space-md py-2.5">Project ID</th>
                                            <th className="px-space-md py-2.5">State</th>
                                            <th className="px-space-md py-2.5">Allocated Amount</th>
                                            <th className="px-space-md py-2.5">Marginal Score</th>
                                            <th className="px-space-md py-2.5">Reason Codes</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-outline-variant/20">
                                        {optResult.allocations.map((alloc) => (
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
                    )}
                </div>
            </div>
        </div>
    )
}

export default Optimization
