/**
 * Converts integer paise to rupees (1 Rupee = 100 Paise).
 */
export function paiseToRupees(paise: number): number {
  return paise / 100;
}

/**
 * Converts rupees to integer paise (1 Rupee = 100 Paise).
 */
export function rupeesToPaise(rupees: number): number {
  return Math.round(rupees * 100);
}

/**
 * Formats integer paise into a human-readable Indian Rupee string (e.g. ₹5,00,000 or ₹1.5 Cr).
 */
export function formatPaise(paise: number, compact: boolean = false): string {
  const rupees = paiseToRupees(paise);

  if (compact) {
    if (rupees >= 1_00_00_000) {
      return `₹${(rupees / 1_00_00_000).toFixed(2)} Cr`;
    }
    if (rupees >= 1_00_000) {
      return `₹${(rupees / 1_00_000).toFixed(2)} Lakh`;
    }
  }

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(rupees);
}

/**
 * Formats a score in [0.0, 1.0] to a percentage string (e.g. 85.4%).
 */
export function formatScore(score: number): string {
  return `${(score * 100).toFixed(1)}%`;
}
