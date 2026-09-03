import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import { Server, Database } from 'lucide-react'

export const Settings: React.FC = () => {
    const { data: health } = useQuery({
        queryKey: ['health'],
        queryFn: () => apiClient.get<any>('/health'),
    })

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            <div>
                <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                    SYSTEM CONFIGURATION
                </p>
                <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                    Platform Settings & Status
                </h1>
                <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                    View active backend environment configuration and engine status.
                </p>
            </div>

            <div className="grid grid-cols-1 gap-space-lg md:grid-cols-2">
                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm space-y-4">
                    <div className="flex items-center space-x-2 border-b border-outline-variant/30 pb-3">
                        <Server className="w-5 h-5 text-secondary" />
                        <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">FastAPI Backend Status</h2>
                    </div>

                    <div className="space-y-3 text-xs font-mono">
                        <div className="flex justify-between p-2.5 rounded bg-surface-container-low">
                            <span className="text-on-surface-variant">Service Name</span>
                            <span className="font-bold text-on-surface">{health?.service || 'AllocateAI Backend'}</span>
                        </div>
                        <div className="flex justify-between p-2.5 rounded bg-surface-container-low">
                            <span className="text-on-surface-variant">Environment</span>
                            <span className="font-bold text-secondary">{health?.environment || 'development'}</span>
                        </div>
                        <div className="flex justify-between p-2.5 rounded bg-surface-container-low">
                            <span className="text-on-surface-variant">Health Status</span>
                            <span className="font-bold text-emerald-700">{health?.status || 'healthy'}</span>
                        </div>
                        <div className="flex justify-between p-2.5 rounded bg-surface-container-low">
                            <span className="text-on-surface-variant">Version</span>
                            <span className="font-bold text-on-surface">{health?.version || '0.1.0'}</span>
                        </div>
                    </div>
                </div>

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm space-y-4">
                    <div className="flex items-center space-x-2 border-b border-outline-variant/30 pb-3">
                        <Database className="w-5 h-5 text-secondary" />
                        <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">PostgreSQL Database Status</h2>
                    </div>

                    <div className="space-y-3 text-xs font-mono">
                        <div className="flex justify-between p-2.5 rounded bg-surface-container-low">
                            <span className="text-on-surface-variant">Database Engine</span>
                            <span className="font-bold text-on-surface">PostgreSQL 18</span>
                        </div>
                        <div className="flex justify-between p-2.5 rounded bg-surface-container-low">
                            <span className="text-on-surface-variant">Connection Port</span>
                            <span className="font-bold text-on-surface">5433</span>
                        </div>
                        <div className="flex justify-between p-2.5 rounded bg-surface-container-low">
                            <span className="text-on-surface-variant">Alembic Migration HEAD</span>
                            <span className="font-bold text-secondary">53b46285e442</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Settings
