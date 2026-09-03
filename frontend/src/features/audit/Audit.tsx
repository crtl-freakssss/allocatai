import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import type { AuditEvent } from '../../types'
import { Calendar, ChevronDown } from 'lucide-react'

export const Audit: React.FC = () => {
    const [expandedRow, setExpandedRow] = useState<string | null>(null)

    const { data: events, isLoading } = useQuery<AuditEvent[]>({
        queryKey: ['auditEvents'],
        queryFn: () => apiClient.get<AuditEvent[]>('/audit/events'),
    })

    const toggleRow = (id: string) => {
        setExpandedRow(expandedRow === id ? null : id)
    }

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            <div>
                <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                    COMPLIANCE & TRACEABILITY
                </p>
                <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                    Audit & History Log
                </h1>
                <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                    System is immutable and fully auditable. Review past decision engine runs and request IDs stored in PostgreSQL.
                </p>
            </div>

            {isLoading ? (
                <div className="p-12 text-center text-on-surface-variant font-body-md">Loading append-only audit trail from PostgreSQL...</div>
            ) : (
                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest shadow-sm overflow-hidden">
                    <table className="w-full text-left font-body-md text-body-md">
                        <thead className="bg-surface-container-low font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant border-b border-outline-variant/30">
                            <tr>
                                <th className="px-space-md py-3 w-12"></th>
                                <th className="px-space-md py-3">Timestamp</th>
                                <th className="px-space-md py-3">Event Type</th>
                                <th className="px-space-md py-3">Entity Type</th>
                                <th className="px-space-md py-3">Entity ID</th>
                                <th className="px-space-md py-3">Request ID</th>
                            </tr>
                        </thead>
                        <tbody>
                            {events?.map((evt) => {
                                const id = evt.public_id || (evt as any).event_id
                                const timestamp = evt.created_at || (evt as any).timestamp
                                const details = evt.payload || (evt as any).details

                                return (
                                    <React.Fragment key={id}>
                                        <tr 
                                            className="border-b border-outline-variant/20 cursor-pointer hover:bg-surface-container-low/50 transition-colors"
                                            onClick={() => toggleRow(id)}
                                        >
                                            <td className="px-space-md py-space-md text-on-surface-variant">
                                                <ChevronDown className={`h-4 w-4 transition-transform ${expandedRow === id ? 'rotate-180' : ''}`} />
                                            </td>
                                            <td className="px-space-md py-space-md text-on-surface">
                                                <div className="flex items-center space-x-2">
                                                    <Calendar className="h-4 w-4 text-on-surface-variant" />
                                                    <span>{timestamp ? new Date(timestamp).toLocaleString() : 'N/A'}</span>
                                                </div>
                                            </td>
                                            <td className="px-space-md py-space-md font-semibold text-secondary">{evt.event_type}</td>
                                            <td className="px-space-md py-space-md text-on-surface-variant">{evt.entity_type}</td>
                                            <td className="px-space-md py-space-md font-mono text-xs text-on-surface">{evt.entity_id || 'N/A'}</td>
                                            <td className="px-space-md py-space-md font-mono text-xs text-on-surface-variant">{evt.request_id}</td>
                                        </tr>
                                        {expandedRow === id && (
                                            <tr className="bg-surface-container-low/80">
                                                <td colSpan={6} className="px-space-md py-3">
                                                    <pre className="font-mono text-[11px] text-on-surface-variant overflow-x-auto p-3 rounded bg-surface-container-lowest border border-outline-variant/30">
                                                        {JSON.stringify(details, null, 2)}
                                                    </pre>
                                                </td>
                                            </tr>
                                        )}
                                    </React.Fragment>
                                )
                            })}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )
}

export default Audit
