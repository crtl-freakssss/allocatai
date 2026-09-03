import os
import re
from typing import Dict, Any, List, Optional


class DocumentParser:
    """Parses raw text, numbers, and tabular data from documents and storage locations."""

    @classmethod
    def parse_text(cls, storage_key: str, filename: str) -> str:
        """Extract text from local file if exists, or generate fallback representation from key."""
        if os.path.exists(storage_key):
            try:
                with open(storage_key, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception:
                pass

        # Fallback text representation from filename/path
        clean_name = filename.replace("_", " ").replace("-", " ").replace(".pdf", "")
        return f"Proposal Document: {clean_name}\nProposed Budget: ₹50,00,000"

    @classmethod
    def extract_financials(cls, text: str) -> int:
        """Regex-based financial quantity extraction in paise."""
        # Check for Crore (e.g. 5 Cr, 5.5 Crore)
        cr_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:cr|crore)", text, re.IGNORECASE)
        if cr_match:
            cr_val = float(cr_match.group(1))
            return int(cr_val * 100_00_000 * 100)

        # Check for Lakh (e.g. 50 Lakh, 75 Lakhs)
        lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac)", text, re.IGNORECASE)
        if lakh_match:
            lakh_val = float(lakh_match.group(1))
            return int(lakh_val * 100_000 * 100)

        # Default standard project requested amount: ₹50 Lakhs = 500,000,000 paise
        return 500_000_000
