"""
===========================================================================
File: schemas.py

Project: ProcureMind AI
Author : Kavin Gupta

Purpose:
--------
This file defines all data models used in the project.

Every request received by the FastAPI backend is validated
using these Pydantic schemas before reaching business logic.

Using Pydantic ensures:
1. Correct data types
2. Required fields are present
3. Invalid data is rejected early
4. Business logic receives clean and validated data
===========================================================================
"""

from pydantic import BaseModel, Field


# -------------------------------------------------------------------------
# RFQItem
#
# Represents one item required by the buyer.
#
# Example:
# Laptop
# Quantity: 20
# RAM: 16 GB
# Storage: 512 GB SSD
# -------------------------------------------------------------------------

class RFQItem(BaseModel):

    item_name: str = Field(
        min_length=2
    )

    required_quantity: int = Field(
        gt=0
    )

    specifications: dict = Field(
        default_factory=dict
    )


# -------------------------------------------------------------------------
# QuotationLineItem
#
# Represents one product offered by a vendor.
#
# It stores:
# - Product name
# - Offered quantity
# - Unit price
# - Offered technical specifications
# -------------------------------------------------------------------------

class QuotationLineItem(BaseModel):

    item_name: str = Field(
        min_length=2
    )

    quoted_quantity: int = Field(
        gt=0
    )

    unit_price: float = Field(
        gt=0
    )

    specifications: dict = Field(
        default_factory=dict
    )


# -------------------------------------------------------------------------
# RFQ
#
# Represents the buyer's complete Request for Quotation.
#
# It stores:
# - RFQ title
# - Department
# - Currency
# - Required delivery timeline
# - Required warranty
# - List of required products
# -------------------------------------------------------------------------

class RFQ(BaseModel):

    rfq_title: str = Field(
        min_length=3
    )

    department: str = Field(
        min_length=2
    )

    currency: str = "INR"

    required_delivery_days: int = Field(
        gt=0
    )

    required_warranty_months: int = Field(
        ge=0
    )

    items: list[RFQItem]


# -------------------------------------------------------------------------
# VendorQuotation
#
# Represents the complete quotation submitted by one vendor.
#
# It stores:
# - Vendor name
# - Currency
# - Delivery time
# - Warranty
# - Payment terms
# - Technical compliance percentage
# - Past rating
# - List of quoted products
# -------------------------------------------------------------------------

class VendorQuotation(BaseModel):

    vendor_name: str = Field(
        min_length=2
    )

    currency: str = "INR"

    delivery_days: int = Field(
        gt=0
    )

    warranty_months: int = Field(
        ge=0
    )

    payment_terms_days: int = Field(
        ge=0
    )

    technical_compliance_percent: float = Field(
        ge=0,
        le=100
    )

    past_rating: float = Field(
        ge=0,
        le=5
    )

    line_items: list[QuotationLineItem]


# -------------------------------------------------------------------------
# VendorScore
#
# Stores calculated vendor scores and final ranking.
# -------------------------------------------------------------------------

class VendorScore(BaseModel):

    vendor_name: str

    subtotal: float

    price_score: float

    delivery_score: float

    compliance_score: float

    past_rating_score: float

    warranty_score: float

    final_score: float

    rank: int


# -------------------------------------------------------------------------
# ComparisonResult
#
# Represents the final vendor comparison response.
# -------------------------------------------------------------------------

class ComparisonResult(BaseModel):

    best_vendor: str

    rankings: list[VendorScore]


# =========================================================================
# schemas.py Summary
# =========================================================================

# 1. RFQItem stores one buyer requirement.

# 2. QuotationLineItem stores one product offered by a vendor.

# 3. Both RFQ and vendor line items now store technical specifications.

# 4. RFQ stores required delivery days and required warranty months.

# 5. VendorQuotation stores the complete vendor offer.

# 6. VendorScore stores calculated procurement scores.

# 7. ComparisonResult returns the best vendor and full ranking.