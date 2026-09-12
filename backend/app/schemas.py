"""Pydantic schemas for the LegalMetriX API contract."""

from typing import Optional

from pydantic import BaseModel


class LabelAnalysis(BaseModel):
    """Extracted legal-metrology fields from a packaged-commodity label.

    Fields mirror the prompt sent to Gemini. `None` means the model could not
    determine the value from the label image.
    """

    product_name: Optional[str] = None
    manufacturer_name: Optional[str] = None
    manufacturer_address: Optional[str] = None
    net_quantity: Optional[str] = None
    mrp: Optional[str] = None
    packing_date: Optional[str] = None
    import_date: Optional[str] = None
    customer_care: Optional[str] = None
    fssai_number: Optional[str] = None


class ScanResponse(BaseModel):
    """Successful response from POST /scan/upload."""

    success: bool = True
    filename: str
    analysis: LabelAnalysis