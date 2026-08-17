from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Float,
    Text
)

from sqlalchemy.orm import (
    mapped_column,
    Mapped
)

from app.database.database import Base


# =========================================================================
# User Model
# =========================================================================

class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(50),
        default="buyer",
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


# =========================================================================
# RFQ Record
# =========================================================================

class RFQRecord(Base):

    __tablename__ = "rfq_records"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    rfq_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    structured_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


# =========================================================================
# Vendor Model
# =========================================================================

class Vendor(Base):

    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    company_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    contact_person: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    gst_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    rating: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


# =========================================================================
# Vendor Quotation Record
# =========================================================================

class VendorQuotationRecord(Base):

    __tablename__ = "vendor_quotation_records"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    rfq_id: Mapped[int] = mapped_column(
        ForeignKey("rfq_records.id"),
        nullable=False,
        index=True
    )

    vendor_id: Mapped[int] = mapped_column(
        ForeignKey("vendors.id"),
        nullable=False,
        index=True
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    subtotal: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    compliance_percentage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    final_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    rank: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )

    structured_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    compliance_report: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


# =========================================================================
# Comparison Result Record
# =========================================================================

class ComparisonResultRecord(Base):

    __tablename__ = "comparison_result_records"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    rfq_id: Mapped[int] = mapped_column(
        ForeignKey("rfq_records.id"),
        nullable=False,
        unique=True,
        index=True
    )

    best_vendor: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    final_decision: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    executive_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    scoring_result: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    ai_recommendation: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

# =========================================================================
# Human Approval Record (B2B workflow)
# =========================================================================

class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    rfq_id: Mapped[int] = mapped_column(
        ForeignKey("rfq_records.id"), nullable=False, unique=True, index=True
    )
    requested_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    approver_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# =========================================================================
# Contract Record (lightweight contract analytics)
# =========================================================================

class ContractRecord(Base):
    __tablename__ = "contract_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(20), default="INR", nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False, index=True)
    terms: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
