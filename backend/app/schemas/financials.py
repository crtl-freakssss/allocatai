from pydantic import BaseModel, Field


class Financials(BaseModel):
    """Project budget and funding structure in integer paise.

    Monetary values must never be represented as floating-point.
    1 Rupee = 100 paise.
    """

    requested_amount_paise: int = Field(
        ...,
        gt=0,
        strict=True,
        description="Total project funding requested in paise",
    )
    current_funding_paise: int = Field(
        default=0,
        ge=0,
        strict=True,
        description="Current committed funding for the project in paise",
    )
    other_funding_paise: int = Field(
        default=0,
        ge=0,
        strict=True,
        description="Other secured or co-funding in paise",
    )
