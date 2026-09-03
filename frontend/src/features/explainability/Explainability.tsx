import React from 'react'

export const Explainability: React.FC = () => {
    return (
        <div className="flex w-full flex-col space-y-space-xl">
            <div>
                <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                    TRANSPARENCY & AUDITABILITY
                </p>
                <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                    Decision Engine Explainability
                </h1>
                <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                    The decision engine is fully deterministic and auditable. It does not hide allocations behind opaque black box models.
                </p>
            </div>

            <div className="grid grid-cols-1 gap-space-lg lg:grid-cols-3">
                {/* Left Column */}
                <div className="space-y-space-lg lg:col-span-1">
                    <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm space-y-4">
                        <h2 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Engine Version Specifications</h2>
                        <div className="space-y-3 text-xs font-mono">
                            <div className="p-2.5 rounded bg-surface-container-low border border-outline-variant/20">
                                <span className="text-on-surface-variant block text-[10px]">SOLVER</span>
                                <span className="font-bold text-secondary">scipy-milp-v1</span>
                            </div>
                            <div className="p-2.5 rounded bg-surface-container-low border border-outline-variant/20">
                                <span className="text-on-surface-variant block text-[10px]">SCORING ENGINE</span>
                                <span className="font-bold text-on-surface">scoring-v1</span>
                            </div>
                            <div className="p-2.5 rounded bg-surface-container-low border border-outline-variant/20">
                                <span className="text-on-surface-variant block text-[10px]">SATURATION ENGINE</span>
                                <span className="font-bold text-on-surface">sat-v1</span>
                            </div>
                            <div className="p-2.5 rounded bg-surface-container-low border border-outline-variant/20">
                                <span className="text-on-surface-variant block text-[10px]">MARGINAL CALCULATOR</span>
                                <span className="font-bold text-on-surface">marginal-v1</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column */}
                <div className="space-y-space-lg lg:col-span-2">
                    <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm space-y-4">
                        <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                            Active Reason Codes & Constraints
                        </h2>
                        <p className="font-body-md text-sm text-on-surface-variant">
                            Every allocated rupee is justified by statutory compliance, socioeconomic need, marginal utility, and regional equity targets.
                        </p>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                            <div className="p-3 rounded-lg bg-surface-container-low border border-outline-variant/30">
                                <span className="font-bold text-secondary">HIGH_MARGINAL_IMPACT</span>
                                <p className="text-[11px] text-on-surface-variant mt-1">Project exhibits high incremental social utility per tranche before regional saturation decay.</p>
                            </div>
                            <div className="p-3 rounded-lg bg-surface-container-low border border-outline-variant/30">
                                <span className="font-bold text-secondary">LOW_SATURATION</span>
                                <p className="text-[11px] text-on-surface-variant mt-1">Target state interventions are currently below national benchmark capacity.</p>
                            </div>
                            <div className="p-3 rounded-lg bg-surface-container-low border border-outline-variant/30">
                                <span className="font-bold text-secondary">HIGH_NEED</span>
                                <p className="text-[11px] text-on-surface-variant mt-1">Intervention addresses acute multidimensional socioeconomic vulnerability index.</p>
                            </div>
                            <div className="p-3 rounded-lg bg-surface-container-low border border-outline-variant/30">
                                <span className="font-bold text-secondary">REGIONAL_EQUITY_FLOOR</span>
                                <p className="text-[11px] text-on-surface-variant mt-1">Constraint enforcing minimum 25% allocation share to underserved regions.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Explainability
