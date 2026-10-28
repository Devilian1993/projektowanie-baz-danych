from decimal import Decimal
from typing import Annotated, List, Optional
from datetime import date, datetime

from sqlalchemy import (CheckConstraint, ForeignKey, Identity, Numeric, String, Text, func, text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import *

intpk = Annotated[int, mapped_column(Identity(always=False), primary_key=True)]

class PersonMixin:
    """Columns shared by client, trainer, receptionist, technician, administrator."""
    first_name:         Mapped[str]           = mapped_column(String(50))
    last_name:          Mapped[str]           = mapped_column(String(80))
    phone:              Mapped[Optional[str]] = mapped_column(String(15))

class UserAccount(Base):
    __tablename__ = "user_account"
    __table_args__ = (
        CheckConstraint("access_card_number >= 0", name="chk_account_card_number"),
        CheckConstraint("last_login_at >= created_at", name="chk_account_time_range"),
    )

    account_id:         Mapped[intpk]
    login:              Mapped[str]      = mapped_column(String(50), unique=True)
    email:              Mapped[str]      = mapped_column(String(254), unique=True)
    password_hash:      Mapped[str]      = mapped_column(String(255))
    access_card_number: Mapped[int]      = mapped_column(unique=True)
    is_active:          Mapped[bool]     = mapped_column(server_default=text("true"))
    created_at:         Mapped[datetime] = mapped_column(server_default=func.current_timestamp())
    last_login_at:      Mapped[Optional[datetime]]

    failed_logins: Mapped[List["FailedLogin"]] = relationship(
        back_populates="account", passive_deletes=True)
    entries: Mapped[List["Entry"]] = relationship(
        back_populates="account", passive_deletes=True)
    client: Mapped[Optional["Client"]] = relationship(
        back_populates="account", passive_deletes=True)
    trainer: Mapped[Optional["Trainer"]] = relationship(
        back_populates="account", passive_deletes=True)
    receptionist: Mapped[Optional["Receptionist"]] = relationship(
        back_populates="account", passive_deletes=True)
    technician: Mapped[Optional["Technician"]] = relationship(
        back_populates="account", passive_deletes=True)
    administrator: Mapped[Optional["Administrator"]] = relationship(
        back_populates="account", passive_deletes=True)

    def __repr__(self) -> str:
        return (
            f"UserAccount("
            f"account_id={self.account_id!r}, "
            f"login={self.login!r}, "
            f"email={self.email!r}, "
            f"access_card_number={self.access_card_number!r}, "
            f"is_active={self.is_active!r}, "
            f"created_at={self.created_at!r}, "
            f"last_login_at={self.last_login_at!r}"
            f")"
        )

class FailedLogin(Base):
    __tablename__ = "failed_login"

    attempt_id: Mapped[intpk]
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.account_id", ondelete="CASCADE"))
    attempted_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())

    account: Mapped["UserAccount"] = relationship(back_populates="failed_logins")

    def __repr__(self) -> str:
        return (
            f"FailedLogin("
            f"attempt_id={self.attempt_id!r}, "
            f"account_id={self.account_id!r}, "
            f"attempted_at={self.attempted_at!r}"
            f")"
        )

class Client(PersonMixin, Base):
    __tablename__ = "client"

    client_id: Mapped[intpk]
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.account_id", ondelete="CASCADE"), unique=True)
    registered_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())
    is_student: Mapped[bool] = mapped_column(server_default=text("false"))

    account: Mapped["UserAccount"] = relationship(back_populates="client")

    def __repr__(self) -> str:
        return (
            f"Client(client_id={self.client_id!r}, "
            f"account_id={self.account_id!r}, "
            f"first_name={self.first_name!r}, "
            f"last_name={self.last_name!r}, "
            f"registered_at={self.registered_at!r}, "
            f"is_student={self.is_student!r})"
        )

class Trainer(PersonMixin, Base):
    __tablename__ = "trainer"
    __table_args__ = (CheckConstraint("training_rate >= 0", name="chk_trainer_rate"),)

    trainer_id: Mapped[intpk]
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.account_id", ondelete="CASCADE"), unique=True)
    hire_date: Mapped[date] = mapped_column(server_default=func.current_date())
    training_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    account: Mapped["UserAccount"] = relationship(back_populates="trainer")
    specialization_links: Mapped[List["TrainerSpecialization"]] = relationship(
        back_populates="trainer", passive_deletes=True)

    def __repr__(self) -> str:
        return (
            f"Trainer(trainer_id={self.trainer_id!r}, "
            f"account_id={self.account_id!r}, "
            f"first_name={self.first_name!r}, "
            f"last_name={self.last_name!r}, "
            f"hire_date={self.hire_date!r}, "
            f"training_rate={self.training_rate!r})"
        )

class Receptionist(PersonMixin, Base):
    __tablename__ = "receptionist"

    receptionist_id: Mapped[intpk]
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.account_id", ondelete="CASCADE"), unique=True)
    hire_date: Mapped[date] = mapped_column(server_default=func.current_date())

    account: Mapped["UserAccount"] = relationship(back_populates="receptionist")

    def __repr__(self) -> str:
        return (
            f"Receptionist(receptionist_id={self.receptionist_id!r}, "
            f"account_id={self.account_id!r}, "
            f"first_name={self.first_name!r}, "
            f"last_name={self.last_name!r}, "
            f"hire_date={self.hire_date!r})"
        )

class Technician(PersonMixin, Base):
    __tablename__ = "technician"

    technician_id: Mapped[intpk]
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.account_id", ondelete="CASCADE"), unique=True)
    hire_date: Mapped[date] = mapped_column(server_default=func.current_date())

    account: Mapped["UserAccount"] = relationship(back_populates="technician")

    def __repr__(self) -> str:
        return (
            f"Technician(technician_id={self.technician_id!r}, "
            f"account_id={self.account_id!r}, "
            f"first_name={self.first_name!r}, "
            f"last_name={self.last_name!r}, "
            f"hire_date={self.hire_date!r})"
        )

class Administrator(PersonMixin, Base):
    __tablename__ = "administrator"

    administrator_id: Mapped[intpk]
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.account_id", ondelete="CASCADE"), unique=True)

    account: Mapped["UserAccount"] = relationship(back_populates="administrator")

    def __repr__(self) -> str:
        return (
            f"Administrator(administrator_id={self.administrator_id!r}, "
            f"account_id={self.account_id!r}, "
            f"first_name={self.first_name!r}, "
            f"last_name={self.last_name!r})"
        )

class Entry(Base):
    __tablename__ = "entry"
    __table_args__ = (
        CheckConstraint("exited_at > entered_at", name="chk_entry_time_range"),
        CheckConstraint("result OR exited_at IS NULL", name="chk_entry_result"),
        CheckConstraint("result = (denial_reason IS NULL)", name="chk_entry_reason"),
    )

    entry_id: Mapped[intpk]
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.account_id", ondelete="CASCADE"))
    entered_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())
    exited_at: Mapped[Optional[datetime]]
    result: Mapped[bool]
    denial_reason: Mapped[Optional[str]] = mapped_column(String(255))

    account: Mapped["UserAccount"] = relationship(back_populates="entries")

    def __repr__(self) -> str:
        return (
            f"Entry(entry_id={self.entry_id!r}, "
            f"account_id={self.account_id!r}, "
            f"entered_at={self.entered_at!r}, "
            f"exited_at={self.exited_at!r}, "
            f"result={self.result!r}, "
            f"denial_reason={self.denial_reason!r})"
        )

class Specialization(Base):
    __tablename__ = "specialization"

    specialization_id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    trainer_links: Mapped[List["TrainerSpecialization"]] = relationship(
        back_populates="specialization", passive_deletes=True)

    def __repr__(self) -> str:
        return (
            f"Specialization(specialization_id={self.specialization_id!r}, "
            f"name={self.name!r}, "
            f"description={self.description!r})"
        )

class TrainerSpecialization(Base):
    __tablename__ = "trainer_specialization"

    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainer.trainer_id", ondelete="CASCADE"),
        primary_key=True, autoincrement=False)
    specialization_id: Mapped[int] = mapped_column(
        ForeignKey("specialization.specialization_id", ondelete="CASCADE"),
        primary_key=True, autoincrement=False)

    trainer: Mapped["Trainer"] = relationship(back_populates="specialization_links")
    specialization: Mapped["Specialization"] = relationship(back_populates="trainer_links")

    def __repr__(self) -> str:
        return (
            f"TrainerSpecialization("
            f"trainer_id={self.trainer_id!r}, "
            f"specialization_id={self.specialization_id!r})"
        )
