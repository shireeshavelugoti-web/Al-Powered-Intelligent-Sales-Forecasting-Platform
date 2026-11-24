# 
from datetime import datetime
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    Float
)
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    company_name: Mapped[str] = mapped_column(
        String(200),
        index=True
    )

    industry: Mapped[str] = mapped_column(
        String(120),
        index=True
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
        String(40),
        nullable=True
    )

    website: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    employee_count: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True
    )

    location: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    technology_stack: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(40),
        default="New",
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class CompanyAnalysis(Base):

    __tablename__ = "company_analyses"

    id: Mapped[int] = mapped_column(Integer,
        primary_key=True,
        index=True
    )

    lead_id: Mapped[int] = mapped_column(
        Integer,
        index=True
    )

    company_overview: Mapped[str] = mapped_column(Text)
    business_needs: Mapped[str] = mapped_column(Text)
    opportunities: Mapped[str] = mapped_column(Text)
    industry_analysis: Mapped[str] = mapped_column(Text)
    qualification_score: Mapped[int] = mapped_column(Integer)
    recommended_action: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


class OutreachEmail(Base):

    __tablename__ = "outreach_emails"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id"), index=True
    )

    recipient: Mapped[str] = mapped_column(
        String(255), index=True
    )

    subject: Mapped[str] = mapped_column(
        String(255)
    )

    body: Mapped[str] = mapped_column(
        Text
    )

    tone: Mapped[str] = mapped_column(
        String(50), default="Professional"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )


class LeadScore(Base):

    __tablename__ = "lead_scores"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id"), index=True
    )

    company_growth: Mapped[int] = mapped_column(
        Integer
    )

    industry_match: Mapped[int] = mapped_column(
        Integer
    )

    technology_alignment: Mapped[int] = mapped_column(
        Integer
    )

    business_need: Mapped[int] = mapped_column(
        Integer
    )

    engagement_level: Mapped[int] = mapped_column(
        Integer
    )

    total_score: Mapped[int] = mapped_column(
        Integer
    )

    priority: Mapped[str] = mapped_column(
        String(50)
    )

    conversation_probability: Mapped[float] = mapped_column(
        Float, nullable=True
    )

    probability_source: Mapped[str] = mapped_column(
        String(100), nullable=True, default="not_available"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )


class OutreachRecommendation(Base):

    __tablename__ = "outreach_recommendations"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id"), index=True
    )

    channel: Mapped[str] = mapped_column(
        String(50)
    )

    follow_up_timing: Mapped[str] = mapped_column(
        String(50)
    )

    strategy: Mapped[str] = mapped_column(
        Text
    )

    next_action: Mapped[str] = mapped_column(
        Text
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
