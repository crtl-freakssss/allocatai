"""Regional CSR saturation benchmarks and demographic capacity models."""

from typing import Dict

# Indicative baseline annual CSR benchmark funding per state (in paise)
# Used to determine saturation ratio: existing_csr / benchmark_csr
STATE_CSR_BENCHMARK_PAISE: Dict[str, int] = {
    # Industrially saturated / high historical CSR hubs
    "Maharashtra": 50_000_000_000,   # ₹500 Cr
    "Gujarat": 30_000_000_000,       # ₹300 Cr
    "Karnataka": 25_000_000_000,     # ₹250 Cr
    "Tamil Nadu": 25_000_000_000,    # ₹250 Cr
    "Delhi": 20_000_000_000,         # ₹200 Cr
    "Telangana": 15_000_000_000,     # ₹150 Cr
    # Moderately funded states
    "Rajasthan": 12_000_000_000,     # ₹120 Cr
    "Uttar Pradesh": 15_000_000_000, # ₹150 Cr
    "Madhya Pradesh": 10_000_000_000,# ₹100 Cr
    "Andhra Pradesh": 10_000_000_000,# ₹100 Cr
    "West Bengal": 10_000_000_000,   # ₹100 Cr
    "Punjab": 8_000_000_000,         # ₹80 Cr
    "Haryana": 10_000_000_000,       # ₹100 Cr
    # High-need / underserved regions
    "Bihar": 5_000_000_000,          # ₹50 Cr
    "Jharkhand": 4_000_000_000,      # ₹40 Cr
    "Odisha": 5_000_000_000,         # ₹50 Cr
    "Assam": 3_000_000_000,          # ₹30 Cr
    "Chhattisgarh": 4_000_000_000,   # ₹40 Cr
    "Uttarakhand": 3_000_000_000,    # ₹30 Cr
    "Himachal Pradesh": 2_000_000_000,# ₹20 Cr
}

DEFAULT_BENCHMARK_PAISE: int = 5_000_000_000  # ₹50 Cr default for other states/UTs
