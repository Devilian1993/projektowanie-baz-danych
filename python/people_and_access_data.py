import hashlib
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import count
from random import Random

from faker import Faker

from models import (
    Administrator,
    Client,
    Entry,
    FailedLogin,
    Receptionist,
    Specialization,
    Technician,
    Trainer,
    TrainerSpecialization,
    UserAccount,
)

__all__ = ["generate_people_and_access_data", "SEQUENCE_RESET_SQL"]

_DEFAULT_REFERENCE_TIME = datetime(2026, 10, 28, 23, 0, 0)

_ACCOUNTS_START = datetime(2024, 1, 1)
_MIN_ACCOUNT_AGE = timedelta(days=1)

_MIN_SUFFIX_POOL = 10_000

_ROLES = ("client", "trainer", "receptionist", "technician", "administrator")

_EMAIL_DOMAINS = ["interia.pl", "onet.pl", "o2.pl", "wp.pl", "gmail.com"]

_ACTIVE_ACCOUNT_PROBABILITY = 0.8
_STUDENT_PROBABILITY = 0.1
_PHONE_MISSING_PROBABILITY = 0.1

_ACTIVE_GRANT_PROBABILITY = 0.95
_STILL_INSIDE_PROBABILITY = 0.3
_RECENT_ENTRY_PROBABILITY = 0.03
_RECENT_WINDOW_SECONDS = 24 * 60 * 60
_MIN_VISIT_SECONDS = 60
_MAX_VISIT_SECONDS = 8 * 60 * 60
_ACTIVE_DENIAL_REASONS = [
    "Invalid access card",
    "Access denied",
    "Unauthorized access",
]
_INACTIVE_DENIAL_REASON = "Inactive account"

_MAX_DAYS_HIRED_BEFORE_ACCOUNT = 60

_POLISH_L = str.maketrans("ł", "l")

_SPECIALIZATIONS = [
    ("Trening Siłowy", "Skupienie na budowaniu siły maksymalnej z wykorzystaniem wolnych ciężarów."),
    ("Trening Funkcjonalny", "Poprawa sprawności w codziennym ruchu poprzez ćwiczenia wielostawowe."),
    ("Hipertrofia i Kulturystyka", "Programy nastawione na rozbudowę masy mięśniowej i estetykę sylwetki."),
    ("Redukcja Tkanki Tłuszczowej", "Treningi skoncentrowane na spalaniu kalorii i utracie zbędnych kilogramów."),
    ("Przygotowanie Motoryczne", "Rozwój dynamiki, szybkości i wydolności dla sportowców."),
    ("Mobilność i Stretching", "Zwiększanie zakresu ruchu w stawach, poprawa postury i niwelowanie napięć."),
    ("Trening Medyczny", "Bezpieczna aktywność fizyczna dostosowana do rehabilitacji po kontuzjach."),
    ("Kalistenika", "Trening oparty na ćwiczeniach siłowych z wykorzystaniem masy własnego ciała."),
    ("Trening Seniora", "Bezpieczne ćwiczenia poprawiające równowagę, siłę i samodzielność osób starszych."),
    ("Trening w Ciąży i Po Porodzie", "Bezpieczna aktywność wspierająca kobiety w tym wyjątkowym okresie życia."),
    ("Trójbój Siłowy (Powerlifting)", "Specjalizacja w przysiadzie, wyciskaniu leżąc i martwym ciągu."),
    ("Kettlebell", "Trening mocno angażujący całe ciało z użyciem odważników kulowych."),
    ("TRX i Trening w Zawieszeniu", "Budowanie siły i stabilizacji z wykorzystaniem taśm oporowych."),
    ("Crossfit i HIIT", "Wysokointensywne treningi interwałowe rozwijające kondycję i wszechstronność."),
    ("Joga i Pilates", "Wzmocnienie mięśni głębokich core, poprawa elastyczności i kontroli oddechu."),
    ("Kondycyjny Trening Bokserski", "Trening bokserski nastawiony na spalanie kalorii, kondycję i koordynację."),
    ("Prewencja Kontuzji", "Ćwiczenia wzmacniające obszary szczególnie narażone na urazy."),
    ("Trening dla Kobiet", "Programy skupione na ujędrnianiu, kształtowaniu pośladków i brzucha."),
    ("Kulturystyka Naturalna", "Rozwój sylwetki bez stosowania niedozwolonego wspomagania farmakologicznego."),
    ("Przygotowanie Wytrzymałościowe", "Treningi pod biegi, triathlon i dyscypliny długodystansowe."),
    ("Korekcja Wad Postawy", "Skuteczna walka z bólami kręgosłupa i asymetrią ciała."),
    ("Trening Siły Eksplozywnej", "Maksymalna moc i dynamika przydatna w sportach zespołowych."),
    ("Aktywność dla Młodzieży", "Bezpieczne wprowadzenie do treningu siłowego dla nastolatków."),
    ("Autorski Trening Odchudzający", "Kompleksowy program łączący nawyki żywieniowe i aktywność."),
]

_IDENTITY_COLUMNS = {
    "user_account": "account_id",
    "failed_login": "attempt_id",
    "client": "client_id",
    "trainer": "trainer_id",
    "receptionist": "receptionist_id",
    "technician": "technician_id",
    "administrator": "administrator_id",
    "entry": "entry_id",
    "specialization": "specialization_id",
}

SEQUENCE_RESET_SQL = [
    f"SELECT setval(pg_get_serial_sequence('{table}', '{column}'), "
    f"COALESCE(MAX({column}), 1), MAX({column}) IS NOT NULL) FROM {table};"
    for table, column in _IDENTITY_COLUMNS.items()
]


def _normalize_name(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name.lower().translate(_POLISH_L))
    return re.sub(r"[^a-z]", "", decomposed)


def _split_counts(total: int, fractions: dict[str, float]) -> dict[str, int]:
    exact = {key: total * fraction for key, fraction in fractions.items()}
    counts = {key: int(value) for key, value in exact.items()}
    leftover = total - sum(counts.values())

    by_remainder = sorted(exact, key=lambda key: exact[key] - counts[key], reverse=True)
    for key in by_remainder[:leftover]:
        counts[key] += 1

    return counts


def _validate_arguments(n_accounts, n_failed_logins, n_entries,
                        fractions, reference_time):
    for name, value in (("n_accounts", n_accounts),
                        ("n_failed_logins", n_failed_logins),
                        ("n_entries", n_entries)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")

    if n_accounts == 0 and (n_failed_logins > 0 or n_entries > 0):
        raise ValueError("Cannot generate failed logins or entries without accounts")

    if set(fractions) != set(_ROLES):
        raise ValueError(f"Fractions must contain exactly: {list(_ROLES)}")

    if not all(0 <= fraction <= 1 for fraction in fractions.values()):
        raise ValueError("Fractions must be between 0 and 1")

    if not abs(sum(fractions.values()) - 1.0) < 1e-9:
        raise ValueError("Fractions must sum to 1")

    if reference_time.tzinfo is not None:
        raise ValueError(
            "reference_time must be a naive datetime "
            "(the models use timestamp without time zone)"
        )

    if reference_time < _ACCOUNTS_START + _MIN_ACCOUNT_AGE:
        raise ValueError(f"reference_time must be after {_ACCOUNTS_START + _MIN_ACCOUNT_AGE}")


class _Generator:
    def __init__(self, reference_time: datetime, n_accounts: int):
        self.now = reference_time.replace(microsecond=0)
        self.rng = Random()
        self.fake = Faker("pl_PL")
        self.fake.seed_instance()

        pool_size = max(_MIN_SUFFIX_POOL, n_accounts)
        self.login_suffixes = self.rng.sample(range(pool_size), n_accounts)
        self.email_suffixes = self.rng.sample(range(pool_size), n_accounts)
        self.access_card_numbers = self.rng.sample(range(pool_size), n_accounts)

        self._ids = defaultdict(lambda: count(1))
        self.person_data = {}
        self.role_accounts = {role: [] for role in _ROLES}

        self.tables = {
            "user_account": [],
            "failed_login": [],
            "client": [],
            "trainer": [],
            "receptionist": [],
            "technician": [],
            "administrator": [],
            "entry": [],
            "specialization": [
                Specialization(specialization_id=i, name=name, description=description)
                for i, (name, description) in enumerate(_SPECIALIZATIONS, start=1)
            ],
            "trainer_specialization": [],
        }

    def _next_id(self, table: str) -> int:
        return next(self._ids[table])

    def _bool(self, probability: float = 0.5) -> bool:
        return self.rng.random() < probability

    def _datetime_between(self, start: datetime, end: datetime) -> datetime:
        seconds = int((end - start).total_seconds())
        return start + timedelta(seconds=self.rng.randint(0, seconds))

    def _phone(self):
        if self._bool(_PHONE_MISSING_PROBABILITY):
            return None
        return self.rng.choice("5678") + "".join(self.rng.choices("0123456789", k=8))

    def _person(self, account: UserAccount) -> dict:
        return self.person_data[account.account_id]

    def _password_hash(self) -> str:
        password = self.rng.randbytes(12).hex()
        salt = self.rng.randbytes(16).hex()
        digest = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return f"sha256${salt}${digest}"

    def _make_user_account(self) -> UserAccount:
        is_male = self._bool()
        person = {
            "first_name": (self.fake.first_name_male() if is_male
                           else self.fake.first_name_female()),
            "last_name": (self.fake.last_name_male() if is_male
                          else self.fake.last_name_female()),
            "phone": self._phone(),
        }

        account_id = self._next_id("user_account")
        self.person_data[account_id] = person

        created_at = self._datetime_between(_ACCOUNTS_START, self.now - _MIN_ACCOUNT_AGE)
        first = _normalize_name(person["first_name"])
        last = _normalize_name(person["last_name"])

        return UserAccount(
            account_id=account_id,
            login=f"{first[:3]}{last[:3]}{self.login_suffixes.pop():04d}",
            email=(f"{first}.{last}{self.email_suffixes.pop():04d}"
                   f"@{self.rng.choice(_EMAIL_DOMAINS)}"),
            password_hash=self._password_hash(),
            access_card_number=self.access_card_numbers.pop(),
            is_active=self._bool(_ACTIVE_ACCOUNT_PROBABILITY),
            created_at=created_at,
            last_login_at=self._datetime_between(created_at, self.now),
        )

    def _assign_roles(self, fractions: dict[str, float]):
        accounts = self.tables["user_account"]
        order = list(range(len(accounts)))
        self.rng.shuffle(order)

        counts = _split_counts(len(accounts), {role: fractions[role] for role in _ROLES})

        start = 0
        for role in _ROLES:
            picked = sorted(order[start:start + counts[role]])
            self.role_accounts[role] = [accounts[i] for i in picked]
            start += counts[role]

    def _hire_date(self, account: UserAccount):
        days = self.rng.randint(0, _MAX_DAYS_HIRED_BEFORE_ACCOUNT)
        return (account.created_at - timedelta(days=days)).date()

    def _make_client(self, account: UserAccount) -> Client:
        return Client(
            client_id=self._next_id("client"),
            account_id=account.account_id,
            **self._person(account),
            registered_at=account.created_at,
            is_student=self._bool(_STUDENT_PROBABILITY),
        )

    def _make_staff(self, model, account: UserAccount, **extra):
        table = model.__tablename__
        return model(
            **{f"{table}_id": self._next_id(table)},
            account_id=account.account_id,
            **self._person(account),
            hire_date=self._hire_date(account),
            **extra,
        )

    def _make_administrator(self, account: UserAccount) -> Administrator:
        return Administrator(
            administrator_id=self._next_id("administrator"),
            account_id=account.account_id,
            **self._person(account),
        )

    def _training_rate(self) -> Decimal:
        cents = self.rng.randint(5_000, 30_000)
        return Decimal(cents).scaleb(-2)

    def _make_role_rows(self):
        makers = {
            "client": self._make_client,
            "trainer": lambda a: self._make_staff(
                Trainer, a, training_rate=self._training_rate()),
            "receptionist": lambda a: self._make_staff(Receptionist, a),
            "technician": lambda a: self._make_staff(Technician, a),
            "administrator": self._make_administrator,
        }
        for role, make in makers.items():
            for account in self.role_accounts[role]:
                self.tables[role].append(make(account))

    def _make_failed_logins(self, n: int):
        accounts = self.tables["user_account"]
        attempts = []
        for _ in range(n):
            account = self.rng.choice(accounts)
            attempts.append(
                (self._datetime_between(account.created_at, self.now), account.account_id)
            )

        attempts.sort()
        for attempted_at, account_id in attempts:
            self.tables["failed_login"].append(FailedLogin(
                attempt_id=self._next_id("failed_login"),
                account_id=account_id,
                attempted_at=attempted_at,
            ))

    def _entries_for_account(self, account: UserAccount, k: int,
                             k_recent: int) -> list[tuple]:
        window = int((self.now - account.created_at).total_seconds())
        recent_span = min(_RECENT_WINDOW_SECONDS, window)
        old_span = window - recent_span

        k_old = min(k - k_recent, old_span)
        k_recent = k - k_old
        if k_recent > recent_span:
            raise ValueError(
                f"Account {account.account_id} cannot fit {k} entries "
                f"into {window} seconds"
            )

        offsets = sorted(
            self.rng.sample(range(old_span), k_old)
            + self.rng.sample(range(old_span, window), k_recent)
        )
        starts = [account.created_at + timedelta(seconds=o) for o in offsets]

        drafts = []
        for i, entered_at in enumerate(starts):
            is_last = i == k - 1
            boundary = self.now if is_last else starts[i + 1]
            seconds_free = int((boundary - entered_at).total_seconds())

            exited_at = None
            denial_reason = None
            granted = account.is_active and self._bool(_ACTIVE_GRANT_PROBABILITY)

            if not granted:
                denial_reason = (self.rng.choice(_ACTIVE_DENIAL_REASONS)
                                 if account.is_active else _INACTIVE_DENIAL_REASON)
            else:
                still_inside = (
                    is_last
                    and seconds_free <= _MAX_VISIT_SECONDS
                    and self._bool(_STILL_INSIDE_PROBABILITY)
                )
                if not still_inside:
                    longest = min(_MAX_VISIT_SECONDS, seconds_free)
                    shortest = min(_MIN_VISIT_SECONDS, longest)
                    exited_at = entered_at + timedelta(
                        seconds=self.rng.randint(shortest, longest))

            drafts.append((entered_at, account.account_id, exited_at, granted, denial_reason))

        return drafts

    def _make_entries(self, n_entries: int):
        accounts = self.tables["user_account"]
        totals, recents = Counter(), Counter()
        for _ in range(n_entries):
            index = self.rng.randrange(len(accounts))
            totals[index] += 1
            if self._bool(_RECENT_ENTRY_PROBABILITY):
                recents[index] += 1

        drafts = []
        for index in sorted(totals):
            drafts.extend(self._entries_for_account(
                accounts[index], totals[index], recents[index]))

        drafts.sort(key=lambda draft: draft[:2])
        for entered_at, account_id, exited_at, granted, denial_reason in drafts:
            self.tables["entry"].append(Entry(
                entry_id=self._next_id("entry"),
                account_id=account_id,
                entered_at=entered_at,
                exited_at=exited_at,
                result=granted,
                denial_reason=denial_reason,
            ))

    def _make_trainer_specializations(self):
        specializations = self.tables["specialization"]
        for trainer in self.tables["trainer"]:
            k = self.rng.randint(1, min(4, len(specializations)))
            chosen = sorted(self.rng.sample(specializations, k),
                            key=lambda s: s.specialization_id)
            for specialization in chosen:
                self.tables["trainer_specialization"].append(TrainerSpecialization(
                    trainer_id=trainer.trainer_id,
                    specialization_id=specialization.specialization_id,
                ))

    def generate(self, n_accounts, n_failed_logins, n_entries, fractions):
        for _ in range(n_accounts):
            self.tables["user_account"].append(self._make_user_account())

        self._assign_roles(fractions)
        self._make_role_rows()
        self._make_failed_logins(n_failed_logins)
        self._make_entries(n_entries)
        self._make_trainer_specializations()

        return self.tables


def generate_people_and_access_data(
        n_accounts: int,
        n_failed_logins: int,
        n_entries: int,
        user_account_fractions: dict[str, float],
        *,
        reference_time: datetime = _DEFAULT_REFERENCE_TIME):
    _validate_arguments(n_accounts, n_failed_logins, n_entries,
                        user_account_fractions, reference_time)

    return _Generator(reference_time, n_accounts).generate(
        n_accounts, n_failed_logins, n_entries, user_account_fractions)
