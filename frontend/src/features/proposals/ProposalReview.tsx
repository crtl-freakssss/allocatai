import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import type { Proposal, ProposalDocument } from '../../types'
import { ArrowLeft, FileCode } from 'lucide-react'

export const ProposalReview: React.FC = () => {
    const { id } = useParams<{ id: string }>()

    const { data: proposal, isLoading, error } = useQuery<Proposal>({
        queryKey: ['proposal', id],
        queryFn: () => apiClient.get<Proposal>(`/proposals/${id}`),
        enabled: Boolean(id),
    })

    const { data: documents } = useQuery<ProposalDocument[]>({
        queryKey: ['proposalDocuments', id],
        queryFn: () => apiClient.get<ProposalDocument[]>(`/proposals/${id}/documents`),
        enabled: Boolean(id),
    })

    if (isLoading) {
        return <div className="p-8 text-center text-on-surface-variant font-body-md">Loading proposal details...</div>
    }

    if (error || !proposal) {
        return (
            <div className="p-8 text-center text-rose-500 font-body-md space-y-3">
                <p>Proposal with ID {id} not found.</p>
                <Link to="/proposals" className="text-secondary font-semibold hover:underline">← Back to Proposals</Link>
            </div>
        )
    }

    return (
        <div className="mx-auto max-w-4xl space-y-space-xl">
            <div className="flex items-center justify-between">
                <div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-secondary/10 px-3 py-1 font-label-caps text-xs text-secondary font-semibold">
                        <span>PROPOSAL {proposal.proposal_id}</span>
                    </div>
                    <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                        {proposal.title}
                    </h1>
                    <p className="mt-1 font-body-md text-on-surface-variant font-mono">
                        NGO ID: {proposal.ngo_id}
                    </p>
                </div>
                <Link to="/proposals" className="text-on-surface-variant hover:text-on-surface font-label-md text-sm font-semibold flex items-center gap-1">
                    <ArrowLeft className="w-4 h-4" /> Back to Proposals
                </Link>
            </div>

            <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-3 rounded bg-surface-container-low border border-outline-variant/20">
                        <span className="font-label-caps text-[10px] uppercase text-on-surface-variant">Status</span>
                        <p className="font-headline-sm text-sm font-bold text-secondary mt-0.5">{proposal.status}</p>
                    </div>
                    <div className="p-3 rounded bg-surface-container-low border border-outline-variant/20">
                        <span className="font-label-caps text-[10px] uppercase text-on-surface-variant">Source Channel</span>
                        <p className="font-headline-sm text-sm font-bold text-on-surface mt-0.5">{proposal.source_type}</p>
                    </div>
                    <div className="p-3 rounded bg-surface-container-low border border-outline-variant/20">
                        <span className="font-label-caps text-[10px] uppercase text-on-surface-variant">Documents Attached</span>
                        <p className="font-headline-sm text-sm font-bold text-on-surface mt-0.5">{documents?.length || 0} PDF File(s)</p>
                    </div>
                    <div className="p-3 rounded bg-surface-container-low border border-outline-variant/20">
                        <span className="font-label-caps text-[10px] uppercase text-on-surface-variant">Created At</span>
                        <p className="font-headline-sm text-xs font-semibold text-on-surface-variant mt-0.5">{new Date(proposal.created_at).toLocaleString()}</p>
                    </div>
                </div>

                <div className="space-y-3">
                    <h3 className="font-headline-sm text-sm font-semibold text-on-surface">Uploaded Documents</h3>
                    {documents?.map((doc) => (
                        <div key={doc.document_id} className="p-3 rounded-lg bg-surface-container-low border border-outline-variant/30 flex items-center justify-between text-xs font-mono">
                            <div className="flex items-center space-x-2">
                                <FileCode className="w-4 h-4 text-secondary" />
                                <div>
                                    <p className="font-bold text-on-surface">{doc.filename}</p>
                                    <p className="text-[10px] text-on-surface-variant">SHA256: {doc.sha256 ? doc.sha256.slice(0, 16) : ''}...</p>
                                </div>
                            </div>
                            <span className="text-on-surface-variant">{(doc.file_size_bytes / 1024).toFixed(1)} KB</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default ProposalReview
