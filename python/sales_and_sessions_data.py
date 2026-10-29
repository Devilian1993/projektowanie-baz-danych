from bisect import bisect_left, bisect_right, insort
from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from itertools import count
from random import Random
from typing import NamedTuple, Optional

from models import (
    ClassEnrollment,
    ClassType,
    GroupClass,
    Membership,
    MembershipPayment,
    MembershipType,
    Payment,
    PersonalTraining,
    StationReservation,
    TrainerQualification,
    TrainingPayment,
)

__all__ = ["generate_sales_and_sessions_data", "SALES_SEQUENCE_RESET_SQL"]

_DEFAULT_REFERENCE_TIME = datetime(2026, 10, 28, 23, 0, 0)

_DATA_START = datetime(2024, 1, 1)
_MIN_DATA_AGE = timedelta(days=1)

_FUTURE_HORIZON = timedelta(days=14)

_FIRST_SLOT_MINUTE = 6 * 60
_LAST_SLOT_MINUTE = 20 * 60
_SLOT_STEP_MINUTES = 30

_MAX_PLACEMENT_ATTEMPTS = 500

_CENT = Decimal("0.01")

_RECEPTIONIST_SALE_PROBABILITY = 0.85
_START_DELAY_PROBABILITY = 0.2
_MAX_START_DELAY_DAYS = 7
_MAX_RENEWAL_ADVANCE_DAYS = 3
_MAX_FIRST_PURCHASE_DELAY = timedelta(days=7)
_MAX_RENEWAL_GAP = timedelta(days=30)

_PAYMENT_METHODS = ("gotowka", "blik", "karta")
_PAYMENT_METHOD_WEIGHTS = (25, 40, 35)
_ONLINE_PAYMENT_METHODS = ("blik", "karta")
_REJECTED_PAYMENT_PROBABILITY = 0.05
_PENDING_PAYMENT_PROBABILITY = 0.1
_PENDING_WINDOW = timedelta(days=1)
_MAX_PAYMENT_DELAY_SECONDS = 10 * 60
_RETRY_DELAY_SECONDS = (60, 10 * 60)
_MEMBERSHIP_PURPOSE = "karnet"
_TRAINING_PURPOSE = "trening_personalny"

_TRAINING_DURATIONS = (45, 60, 90)
_TRAINING_DURATION_WEIGHTS = (20, 65, 15)
_TRAINING_CANCELLED_PROBABILITY = 0.1
_TRAINING_NOTE_PROBABILITY = 0.25
_MAX_STATIONS_PER_TRAINING = 3
_BOOKING_LEAD = timedelta(days=14)
_PAYMENT_ADVANCE_PROBABILITY = 0.6

_MAX_QUALIFICATIONS_PER_TRAINER = 5
_CLASS_CANCELLED_PROBABILITY = 0.05
_MIN_CLASS_CAPACITY = 8
_MAX_CLASS_CAPACITY = 30
_ENROLLMENT_LEAD = timedelta(days=14)

_MEMBERSHIP_TYPES = [
    ("Wejście jednorazowe", 1, Decimal("25.00"), Decimal("20.00"),
     "Pojedyncze wejście na siłownię, ważne przez jeden dzień."),
    ("Karnet tygodniowy", 7, Decimal("69.00"), Decimal("55.00"),
     "Nieograniczony dostęp do siłowni przez 7 dni."),
    ("Karnet miesięczny", 30, Decimal("149.00"), Decimal("119.00"),
     "Nieograniczony dostęp do siłowni i zajęć grupowych przez 30 dni."),
    ("Karnet kwartalny", 90, Decimal("399.00"), Decimal("319.00"),
     "Nieograniczony dostęp do siłowni i zajęć grupowych przez 90 dni."),
    ("Karnet półroczny", 180, Decimal("719.00"), Decimal("579.00"),
     "Nieograniczony dostęp do siłowni i zajęć grupowych przez 180 dni."),
    ("Karnet roczny", 365, Decimal("1290.00"), Decimal("999.00"),
     "Nieograniczony dostęp do siłowni i zajęć grupowych przez 365 dni."),
]
_MEMBERSHIP_TYPE_WEIGHTS = (10, 6, 40, 20, 9, 15)

_CLASS_TYPES = [
    ("Joga", "Łagodne asany i praca z oddechem, poprawa elastyczności i redukcja stresu.", "poczatkujacy", 60),
    ("Pilates", "Ćwiczenia wzmacniające mięśnie głębokie i poprawiające postawę.", "poczatkujacy", 55),
    ("Stretching", "Rozciąganie całego ciała, zwiększenie zakresu ruchu w stawach.", "poczatkujacy", 45),
    ("Zdrowy Kręgosłup", "Ćwiczenia odciążające kręgosłup i wzmacniające mięśnie posturalne.", "poczatkujacy", 45),
    ("Aerobik", "Choreograficzny trening cardio w rytm muzyki.", "poczatkujacy", 50),
    ("Zumba", "Taneczny trening cardio oparty na rytmach latynoskich.", "poczatkujacy", 50),
    ("Spinning", "Interwałowa jazda na rowerach stacjonarnych w rytm muzyki.", "sredniozaawansowany", 45),
    ("Body Pump", "Trening siłowy ze sztangą angażujący całe ciało.", "sredniozaawansowany", 60),
    ("Trening Obwodowy", "Seria stacji angażujących różne partie mięśni.", "sredniozaawansowany", 50),
    ("TRX", "Ćwiczenia na taśmach zawieszonych, budowanie siły i stabilizacji.", "sredniozaawansowany", 45),
    ("Kettlebell", "Dynamiczny trening z użyciem odważników kulowych.", "sredniozaawansowany", 60),
    ("Boks Kondycyjny", "Trening bokserski nastawiony na kondycję i koordynację.", "sredniozaawansowany", 55),
    ("Crossfit", "Wysokointensywne zestawy ćwiczeń funkcjonalnych.", "zaawansowany", 60),
    ("HIIT", "Krótkie interwały maksymalnego wysiłku przeplatane odpoczynkiem.", "zaawansowany", 40),
]

_TRAINING_NOTES = [
    "Klient zgłasza ból kolana, ograniczyć obciążenie.",
    "Pierwszy trening, wstępna ocena sprawności.",
    "Nacisk na technikę martwego ciągu.",
    "Praca nad mobilnością bioder.",
    "Klient prosi o lżejszą sesję po kontuzji.",
    "Test siły maksymalnej w wyciskaniu.",
    "Trening interwałowy zamiast siłowego.",
    "Omówienie planu żywieniowego po treningu.",
]

_IDENTITY_COLUMNS = {
    "membership_type": "type_id",
    "membership": "membership_id",
    "payment": "payment_id",
    "personal_training": "training_id",
    "station_reservation": "reservation_id",
    "class_type": "class_type_id",
    "group_class": "class_id",
}

SALES_SEQUENCE_RESET_SQL = [
    f"SELECT setval(pg_get_serial_sequence('{table}', '{column}'), "
    f"COALESCE(MAX({column}), 1), MAX({column}) IS NOT NULL) FROM {table};"
    for table, column in _IDENTITY_COLUMNS.items()
]


class _TrainingDraft(NamedTuple):
    starts_at: datetime
    ends_at: datetime
    client_id: int
    trainer_id: int
    price: Decimal
    is_cancelled: bool
    notes: Optional[str]
    booked_at: datetime
    reservations: list


def _validate_arguments(clients, trainers, receptionists, rooms, stations,
                        n_memberships, n_personal_trainings, n_group_classes,
                        n_enrollments, reference_time):
    for name, value in (("n_memberships", n_memberships),
                        ("n_personal_trainings", n_personal_trainings),
                        ("n_group_classes", n_group_classes),
                        ("n_enrollments", n_enrollments)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")

    if reference_time.tzinfo is not None:
        raise ValueError(
            "reference_time must be a naive datetime "
            "(the models use timestamp without time zone)"
        )

    if reference_time < _DATA_START + _MIN_DATA_AGE:
        raise ValueError(f"reference_time must be after {_DATA_START + _MIN_DATA_AGE}")

    rooms_by_id = {room.room_id: room for room in rooms}
    if any(station.room_id not in rooms_by_id for station in stations):
        raise ValueError("Every station must belong to one of the given rooms")

    if any(client.registered_at > reference_time for client in clients):
        raise ValueError("Clients registered after reference_time are not allowed")

    if (n_memberships or n_personal_trainings or n_enrollments) and not clients:
        raise ValueError("Cannot generate memberships, trainings or enrollments without clients")

    if n_personal_trainings:
        if not any(trainer.training_rate is not None for trainer in trainers):
            raise ValueError("Personal trainings require a trainer with a training_rate")
        if not any(station.is_available and rooms_by_id[station.room_id].is_active
                   for station in stations):
            raise ValueError("Personal trainings require an available station in an active room")

    if n_group_classes:
        if not trainers:
            raise ValueError("Cannot generate group classes without trainers")
        if not any(room.is_active for room in rooms):
            raise ValueError("Cannot generate group classes without an active room")

    if n_enrollments and not n_group_classes:
        raise ValueError("Cannot generate enrollments without group classes")


class _Generator:
    def __init__(self, reference_time: datetime, clients, trainers,
                 receptionists, rooms, stations):
        self.now = reference_time.replace(microsecond=0)
        self.rng = Random()

        self.clients = clients
        self.trainers = trainers
        self.personal_trainers = [t for t in trainers if t.training_rate is not None]
        self.receptionists = sorted(receptionists, key=lambda r: r.hire_date)
        self.receptionist_hire_dates = [r.hire_date for r in self.receptionists]

        self.room_by_id = {room.room_id: room for room in rooms}
        self.active_rooms = [room for room in rooms if room.is_active]
        self.usable_stations = [
            station for station in stations
            if station.is_available and self.room_by_id[station.room_id].is_active
        ]

        self._ids = defaultdict(lambda: count(1))
        self.busy = defaultdict(list)
        self.qualified = defaultdict(list)
        self.payment_drafts = []

        self.tables = {
            "membership_type": [
                MembershipType(type_id=i, name=name, validity_period=period,
                               regular_price=regular, reduced_price=reduced,
                               description=description)
                for i, (name, period, regular, reduced, description)
                in enumerate(_MEMBERSHIP_TYPES, start=1)
            ],
            "membership": [],
            "payment": [],
            "membership_payment": [],
            "personal_training": [],
            "training_payment": [],
            "station_reservation": [],
            "class_type": [
                ClassType(class_type_id=i, name=name, description=description,
                          skill_level=skill_level, duration_minutes=duration)
                for i, (name, description, skill_level, duration)
                in enumerate(_CLASS_TYPES, start=1)
            ],
            "trainer_qualification": [],
            "group_class": [],
            "class_enrollment": [],
        }
        self.class_types = {ct.class_type_id: ct for ct in self.tables["class_type"]}

    def _next_id(self, table: str) -> int:
        return next(self._ids[table])

    def _bool(self, probability: float = 0.5) -> bool:
        return self.rng.random() < probability

    def _datetime_between(self, start: datetime, end: datetime) -> datetime:
        seconds = int((end - start).total_seconds())
        return start + timedelta(seconds=self.rng.randint(0, seconds))

    def _is_free(self, key, start: datetime, end: datetime) -> bool:
        slots = self.busy[key]
        index = bisect_left(slots, (start,))
        if index > 0 and slots[index - 1][1] > start:
            return False
        if index < len(slots) and slots[index][0] < end:
            return False
        return True

    def _book(self, key, start: datetime, end: datetime):
        insort(self.busy[key], (start, end))

    def _random_slot_start(self, window_start: datetime,
                           window_end: datetime) -> Optional[datetime]:
        if window_start > window_end:
            return None

        days = (window_end.date() - window_start.date()).days
        day = window_start.date() + timedelta(days=self.rng.randint(0, days))
        minute = self.rng.randrange(
            _FIRST_SLOT_MINUTE, _LAST_SLOT_MINUTE + 1, _SLOT_STEP_MINUTES)

        start = datetime.combine(day, time()) + timedelta(minutes=minute)
        return start if window_start <= start <= window_end else None

    @staticmethod
    def _fits_opening_hours(room, start: datetime, end: datetime) -> bool:
        return (start.date() == end.date()
                and room.opening_time <= start.time()
                and end.time() <= room.closing_time)

    def _make_trainer_qualifications(self):
        class_types = self.tables["class_type"]
        for trainer in self.trainers:
            k = self.rng.randint(1, min(_MAX_QUALIFICATIONS_PER_TRAINER, len(class_types)))
            chosen = sorted(self.rng.sample(class_types, k),
                            key=lambda ct: ct.class_type_id)
            for class_type in chosen:
                self.tables["trainer_qualification"].append(TrainerQualification(
                    trainer_id=trainer.trainer_id,
                    class_type_id=class_type.class_type_id,
                ))
                self.qualified[class_type.class_type_id].append(trainer)

    def _place_group_class(self, class_types: list) -> tuple:
        for _ in range(_MAX_PLACEMENT_ATTEMPTS):
            class_type = self.rng.choice(class_types)
            trainer = self.rng.choice(self.qualified[class_type.class_type_id])
            room = self.rng.choice(self.active_rooms)

            window_start = max(_DATA_START, datetime.combine(trainer.hire_date, time()))
            starts_at = self._random_slot_start(window_start, self.now + _FUTURE_HORIZON)
            if starts_at is None:
                continue

            ends_at = starts_at + timedelta(minutes=class_type.duration_minutes)
            trainer_key = ("trainer", trainer.trainer_id)
            room_key = ("room", room.room_id)
            if not (self._fits_opening_hours(room, starts_at, ends_at)
                    and self._is_free(trainer_key, starts_at, ends_at)
                    and self._is_free(room_key, starts_at, ends_at)):
                continue

            self._book(trainer_key, starts_at, ends_at)
            self._book(room_key, starts_at, ends_at)

            upper = min(room.max_occupancy, _MAX_CLASS_CAPACITY)
            lower = min(_MIN_CLASS_CAPACITY, upper)
            return (starts_at, trainer.trainer_id, class_type.class_type_id,
                    room.room_id, self.rng.randint(lower, upper),
                    self._bool(_CLASS_CANCELLED_PROBABILITY))

        raise ValueError("Could not schedule a group class without conflicts")

    def _make_group_classes(self, n: int):
        class_types = [ct for ct in self.tables["class_type"]
                       if self.qualified[ct.class_type_id]]

        drafts = [self._place_group_class(class_types) for _ in range(n)]
        drafts.sort(key=lambda draft: draft[:2])

        for starts_at, trainer_id, class_type_id, room_id, capacity, is_cancelled in drafts:
            self.tables["group_class"].append(GroupClass(
                class_id=self._next_id("group_class"),
                class_type_id=class_type_id,
                room_id=room_id,
                trainer_id=trainer_id,
                starts_at=starts_at,
                capacity=capacity,
                is_cancelled=is_cancelled,
            ))

    def _find_station(self, start: datetime, end: datetime, used_ids: set):
        candidates = self.rng.sample(self.usable_stations, len(self.usable_stations))
        for station in candidates:
            room = self.room_by_id[station.room_id]
            if (station.station_id not in used_ids
                    and self._fits_opening_hours(room, start, end)
                    and self._is_free(("station", station.station_id), start, end)
                    and self._is_free(("room", room.room_id), start, end)):
                return station
        return None

    def _pick_stations(self, starts_at: datetime, ends_at: datetime) -> Optional[list]:
        k = self.rng.randint(1, _MAX_STATIONS_PER_TRAINING)
        total = int((ends_at - starts_at).total_seconds())
        bounds = [starts_at + timedelta(seconds=total * i // k) for i in range(k + 1)]

        chosen = []
        for segment_start, segment_end in zip(bounds, bounds[1:]):
            station = self._find_station(
                segment_start, segment_end, {item[0] for item in chosen})
            if station is None:
                return None
            chosen.append((station.station_id, segment_start, segment_end))
        return chosen

    def _place_personal_training(self) -> _TrainingDraft:
        for _ in range(_MAX_PLACEMENT_ATTEMPTS):
            client = self.rng.choice(self.clients)
            trainer = self.rng.choice(self.personal_trainers)
            minutes = self.rng.choices(
                _TRAINING_DURATIONS, weights=_TRAINING_DURATION_WEIGHTS)[0]

            window_start = max(client.registered_at,
                               datetime.combine(trainer.hire_date, time()))
            starts_at = self._random_slot_start(window_start, self.now + _FUTURE_HORIZON)
            if starts_at is None:
                continue

            ends_at = starts_at + timedelta(minutes=minutes)
            trainer_key = ("trainer", trainer.trainer_id)
            client_key = ("client", client.client_id)
            if not (self._is_free(trainer_key, starts_at, ends_at)
                    and self._is_free(client_key, starts_at, ends_at)):
                continue

            reservations = self._pick_stations(starts_at, ends_at)
            if reservations is None:
                continue

            self._book(trainer_key, starts_at, ends_at)
            self._book(client_key, starts_at, ends_at)
            for station_id, segment_start, segment_end in reservations:
                self._book(("station", station_id), segment_start, segment_end)

            latest = min(starts_at, self.now)
            earliest = max(client.registered_at, latest - _BOOKING_LEAD)
            price = (trainer.training_rate * minutes / 60).quantize(
                _CENT, rounding=ROUND_HALF_UP)

            return _TrainingDraft(
                starts_at=starts_at,
                ends_at=ends_at,
                client_id=client.client_id,
                trainer_id=trainer.trainer_id,
                price=price,
                is_cancelled=self._bool(_TRAINING_CANCELLED_PROBABILITY),
                notes=(self.rng.choice(_TRAINING_NOTES)
                       if self._bool(_TRAINING_NOTE_PROBABILITY) else None),
                booked_at=self._datetime_between(earliest, latest),
                reservations=reservations,
            )

        raise ValueError("Could not schedule a personal training without conflicts")

    def _add_payment_attempts(self, first_attempt_at: datetime, amount: Decimal,
                              purpose: str, target_table: str, target_id: int):
        final_method = self.rng.choices(_PAYMENT_METHODS, weights=_PAYMENT_METHOD_WEIGHTS)[0]
        final_at = first_attempt_at

        if self._bool(_REJECTED_PAYMENT_PROBABILITY):
            self.payment_drafts.append((
                first_attempt_at, target_table, target_id, amount,
                self.rng.choice(_ONLINE_PAYMENT_METHODS), purpose, "odrzucona"))
            retry_delay = self.rng.randint(*_RETRY_DELAY_SECONDS)
            final_at = min(self.now, first_attempt_at + timedelta(seconds=retry_delay))

        is_recent = self.now - final_at <= _PENDING_WINDOW
        status = ("oczekujaca"
                  if is_recent and self._bool(_PENDING_PAYMENT_PROBABILITY)
                  else "oplacona")
        self.payment_drafts.append((
            final_at, target_table, target_id, amount, final_method, purpose, status))

    def _add_training_payments(self, training_id: int, draft: _TrainingDraft):
        if draft.is_cancelled:
            return

        is_upcoming = draft.starts_at > self.now
        if is_upcoming and not self._bool(_PAYMENT_ADVANCE_PROBABILITY):
            return

        latest = min(draft.starts_at, self.now)
        self._add_payment_attempts(
            self._datetime_between(draft.booked_at, latest),
            draft.price, _TRAINING_PURPOSE, "training", training_id)

    def _make_personal_trainings(self, n: int):
        drafts = [self._place_personal_training() for _ in range(n)]
        drafts.sort(key=lambda draft: (draft.starts_at, draft.trainer_id))

        reservations = []
        for draft in drafts:
            training = PersonalTraining(
                training_id=self._next_id("personal_training"),
                client_id=draft.client_id,
                trainer_id=draft.trainer_id,
                starts_at=draft.starts_at,
                ends_at=draft.ends_at,
                price=draft.price,
                is_cancelled=draft.is_cancelled,
                notes=draft.notes,
            )
            self.tables["personal_training"].append(training)
            self._add_training_payments(training.training_id, draft)

            for station_id, reserved_from, reserved_to in draft.reservations:
                reservations.append((draft.booked_at, reserved_from, station_id,
                                     reserved_to, training.training_id,
                                     not draft.is_cancelled))

        reservations.sort(key=lambda reservation: reservation[:3])
        for (created_at, reserved_from, station_id,
             reserved_to, training_id, is_active) in reservations:
            self.tables["station_reservation"].append(StationReservation(
                reservation_id=self._next_id("station_reservation"),
                station_id=station_id,
                training_id=training_id,
                reserved_from=reserved_from,
                reserved_to=reserved_to,
                created_at=created_at,
                is_active=is_active,
            ))

    def _make_enrollments(self, n: int):
        classes = [c for c in self.tables["group_class"] if not c.is_cancelled]
        seats_left = {c.class_id: c.capacity for c in classes}
        drafts = []
        failures = 0

        while len(drafts) < n:
            if not classes or failures >= _MAX_PLACEMENT_ATTEMPTS:
                raise ValueError("Could not place all enrollments (not enough seats or free clients)")

            position = self.rng.randrange(len(classes))
            group_class = classes[position]
            client = self.rng.choice(self.clients)

            starts_at = group_class.starts_at
            ends_at = starts_at + timedelta(
                minutes=self.class_types[group_class.class_type_id].duration_minutes)
            client_key = ("client", client.client_id)

            if (client.registered_at > starts_at
                    or not self._is_free(client_key, starts_at, ends_at)):
                failures += 1
                continue

            failures = 0
            self._book(client_key, starts_at, ends_at)

            latest = min(starts_at, self.now)
            earliest = max(client.registered_at, latest - _ENROLLMENT_LEAD)
            drafts.append((self._datetime_between(earliest, latest),
                           group_class.class_id, client.client_id))

            seats_left[group_class.class_id] -= 1
            if seats_left[group_class.class_id] == 0:
                classes[position] = classes[-1]
                classes.pop()

        drafts.sort()
        for enrolled_at, class_id, client_id in drafts:
            self.tables["class_enrollment"].append(ClassEnrollment(
                client_id=client_id,
                class_id=class_id,
                enrolled_at=enrolled_at,
            ))

    def _pick_receptionist(self, purchase_date: datetime) -> Optional[int]:
        if not self._bool(_RECEPTIONIST_SALE_PROBABILITY):
            return None

        eligible = bisect_right(self.receptionist_hire_dates, purchase_date.date())
        if eligible == 0:
            return None
        return self.receptionists[self.rng.randrange(eligible)].receptionist_id

    def _make_memberships(self, n: int):
        types = self.tables["membership_type"]
        open_clients = list(range(len(self.clients)))
        previous = {}
        drafts = []

        while len(drafts) < n:
            if not open_clients:
                raise ValueError("Clients cannot take more memberships before reference_time")

            position = self.rng.randrange(len(open_clients))
            index = open_clients[position]
            client = self.clients[index]

            if index in previous:
                last_purchase, last_end = previous[index]
                earliest = max(
                    last_purchase,
                    datetime.combine(last_end, time())
                    - timedelta(days=_MAX_RENEWAL_ADVANCE_DAYS))
                max_delay = _MAX_RENEWAL_GAP
            else:
                earliest = client.registered_at
                max_delay = _MAX_FIRST_PURCHASE_DELAY

            if earliest > self.now:
                open_clients[position] = open_clients[-1]
                open_clients.pop()
                continue

            span = min(int(max_delay.total_seconds()),
                       int((self.now - earliest).total_seconds()))
            purchase_date = earliest + timedelta(
                seconds=int(self.rng.triangular(0, span, 0)))

            membership_type = self.rng.choices(types, weights=_MEMBERSHIP_TYPE_WEIGHTS)[0]

            start_date = purchase_date.date()
            if index in previous:
                start_date = max(start_date, last_end)
            if self._bool(_START_DELAY_PROBABILITY):
                start_date += timedelta(days=self.rng.randint(1, _MAX_START_DELAY_DAYS))
            end_date = start_date + timedelta(days=membership_type.validity_period)
            previous[index] = (purchase_date, end_date)

            price = (membership_type.reduced_price if client.is_student
                     else membership_type.regular_price)
            drafts.append((purchase_date, client.client_id, membership_type.type_id,
                           self._pick_receptionist(purchase_date), start_date, price))

        drafts.sort(key=lambda draft: draft[:2])
        for (purchase_date, client_id, type_id,
             receptionist_id, start_date, price) in drafts:
            membership = Membership(
                membership_id=self._next_id("membership"),
                client_id=client_id,
                type_id=type_id,
                receptionist_id=receptionist_id,
                purchase_date=purchase_date,
                start_date=start_date,
                price=price,
            )
            self.tables["membership"].append(membership)

            first_attempt_at = min(
                self.now,
                purchase_date + timedelta(
                    seconds=self.rng.randint(0, _MAX_PAYMENT_DELAY_SECONDS)))
            self._add_payment_attempts(
                first_attempt_at, price, _MEMBERSHIP_PURPOSE,
                "membership", membership.membership_id)

    def _make_payments(self):
        self.payment_drafts.sort(key=lambda draft: draft[:3])
        for (payment_date, target_table, target_id,
             amount, method, purpose, status) in self.payment_drafts:
            payment_id = self._next_id("payment")
            self.tables["payment"].append(Payment(
                payment_id=payment_id,
                amount=amount,
                payment_date=payment_date,
                method=method,
                purpose=purpose,
                status=status,
            ))

            if target_table == "membership":
                self.tables["membership_payment"].append(MembershipPayment(
                    payment_id=payment_id, membership_id=target_id))
            else:
                self.tables["training_payment"].append(TrainingPayment(
                    payment_id=payment_id, training_id=target_id))

    def generate(self, n_memberships, n_personal_trainings, n_group_classes,
                 n_enrollments):
        self._make_trainer_qualifications()
        self._make_group_classes(n_group_classes)
        self._make_personal_trainings(n_personal_trainings)
        self._make_enrollments(n_enrollments)
        self._make_memberships(n_memberships)
        self._make_payments()

        return self.tables


def generate_sales_and_sessions_data(
        clients: list,
        trainers: list,
        receptionists: list,
        rooms: list,
        stations: list,
        n_memberships: int,
        n_personal_trainings: int,
        n_group_classes: int,
        n_enrollments: int,
        *,
        reference_time: datetime = _DEFAULT_REFERENCE_TIME):
    _validate_arguments(clients, trainers, receptionists, rooms, stations,
                        n_memberships, n_personal_trainings, n_group_classes,
                        n_enrollments, reference_time)

    return _Generator(reference_time, clients, trainers, receptionists,
                      rooms, stations).generate(
        n_memberships, n_personal_trainings, n_group_classes, n_enrollments)