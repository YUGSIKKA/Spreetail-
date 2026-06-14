from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Date, Numeric, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    memberships = relationship("GroupMembership", back_populates="group")
    expenses = relationship("Expense", back_populates="group")
    settlements = relationship("Settlement", back_populates="group")

class GroupMembership(Base):
    __tablename__ = "group_memberships"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    left_at = Column(DateTime(timezone=True), nullable=True) # NULL means still active
    
    group = relationship("Group", back_populates="memberships")
    user = relationship("User")

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    description = Column(String(255), nullable=False)
    paid_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    amount_inr = Column(Numeric(10, 2), nullable=False)
    original_amount = Column(Numeric(10, 2), nullable=False)
    original_currency = Column(String(10), nullable=False)
    usd_rate_used = Column(Numeric(10, 4), nullable=True)
    split_type = Column(String(50), nullable=False) # 'equal', 'unequal', 'percentage', 'share'
    expense_date = Column(Date, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    import_row_number = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    group = relationship("Group", back_populates="expenses")
    payer = relationship("User")
    participants = relationship("ExpenseParticipant", back_populates="expense")

class ExpenseParticipant(Base):
    __tablename__ = "expense_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    share_amount_inr = Column(Numeric(10, 2), nullable=False)
    share_raw = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    expense = relationship("Expense", back_populates="participants")
    user = relationship("User")

class Settlement(Base):
    __tablename__ = "settlements"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    paid_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    paid_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount_inr = Column(Numeric(10, 2), nullable=False)
    settlement_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    group = relationship("Group", back_populates="settlements")
    payer = relationship("User", foreign_keys=[paid_by_user_id])
    payee = relationship("User", foreign_keys=[paid_to_user_id])

class ImportSession(Base):
    __tablename__ = "import_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())
    imported_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_rows = Column(Integer, nullable=False, default=0)
    imported_count = Column(Integer, nullable=False, default=0)
    flagged_count = Column(Integer, nullable=False, default=0)
    skipped_count = Column(Integer, nullable=False, default=0)
    
    importer = relationship("User")
    anomalies = relationship("ImportAnomaly", back_populates="session")

class ImportAnomaly(Base):
    __tablename__ = "import_anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    import_session_id = Column(Integer, ForeignKey("import_sessions.id"), nullable=False)
    row_number = Column(Integer, nullable=False)
    raw_row = Column(Text, nullable=False)
    anomaly_type = Column(String(100), nullable=False)
    anomaly_detail = Column(Text, nullable=False)
    action_taken = Column(String(50), nullable=False) # 'imported_with_fix', 'flagged_for_review', 'skipped'
    resolution = Column(Text, nullable=True)
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    session = relationship("ImportSession", back_populates="anomalies")
    approver = relationship("User")
