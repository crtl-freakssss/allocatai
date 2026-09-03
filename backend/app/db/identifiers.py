from typing import Set

# Standard AllocateAI contract prefixes
STANDARD_PREFIXES: Set[str] = {
    "ORG",  # Organization
    "USR",  # User
    "NGO",  # NGO
    "PRO",  # Proposal
    "DOC",  # Document
    "PRJ",  # Project
    "OPT",  # OptimizationRun
    "REA",  # ReallocationRun
    "AUD",  # AuditEvent
    "DD",   # DueDiligenceReport
    "DNA",  # ImpactDNA
}


def generate_public_id(prefix: str, sequence_number: int) -> str:
    """Generate a deterministic sequential public identifier according to the AllocateAI contract.

    Format:
        PREFIX-0001
        PREFIX-0002
        etc.

    Args:
        prefix: Entity prefix. Must be one of:
                ORG, USR, NGO, PRO, DOC, PRJ, OPT, REA, AUD, DD, DNA.
        sequence_number: Positive integer representing the sequence position (1-indexed).

    Returns:
        Deterministic formatted string (e.g. 'PRJ-0001', 'PRO-0042').

    Raises:
        ValueError: If prefix is not in the contract or sequence_number < 1.
    """
    clean_prefix = prefix.strip().upper()
    if clean_prefix not in STANDARD_PREFIXES:
        raise ValueError(
            f"Invalid public ID prefix '{prefix}'. Must be one of: {sorted(STANDARD_PREFIXES)}"
        )

    if not isinstance(sequence_number, int) or sequence_number < 1:
        raise ValueError(
            f"sequence_number must be a positive integer >= 1, got {sequence_number}"
        )

    return f"{clean_prefix}-{sequence_number:04d}"
