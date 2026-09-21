from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass(frozen=True)
class Customer:
    id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    pan_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None


@dataclass(frozen=True)
class Account:
    id: int
    customer_id: int
    account_number: str
    account_type: str
    balance: float
    status: str


@dataclass(frozen=True)
class Transaction:
    id: int
    account_id: int
    txn_type: str
    amount: float
    description: Optional[str]
    reference_id: Optional[str]
    created_at: Optional[datetime] = None


@dataclass(frozen=True)
class Loan:
    id: int
    customer_id: int
    loan_type: str
    principal: float
    interest_rate: float
    tenure_months: int
    emi: Optional[float]
    status: str


@dataclass(frozen=True)
class Card:
    id: int
    customer_id: int
    card_number: str
    card_type: str
    credit_limit: Optional[float]
    outstanding: Optional[float]
    status: str
    expiry_date: date


@dataclass(frozen=True)
class Complaint:
    id: int
    customer_id: int
    category: str
    subject: str
    description: str
    status: str
    priority: str
    resolution: Optional[str] = None
