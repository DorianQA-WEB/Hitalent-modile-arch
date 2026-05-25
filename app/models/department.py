from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name : Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id : Mapped[int | None] = mapped_column(Integer,
                                                   ForeignKey('departments.id', ondelete="CASCADE"),
                                                   nullable=True)
    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False)
    employees : Mapped[list["Employee"]] = relationship("Employee", back_populates="department"
                                                        , cascade="all, delete-orphan")

    parent : Mapped["Department | None"]  = relationship(
        "Department",
        remote_side="Department.id",
        back_populates="children")
    children : Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="parent", cascade="all, delete-orphan")
