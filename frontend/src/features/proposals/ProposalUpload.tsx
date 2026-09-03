import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import type { Proposal, ExtractionResult, ProposalDocument, NGO } from '../../types'
import { FileUp, Loader2, AlertCircle, Building2 } from 'lucide-react'

export const ProposalUpload: React.FC = () => {
    const navigate = useNavigate()
    const queryClient = useQueryClient()

    const [title, setTitle] = useState('Rural Clean Water & Sanitation Drive')
    const [organizationName, setOrganizationName] = useState('')
    const [selectedNgoId, setSelectedNgoId] = useState<string>('')
    const [file, setFile] = useState<File | null>(null)
    const [statusText, setStatusText] = useState('')
    const [errorMsg, setErrorMsg] = useState<string | null>(null)

    // Fetch registered NGOs from backend GET /api/v1/ngos
    const { data: ngos, isLoading: ngosLoading } = useQuery<NGO[]>({
        queryKey: ['ngos'],
        queryFn: () => apiClient.get<NGO[]>('/ngos'),
    })

    // Derive active NGO ID and Organization Name cleanly without effect setState
    const activeNgoId = selectedNgoId || (ngos && ngos.length > 0 ? ngos[0].id : '')
    const activeOrgName = organizationName || (ngos?.find(n => n.id === activeNgoId)?.name || '')

    const handleNgoChange = (ngoId: string) => {
        setSelectedNgoId(ngoId)
        const matched = ngos?.find((n) => n.id === ngoId)
        if (matched) {
            setOrganizationName(matched.name)
        }
    }

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selected = e.target.files?.[0]
        if (selected) {
            setErrorMsg(null)
            if (selected.type && !selected.type.includes('pdf')) {
                setErrorMsg('Only PDF files are supported.')
                return
            }
            if (selected.size > 20 * 1024 * 1024) {
                setErrorMsg('File size exceeds 20 MB limit.')
                return
            }
            setFile(selected)
        }
    }

    const uploadMutation = useMutation({
        mutationFn: async () => {
            setErrorMsg(null)

            let finalNgoId = activeNgoId
            if (!finalNgoId && ngos && ngos.length > 0) {
                finalNgoId = ngos[0].id
            }

            if (!finalNgoId) {
                // Fetch fresh from backend if state was empty
                const freshNgos = await apiClient.get<NGO[]>('/ngos')
                if (freshNgos && freshNgos.length > 0) {
                    finalNgoId = freshNgos[0].id
                }
            }

            if (!finalNgoId) {
                throw new Error("No registered NGO found in PostgreSQL database. Ensure backend seed data is loaded.")
            }

            if (!title.trim()) {
                throw new Error("Proposal title is required.")
            }

            if (!file) {
                throw new Error("PDF document is required.")
            }

            setStatusText('Creating proposal record in PostgreSQL...')

            // 1. Create proposal (POST /api/v1/proposals)
            const proposal = await apiClient.post<Proposal>('/proposals', {
                ngo_id: finalNgoId,
                title: title.trim(),
                source_type: "PDF_UPLOAD",
            })

            // 2. Attach document metadata (POST /api/v1/proposals/{id}/documents)
            setStatusText('Attaching PDF document metadata...')
            const fakeSha256 = Array.from({ length: 64 }, (_, i) => (i % 16).toString(16)).join('')
            const docRes = await apiClient.post<ProposalDocument>(`/proposals/${proposal.proposal_id}/documents`, {
                filename: file.name,
                mime_type: file.type || "application/pdf",
                storage_key: `uploads/${proposal.proposal_id}/${file.name}`,
                file_size_bytes: file.size,
                sha256: fakeSha256,
            })

            // 3. Trigger extraction (POST /api/v1/proposals/{id}/extract)
            setStatusText('Running AI extraction engine...')
            await apiClient.post<ExtractionResult>(`/proposals/${proposal.proposal_id}/extract`, {
                document_id: docRes.document_id,
            })

            return proposal
        },
        onSuccess: (proposal) => {
            queryClient.invalidateQueries({ queryKey: ['proposals'] })
            queryClient.invalidateQueries({ queryKey: ['projects'] })
            navigate(`/proposals/${proposal.proposal_id}`)
        },
        onError: (err: any) => {
            // Keep title, selected NGO, file, and form state intact for retry
            setErrorMsg(err.message || 'Failed to upload proposal')
            setStatusText('')
        },
    })

    return (
        <div className="mx-auto max-w-4xl space-y-space-xl">
            {/* Header */}
            <div>
                <p className="font-label-caps text-label-caps uppercase tracking-wider text-secondary">
                    PROPOSALS
                </p>
                <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                    Upload CSR Proposal
                </h1>
                <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                    Submit proposal metadata and attach a PDF to trigger canonical AI extraction.
                </p>
            </div>

            {errorMsg && (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between text-rose-700 text-xs">
                    <div className="flex items-center space-x-3">
                        <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
                        <div>
                            <p className="font-semibold">Upload Failure</p>
                            <p>{errorMsg}</p>
                        </div>
                    </div>
                    <button
                        type="button"
                        onClick={() => uploadMutation.mutate()}
                        className="px-3 py-1.5 rounded bg-rose-600 text-white font-semibold hover:bg-rose-700 transition shrink-0"
                    >
                        Retry Upload
                    </button>
                </div>
            )}

            {/* Upload Form Card */}
            <div className="rounded-xl border border-outline-variant/50 bg-surface-container-lowest p-8 shadow-sm space-y-6">
                <div className="space-y-4">
                    <div>
                        <label className="block font-label-md text-xs font-semibold text-on-surface-variant mb-1">Proposal Title</label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="w-full px-3 py-2 rounded border border-outline-variant/50 bg-surface-container-low text-sm text-on-surface focus:border-secondary focus:outline-none"
                            required
                        />
                    </div>

                    <div>
                        <label className="block font-label-md text-xs font-semibold text-on-surface-variant mb-1 flex items-center gap-1">
                            <Building2 className="w-3.5 h-3.5 text-secondary" />
                            <span>Select Registered NGO Partner {activeOrgName ? `(${activeOrgName})` : ''}</span>
                        </label>
                        {ngosLoading ? (
                            <div className="p-2 text-xs text-on-surface-variant animate-pulse">Loading registered NGOs from PostgreSQL...</div>
                        ) : !ngos || ngos.length === 0 ? (
                            <div className="p-3 rounded bg-amber-500/10 border border-amber-500/30 text-amber-700 text-xs flex items-center justify-between">
                                <span>No registered NGO found in PostgreSQL database. Ensure backend seed data is loaded.</span>
                                <button
                                    type="button"
                                    onClick={() => queryClient.invalidateQueries({ queryKey: ['ngos'] })}
                                    className="underline font-semibold"
                                >
                                    Reload NGOs
                                </button>
                            </div>
                        ) : (
                            <select
                                value={activeNgoId}
                                onChange={(e) => handleNgoChange(e.target.value)}
                                className="w-full px-3 py-2.5 rounded border border-outline-variant/50 bg-surface-container-low text-xs font-mono text-on-surface focus:border-secondary focus:outline-none"
                            >
                                {ngos.map((ngo) => (
                                    <option key={ngo.id} value={ngo.id}>
                                        {ngo.name} ({ngo.registration_number || ngo.external_id || ngo.id})
                                    </option>
                                ))}
                            </select>
                        )}
                    </div>
                </div>

                <label
                    htmlFor="proposal-file"
                    className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-outline-variant bg-surface-container-low px-6 py-12 text-center transition hover:border-secondary hover:bg-surface-container"
                >
                    <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-secondary/10 text-secondary">
                        <FileUp className="w-7 h-7" />
                    </div>

                    <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                        {file ? file.name : 'Upload Proposal PDF'}
                    </h2>

                    <p className="mt-1 font-body-sm text-body-sm text-on-surface-variant">
                        {file ? `${(file.size / (1024 * 1024)).toFixed(2)} MB PDF Selected` : 'Drag and drop a PDF here, or click to browse'}
                    </p>

                    <input
                        id="proposal-file"
                        type="file"
                        accept=".pdf,application/pdf"
                        className="hidden"
                        onChange={handleFileChange}
                    />
                </label>

                <button
                    type="button"
                    onClick={() => uploadMutation.mutate()}
                    disabled={uploadMutation.isPending || !title || !file || (ngosLoading && !activeNgoId)}
                    className="w-full rounded bg-secondary px-5 py-3 font-label-md text-sm font-semibold text-on-secondary shadow-sm transition hover:bg-on-secondary-container disabled:cursor-not-allowed disabled:opacity-40 flex items-center justify-center space-x-2"
                >
                    {uploadMutation.isPending ? (
                        <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>{statusText || 'Processing...'}</span>
                        </>
                    ) : (
                        <span>Upload & Run AI Extraction</span>
                    )}
                </button>
            </div>
        </div>
    )
}

export default ProposalUpload
