from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database.db import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True)
    subject = Column(String(500))
    sender = Column(String(200))
    received_at = Column(DateTime)
    raw_body = Column(Text)
    category = Column(String(50))          # tonnage | cargo_vc | cargo_tc | unknown
    confidence = Column(Float, default=0.0)
    is_duplicate = Column(Boolean, default=False)
    fingerprint = Column(String(64), nullable=True, index=True)  # SHA-256 of normalised body
    created_at = Column(DateTime, default=_utcnow)

    tonnage = relationship("Tonnage", back_populates="email", cascade="all, delete-orphan")
    cargo_vc = relationship("CargoVC", back_populates="email", cascade="all, delete-orphan")
    cargo_tc = relationship("CargoTC", back_populates="email", cascade="all, delete-orphan")

    def to_dict(self, include_extracted=False):
        d = {
            "id": self.id,
            "subject": self.subject,
            "sender": self.sender,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "raw_body": self.raw_body,
            "category": self.category,
            "confidence": round(self.confidence or 0, 3),
            "is_duplicate": self.is_duplicate,
            "fingerprint": self.fingerprint,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_extracted:
            d["tonnage"] = [t.to_dict() for t in self.tonnage]
            d["cargo_vc"] = [c.to_dict() for c in self.cargo_vc]
            d["cargo_tc"] = [c.to_dict() for c in self.cargo_tc]
        return d


class Tonnage(Base):
    __tablename__ = "tonnage"

    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    vessel_name = Column(String(200))
    account_name = Column(String(200))
    open_port = Column(String(200))
    open_date = Column(String(100))
    vessel_type = Column(String(100))
    vessel_size = Column(String(100))
    flag = Column(String(100))
    built_year = Column(String(20))
    class_society = Column(String(100))
    loa = Column(String(50))
    beam = Column(String(50))

    email = relationship("Email", back_populates="tonnage")

    def to_dict(self):
        return {
            "id": self.id,
            "email_id": self.email_id,
            "vessel_name": self.vessel_name,
            "account_name": self.account_name,
            "open_port": self.open_port,
            "open_date": self.open_date,
            "vessel_type": self.vessel_type,
            "vessel_size": self.vessel_size,
            "flag": self.flag,
            "built_year": self.built_year,
            "class_society": self.class_society,
            "loa": self.loa,
            "beam": self.beam,
        }


class CargoVC(Base):
    __tablename__ = "cargo_vc"

    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    account_name = Column(String(200))
    cargo_name = Column(String(200))
    loading_port = Column(String(200))
    discharge_port = Column(String(200))
    laycan = Column(String(100))
    cargo_type = Column(String(100))
    quantity = Column(String(100))

    email = relationship("Email", back_populates="cargo_vc")

    def to_dict(self):
        return {
            "id": self.id,
            "email_id": self.email_id,
            "account_name": self.account_name,
            "cargo_name": self.cargo_name,
            "loading_port": self.loading_port,
            "discharge_port": self.discharge_port,
            "laycan": self.laycan,
            "cargo_type": self.cargo_type,
            "quantity": self.quantity,
        }


class CargoTC(Base):
    __tablename__ = "cargo_tc"

    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    account_name = Column(String(200))
    cargo_name = Column(String(200))
    delivery_port = Column(String(200))
    redelivery_port = Column(String(200))
    duration = Column(String(100))
    laycan = Column(String(100))
    cargo_type = Column(String(100))

    email = relationship("Email", back_populates="cargo_tc")

    def to_dict(self):
        return {
            "id": self.id,
            "email_id": self.email_id,
            "account_name": self.account_name,
            "cargo_name": self.cargo_name,
            "delivery_port": self.delivery_port,
            "redelivery_port": self.redelivery_port,
            "duration": self.duration,
            "laycan": self.laycan,
            "cargo_type": self.cargo_type,
        }
