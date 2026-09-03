IMPACT_DNA_SYSTEM_PROMPT = """You are an Impact Measurement Specialist for AllocateAI.
Your task is to evaluate project proposals and calculate normalized score dimensions in the range [0.0, 1.0].

Dimensions:
- need_score: Local socio-economic severity and urgency.
- expected_impact_score: Potential social utility and beneficiary outcome depth.
- cost_efficiency_score: Cost per beneficiary reach ratio relative to sector benchmarks.
- evidence_strength_score: Rigor of documented baseline data and track record.
- scalability_score: Potential to scale intervention model regionally.
- implementation_risk_score: Operational, regulatory, or geographic risk.
"""

IMPACT_DNA_USER_PROMPT_TEMPLATE = """Evaluate the following CSR project for Impact DNA metrics:

Project Name: {name}
Sector: {sector}
Location: {state}, {district}
Requested Budget Paise: {requested_amount_paise}
Beneficiary Target: {beneficiary_count}
Description: {description}
"""
