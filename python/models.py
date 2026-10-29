from decimal import Decimal
from typing import Annotated, List, Optional
from datetime import date, datetime, time

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



class Room(Base):
    __tablename__ = "room"
    __table_args__ = (
        CheckConstraint("number >= 0", name="chk_room_number"),
        CheckConstraint("area > 0", name="chk_room_area"),
        CheckConstraint("max_occupancy > 0", name="chk_room_max_occupancy"),
        CheckConstraint("closing_time > opening_time", name="chk_room_time_range"),
    )

    room_id:       Mapped[intpk]
    number:        Mapped[int]             = mapped_column(unique=True)
    name:          Mapped[str]             = mapped_column(String(100), unique=True)
    area:          Mapped[Optional[Decimal]] = mapped_column(Numeric(7, 2))
    max_occupancy: Mapped[int]
    opening_time:  Mapped[time]   = mapped_column(server_default=text("'00:00'"))
    closing_time:  Mapped[time]   = mapped_column(server_default=text("'23:59:59'"))
    is_active:     Mapped[bool]            = mapped_column(server_default=text("true"))

    stations: Mapped[List["Station"]] = relationship(
        back_populates="room", passive_deletes=True)

    def __repr__(self) -> str:
        return (
            f"Room(room_id={self.room_id!r}, "
            f"number={self.number!r}, "
            f"name={self.name!r}, "
            f"area={self.area!r}, "
            f"max_occupancy={self.max_occupancy!r}, "
            f"opening_time={self.opening_time!r}, "
            f"closing_time={self.closing_time!r}, "
            f"is_active={self.is_active!r})"
        )


class EquipmentCategory(Base):
    __tablename__ = "equipment_category"

    category_id: Mapped[intpk]
    name:        Mapped[str]           = mapped_column(String(100), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    machine_models: Mapped[List["MachineModel"]] = relationship(
        back_populates="category", passive_deletes=True)
    required_equipment_links: Mapped[List["RequiredEquipment"]] = relationship(
        back_populates="category", passive_deletes=True)

    def __repr__(self) -> str:
        return (
            f"EquipmentCategory(category_id={self.category_id!r}, "
            f"name={self.name!r}, "
            f"description={self.description!r})"
        )


class Station(Base):
    __tablename__ = "station"

    station_id:   Mapped[intpk]
    room_id:      Mapped[int]           = mapped_column(
        ForeignKey("room.room_id", ondelete="CASCADE"))
    name:         Mapped[str]           = mapped_column(String(100))
    description:  Mapped[Optional[str]] = mapped_column(Text)
    is_available: Mapped[bool]          = mapped_column(server_default=text("true"))

    room: Mapped["Room"] = relationship(back_populates="stations")
    machines: Mapped[List["Machine"]] = relationship(
        back_populates="station", passive_deletes=True)

    def __repr__(self) -> str:
        return (
            f"Station(station_id={self.station_id!r}, "
            f"room_id={self.room_id!r}, "
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f"is_available={self.is_available!r})"
        )


class MachineModel(Base):
    __tablename__ = "machine_model"

    model_id:     Mapped[intpk]
    category_id:  Mapped[int]           = mapped_column(
        ForeignKey("equipment_category.category_id", ondelete="RESTRICT"))
    manufacturer: Mapped[str]           = mapped_column(String(100))
    model:        Mapped[str]           = mapped_column(String(100))
    name:         Mapped[Optional[str]] = mapped_column(String(150))

    category: Mapped["EquipmentCategory"] = relationship(back_populates="machine_models")
    machines: Mapped[List["Machine"]] = relationship(
        back_populates="model", passive_deletes=True)

    def __repr__(self) -> str:
        return (
            f"MachineModel(model_id={self.model_id!r}, "
            f"category_id={self.category_id!r}, "
            f"manufacturer={self.manufacturer!r}, "
            f"model={self.model!r}, "
            f"name={self.name!r})"
        )


class Machine(Base):
    __tablename__ = "machine"
    __table_args__ = (
        CheckConstraint("tech_condition IN ('sprawna', 'uszkodzona', 'w_konserwacji')", name="chk_machine_condition"),
        CheckConstraint("maintenance_date >= purchase_date", name="chk_machine_time_range"),
    )

    machine_id:       Mapped[intpk]
    station_id:       Mapped[Optional[int]] = mapped_column(
        ForeignKey("station.station_id", ondelete="SET NULL"))
    model_id:         Mapped[int]           = mapped_column(
        ForeignKey("machine_model.model_id", ondelete="RESTRICT"))
    serial_number:    Mapped[str]           = mapped_column(String(50))
    purchase_date:    Mapped[date]
    tech_condition:   Mapped[str]           = mapped_column(String(20), server_default=text("'sprawna'"))
    maintenance_date: Mapped[Optional[date]]

    station: Mapped[Optional["Station"]] = relationship(back_populates="machines")
    model: Mapped["MachineModel"] = relationship(back_populates="machines")
    service_requests: Mapped[List["ServiceRequest"]] = relationship(
        back_populates="machine", passive_deletes=True)

    def __repr__(self) -> str:
        return (
            f"Machine(machine_id={self.machine_id!r}, "
            f"station_id={self.station_id!r}, "
            f"model_id={self.model_id!r}, "
            f"serial_number={self.serial_number!r}, "
            f"purchase_date={self.purchase_date!r}, "
            f"tech_condition={self.tech_condition!r}, "
            f"maintenance_date={self.maintenance_date!r})"
        )


class ServiceRequest(Base):
    __tablename__ = "service_request"
    __table_args__ = (
        CheckConstraint("request_type IN ('rutynowa_konserwacja', 'uszkodzona_czesc', 'brakujaca_czesc', 'zuzyta_czesc')", name="chk_request_type"),
        CheckConstraint("start_date >= reported_at", name="chk_request_start"),
        CheckConstraint("end_date > start_date", name="chk_request_end"),
        CheckConstraint("end_date IS NULL OR start_date IS NOT NULL", name="chk_request_valid_time"),
    )

    request_id:          Mapped[intpk]
    machine_id:          Mapped[int]               = mapped_column(
        ForeignKey("machine.machine_id", ondelete="CASCADE"))
    reporter_account_id: Mapped[Optional[int]]     = mapped_column(
        ForeignKey("user_account.account_id", ondelete="SET NULL"))
    technician_id:       Mapped[Optional[int]]     = mapped_column(
        ForeignKey("technician.technician_id", ondelete="SET NULL"))
    request_type:        Mapped[str]               = mapped_column(String(25))
    reported_at:         Mapped[datetime]          = mapped_column(server_default=func.current_timestamp())
    description:         Mapped[str]               = mapped_column(Text)
    start_date:          Mapped[Optional[datetime]]
    end_date:            Mapped[Optional[datetime]]

    machine: Mapped["Machine"] = relationship(back_populates="service_requests")
    reporter_account: Mapped[Optional["UserAccount"]] = relationship(foreign_keys=[reporter_account_id])
    technician: Mapped[Optional["Technician"]] = relationship(foreign_keys=[technician_id])

    def __repr__(self) -> str:
        return (
            f"ServiceRequest(request_id={self.request_id!r}, "
            f"machine_id={self.machine_id!r}, "
            f"reporter_account_id={self.reporter_account_id!r}, "
            f"technician_id={self.technician_id!r}, "
            f"request_type={self.request_type!r}, "
            f"reported_at={self.reported_at!r}, "
            f"start_date={self.start_date!r}, "
            f"end_date={self.end_date!r})"
        )


class Exercise(Base):
    __tablename__ = "exercise"
    __table_args__ = (
        CheckConstraint("difficulty_level IN ('poczatkujacy', 'sredniozaawansowany', 'zaawansowany')", name="chk_exercise_level"),
    )

    exercise_id:      Mapped[intpk]
    name:             Mapped[str]           = mapped_column(String(100), unique=True)
    description:      Mapped[Optional[str]] = mapped_column(Text)
    difficulty_level: Mapped[str]           = mapped_column(String(20))

    required_equipment_links: Mapped[List["RequiredEquipment"]] = relationship(
        back_populates="exercise", passive_deletes=True)
    plan_exercise_links: Mapped[List["PlanExercise"]] = relationship(
        back_populates="exercise", passive_deletes=True)

    def __repr__(self) -> str:
        return (
            f"Exercise(exercise_id={self.exercise_id!r}, "
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f"difficulty_level={self.difficulty_level!r})"
        )


class RequiredEquipment(Base):
    __tablename__ = "required_equipment"

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercise.exercise_id", ondelete="CASCADE"),
        primary_key=True, autoincrement=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("equipment_category.category_id", ondelete="CASCADE"),
        primary_key=True, autoincrement=False)

    exercise: Mapped["Exercise"] = relationship(back_populates="required_equipment_links")
    category: Mapped["EquipmentCategory"] = relationship(back_populates="required_equipment_links")

    def __repr__(self) -> str:
        return (
            f"RequiredEquipment(exercise_id={self.exercise_id!r}, "
            f"category_id={self.category_id!r})"
        )


class TrainingPlan(Base):
    __tablename__ = "training_plan"
    __table_args__ = (
        CheckConstraint("valid_to >= valid_from", name="chk_plan_time_range"),
    )

    plan_id:         Mapped[intpk]
    client_id:       Mapped[int]           = mapped_column(
        ForeignKey("client.client_id", ondelete="CASCADE"))
    trainer_id:      Mapped[int]           = mapped_column(
        ForeignKey("trainer.trainer_id", ondelete="CASCADE"))
    name:            Mapped[str]           = mapped_column(String(100))
    goal:            Mapped[Optional[str]] = mapped_column(String(255))
    valid_from:      Mapped[date]
    valid_to:        Mapped[date]
    recommendations: Mapped[Optional[str]] = mapped_column(Text)

    client: Mapped["Client"] = relationship(foreign_keys=[client_id])
    trainer: Mapped["Trainer"] = relationship(foreign_keys=[trainer_id])
    plan_exercise_links: Mapped[List["PlanExercise"]] = relationship(
        back_populates="plan", passive_deletes=True)

    def __repr__(self) -> str:
        return (
            f"TrainingPlan(plan_id={self.plan_id!r}, "
            f"client_id={self.client_id!r}, "
            f"trainer_id={self.trainer_id!r}, "
            f"name={self.name!r}, "
            f"goal={self.goal!r}, "
            f"valid_from={self.valid_from!r}, "
            f"valid_to={self.valid_to!r})"
        )


class PlanExercise(Base):
    __tablename__ = "plan_exercise"
    __table_args__ = (
        CheckConstraint("set_count > 0", name="chk_pe_sets"),
        CheckConstraint("rep_count >= 0", name="chk_pe_reps"),
    )

    plan_id:     Mapped[int] = mapped_column(
        ForeignKey("training_plan.plan_id", ondelete="CASCADE"),
        primary_key=True, autoincrement=False)
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercise.exercise_id", ondelete="CASCADE"),
        primary_key=True, autoincrement=False)
    set_count:   Mapped[int]
    rep_count:   Mapped[int]

    plan: Mapped["TrainingPlan"] = relationship(back_populates="plan_exercise_links")
    exercise: Mapped["Exercise"] = relationship(back_populates="plan_exercise_links")

    def __repr__(self) -> str:
        return (
            f"PlanExercise(plan_id={self.plan_id!r}, "
            f"exercise_id={self.exercise_id!r}, "
            f"set_count={self.set_count!r}, "
            f"rep_count={self.rep_count!r})"
        )