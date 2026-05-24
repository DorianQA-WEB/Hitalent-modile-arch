from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    department_id : Mapped[int] = mapped_column(Integer, ForeignKey('departments.id'))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position : Mapped[str] = mapped_column(String(255), nullable=False)
    hired_at : Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)
    department : Mapped["Department"] = relationship("Department", back_populates="employees")