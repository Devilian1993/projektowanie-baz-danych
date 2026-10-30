from datetime import date, datetime, time, timedelta
from itertools import count
from random import Random
from decimal import Decimal

from faker import Faker

from models import (
    EquipmentCategory,
    Exercise,
    Machine,
    MachineModel,
    PlanExercise,
    RequiredEquipment,
    Room,
    ServiceRequest,
    Station,
    TrainingPlan,

    #from part 1
    Client,
    Technician,
    Trainer,
    UserAccount,
)

__all__ = ["generate_facility_and_training_data", "FACILITY_SEQUENCE_RESET_SQL"]

_DEFAULT_REFERENCE_TIME = datetime(2026, 10, 28, 23, 0, 0)
_GYM_OPENING_DATE = date(2024, 1, 1)


_ROOMS = [
    #number, name, area, max_occupancy, opening_time, closing_time
    (101, "Strefa Wolnych Ciężarków", 150.0, 40, time(6, 0), time(23, 0)),
    (102, "Strefa Maszyn Siłowych", 200.0, 50, time(6, 0), time(23, 0)),
    (103, "Strefa Cardio", 180.0, 45, time(6, 0), time(23, 0)),
    (104, "Sala Fitness", 100.0, 30, time(8, 0), time(22, 0)),
    (105, "Sala Crossfit", 120.0, 25, time(6, 0), time(22, 0)),
    (106, "Strefa Funkcjonalna", 90.0, 20, time(6, 0), time(23, 0)),
]

_EQUIPMENT_CATEGORIES = [
    ("Bieżnie", "Urządzenia do biegania w miejscu."),
    ("Orbitreki i Steppery", "Sprzęt eliptyczny oraz schody treningowe angażujące całe ciało."),
    ("Rowerki Stacjonarne", "Rowerki pionowe i poziome do treningu wytrzymałościowego."),
    ("Maszyny Siłowe (Stos)", "Urządzenia ze stałym stosem obciążeń do bezpiecznego treningu izolowanego."),
    ("Maszyny Półwolne", "Maszyny obciążane niezależnymi talerzami olimpijskimi."),
    ("Wolne Ciężary", "Hantle, talerze oraz gryfy proste i łamane."),
    ("Ławki i Stojaki", "Regulowane ławki treningowe oraz stojaki pod sztangi."),
    ("Bramy i Wyciągi", "Wielofunkcyjne wyciągi linowe i bramy crossfitowe."),
    ("Akcesoria", "Gumy, Maty, Piłki - drobny sprzęt wspomagający rozgrzewkę i rozciąganie."),
    ("Kettlebells", "Odważniki kulowe do treningu funkcjonalnego i siłowego."),
]

_EXERCISES = [
    ("Wyciskanie sztangi leżąc", "Klasyczne ćwiczenie na klatkę piersiową.", "sredniozaawansowany", ["Wolne Ciężary", "Ławki i Stojaki"]),
    ("Przysiad ze sztangą", "Podstawowe ćwiczenie budujące siłę nóg.", "sredniozaawansowany", ["Wolne Ciężary", "Ławki i Stojaki"]),
    ("Martwy ciąg", "Angażuje niemal całe ciało, głównie plecy i pośladki.", "zaawansowany", ["Wolne Ciężary"]),
    ("Wyciskanie hantli na ławce skośnej", "Rozwija górną część klatki piersiowej.", "poczatkujacy", ["Wolne Ciężary", "Ławki i Stojaki"]),
    ("Bieg interwałowy", "Trening cardio na bieżni.", "poczatkujacy", ["Bieżnie"]),
    ("Wiosłowanie sztangą w opadzie", "Buduje grubość mięśni grzbietu.", "sredniozaawansowany", ["Wolne Ciężary"]),
    ("Wyciskanie żołnierskie", "Rozwija przednie i boczne aktony barków.", "sredniozaawansowany", ["Wolne Ciężary", "Ławki i Stojaki"]),
    ("Podciąganie na drążku", "Ćwiczenie z masą własnego ciała na szerokość pleców.", "zaawansowany", ["Bramy i Wyciągi"]),
    ("Uginanie ramion z hantlami", "Izolowane ćwiczenie na bicepsy.", "poczatkujacy", ["Wolne Ciężary"]),
    ("Prostowanie ramion na wyciągu", "Izolowane ćwiczenie na tricepsy.", "poczatkujacy", ["Bramy i Wyciągi"]),
    ("Wyciskanie hantli na ławce płaskiej", "Rozwija mięśnie klatki piersiowej, tricepsy i przednie aktony barków.", "poczatkujacy", ["Wolne Ciężary", "Ławki i Stojaki"]),
    ("Rozpiętki z hantlami", "Ćwiczenie izolowane poprawiające rozwój mięśni klatki piersiowej.", "poczatkujacy", ["Wolne Ciężary", "Ławki i Stojaki"]),
    ("Rozpiętki na bramie", "Utrzymuje stałe napięcie mięśni klatki piersiowej podczas ruchu.", "sredniozaawansowany", ["Bramy i Wyciągi"]),
    ("Pompki klasyczne", "Angażują klatkę piersiową, barki i tricepsy.", "poczatkujacy", ["Akcesoria"]),
    ("Pompki diamentowe", "Wariant pompek mocniej angażujący tricepsy.", "sredniozaawansowany", ["Akcesoria"]),
    ("Pompki na poręczach", "Budują siłę tricepsów, klatki piersiowej i obręczy barkowej.", "sredniozaawansowany", ["Bramy i Wyciągi"]),
    ("Wyciskanie na maszynie siedząc", "Ćwiczenie na klatkę piersiową z kontrolowanym torem ruchu.", "poczatkujacy", ["Maszyny Siłowe (Stos)"]),
    ("Przenoszenie hantli za głowę", "Angażuje mięśnie klatki piersiowej i zębate przednie.", "sredniozaawansowany", ["Wolne Ciężary", "Ławki i Stojaki"]),
    ("Ściąganie drążka wyciągu górnego do klatki", "Rozwija mięśnie najszersze grzbietu i siłę pleców.", "poczatkujacy", ["Bramy i Wyciągi"]),
    ("Przyciąganie linki wyciągu dolnego", "Wzmacnia środkową część pleców i mięśnie stabilizujące łopatki.", "poczatkujacy", ["Bramy i Wyciągi"]),
    ("Wiosłowanie hantlą jednorącz", "Rozwija mięśnie grzbietu i pomaga wyrównywać różnice siłowe.", "sredniozaawansowany", ["Wolne Ciężary", "Ławki i Stojaki"]),
    ("Face pull", "Wzmacnia tylną część barków i mięśnie stabilizujące łopatki.", "poczatkujacy", ["Bramy i Wyciągi"]),
    ("Unoszenie hantli bokiem", "Izoluje boczne aktony mięśni naramiennych.", "poczatkujacy", ["Wolne Ciężary"]),
    ("Odwrotne rozpiętki", "Wzmacniają tylną część barków i górną część pleców.", "poczatkujacy", ["Wolne Ciężary"]),
    ("Szrugsy z hantlami", "Rozwijają mięśnie czworoboczne odpowiedzialne za unoszenie barków.", "poczatkujacy", ["Wolne Ciężary"]),
    ("Uginanie ramion ze sztangą", "Buduje siłę i masę mięśni dwugłowych ramion.", "poczatkujacy", ["Wolne Ciężary"]),
    ("Uginanie ramion chwytem młotkowym", "Angażuje bicepsy, mięsień ramienny i przedramiona.", "poczatkujacy", ["Wolne Ciężary"]),
    ("Uginanie ramion na modlitewniku", "Izoluje bicepsy i ułatwia kontrolowanie ruchu.", "sredniozaawansowany", ["Wolne Ciężary", "Ławki i Stojaki"]),
    ("Francuskie wyciskanie sztangi", "Rozwija mięśnie trójgłowe ramion.", "sredniozaawansowany", ["Wolne Ciężary", "Ławki i Stojaki"]),
    ("Prostowanie ramion nad głową z hantlą", "Akcentuje długą głowę tricepsa podczas prostowania łokci.", "poczatkujacy", ["Wolne Ciężary"]),
    ("Przysiad goblet", "Wzmacnia uda i pośladki oraz pomaga opanować technikę przysiadu.", "poczatkujacy", ["Kettlebells"]),
    ("Przysiad przedni ze sztangą", "Rozwija mięśnie czworogłowe ud i stabilizację tułowia.", "zaawansowany", ["Wolne Ciężary", "Ławki i Stojaki"]),
    ("Przysiad na suwnicy Hacka", "Angażuje przede wszystkim mięśnie czworogłowe ud i pośladki.", "sredniozaawansowany", ["Maszyny Półwolne"]),
    ("Wypychanie ciężaru na suwnicy", "Wzmacnia mięśnie ud i pośladków.", "poczatkujacy", ["Maszyny Półwolne"]),
    ("Wykroki z hantlami", "Rozwijają siłę nóg, pośladków i równowagę.", "sredniozaawansowany", ["Wolne Ciężary"]),
    ("Zakroki z hantlami", "Wzmacniają mięśnie nóg i pośladków oraz stabilność.", "sredniozaawansowany", ["Wolne Ciężary"]),
    ("Przysiad bułgarski", "Poprawia siłę nóg, pośladków i równowagę.", "zaawansowany", ["Wolne Ciężary", "Ławki i Stojaki"]),
    ("Hip thrust ze sztangą", "Wzmacnia mięśnie pośladkowe i rozwija siłę bioder.", "sredniozaawansowany", ["Wolne Ciężary", "Ławki i Stojaki"]),
    ("Most biodrowy", "Wzmacnia pośladki i mięśnie stabilizujące miednicę.", "poczatkujacy", ["Akcesoria"]),
    ("Martwy ciąg rumuński", "Rozwija mięśnie dwugłowe ud, pośladki i tylną taśmę mięśniową.", "sredniozaawansowany", ["Wolne Ciężary"]),
    ("Uginanie nóg na maszynie leżąc", "Izoluje mięśnie kulszowo-goleniowe z tyłu ud.", "poczatkujacy", ["Maszyny Siłowe (Stos)"]),
    ("Prostowanie nóg na maszynie", "Izoluje mięśnie czworogłowe ud.", "poczatkujacy", ["Maszyny Siłowe (Stos)"]),
    ("Wspięcia na palce stojąc", "Wzmacniają mięśnie łydek.", "poczatkujacy", ["Maszyny Siłowe (Stos)", "Wolne Ciężary"]),
    ("Wspięcia na palce siedząc", "Koncentrują pracę na mięśniu płaszczkowatym łydki.", "poczatkujacy", ["Maszyny Siłowe (Stos)"]),
    ("Odwodzenie nóg na maszynie", "Wzmacnia mięśnie pośladkowe odpowiedzialne za odwodzenie biodra.", "poczatkujacy", ["Maszyny Siłowe (Stos)"]),
    ("Przywodzenie nóg na maszynie", "Angażuje mięśnie przywodziciele po wewnętrznej stronie ud.", "poczatkujacy", ["Maszyny Siłowe (Stos)"]),
    ("Swing z kettlebell", "Rozwija siłę bioder, pośladków i kondycję.", "sredniozaawansowany", ["Kettlebells"]),
    ("Wchodzenie na podest", "Wzmacnia mięśnie nóg i pośladków oraz poprawia kondycję.", "poczatkujacy", ["Orbitreki i Steppery"]),
    ("Plank", "Wzmacnia mięśnie brzucha i stabilizuje tułów.", "poczatkujacy", ["Akcesoria"]),
    ("Deska boczna", "Wzmacnia mięśnie skośne brzucha i boczne stabilizatory tułowia.", "sredniozaawansowany", ["Akcesoria"]),
    ("Dead bug", "Poprawia kontrolę tułowia i stabilizację odcinka lędźwiowego.", "poczatkujacy", ["Akcesoria"]),
    ("Russian twist", "Angażuje mięśnie skośne brzucha podczas rotacji tułowia.", "sredniozaawansowany", ["Akcesoria"]),
    ("Unoszenie kolan w zwisie", "Wzmacnia mięśnie brzucha i stabilizację ciała.", "sredniozaawansowany", ["Bramy i Wyciągi"]),
    ("Spięcia brzucha na ławce skośnej", "Rozwijają mięśnie proste brzucha.", "poczatkujacy", ["Ławki i Stojaki"]),
    ("Mountain climbers", "Łączą pracę mięśni brzucha z treningiem kondycyjnym.", "sredniozaawansowany", ["Akcesoria"]),
    ("Burpees", "Poprawiają wydolność i wytrzymałość mięśniową całego ciała.", "zaawansowany", ["Akcesoria"]),
    ("Skakanie na skakance", "Poprawia koordynację, pracę nóg i wydolność.", "poczatkujacy", ["Akcesoria"]),
    ("Jazda na rowerze stacjonarnym", "Poprawia wydolność sercowo-naczyniową i wytrzymałość nóg.", "poczatkujacy", ["Rowerki Stacjonarne"]),
    ("Trening na orbitreku", "Poprawia wydolność i angażuje nogi oraz ramiona.", "poczatkujacy", ["Orbitreki i Steppery"]),
    ("Spacer farmera", "Rozwija siłę chwytu, stabilizację tułowia i wytrzymałość.", "sredniozaawansowany", ["Wolne Ciężary"]),
]

#kolumny z id
_FACILITY_IDENTITY_COLUMNS = {
    "room": "room_id",
    "station": "station_id",
    "equipment_category": "category_id",
    "machine_model": "model_id",
    "machine": "machine_id",
    "service_request": "request_id",
    "exercise": "exercise_id",
    "training_plan": "plan_id",
}

FACILITY_SEQUENCE_RESET_SQL = [
    f"SELECT setval(pg_get_serial_sequence('{table}', '{column}'), "
    f"COALESCE(MAX({column}), 1), MAX({column}) IS NOT NULL) FROM {table};"
    for table, column in _FACILITY_IDENTITY_COLUMNS.items()
]

#generator
class _FacilityGenerator:
    def __init__(self, reference_time: datetime,
                 accounts: list[UserAccount], clients: list[Client], 
                 trainers: list[Trainer], technicians: list[Technician],
                 training_plan_fraction: float,
                 n_historical_service_requests: int,
                 warehouse_machines_count: int):
        self.now = reference_time.replace(microsecond=0)
        self.rng = Random()
        self.fake = Faker("pl_PL")
        self.fake.seed_instance()

        self.training_plan_fraction = training_plan_fraction
        self.n_historical_service_requests = n_historical_service_requests
        self.warehouse_machines_count = warehouse_machines_count

        self.accounts = accounts
        self.clients = clients
        self.trainers = trainers
        self.technicians = technicians

        self._ids = {
            "room": count(1),
            "station": count(1),
            "equipment_category": count(1),
            "machine_model": count(1),
            "machine": count(1),
            "service_request": count(1),
            "exercise": count(1),
            "training_plan": count(1),
        }


        self.tables = {
            "room": [],
            "station": [],
            "equipment_category": [],
            "machine_model": [],
            "machine": [],
            "service_request": [],
            "exercise": [],
            "required_equipment": [],
            "training_plan": [],
            "plan_exercise": [],
        }

    def _next_id(self, table: str) -> int:
        return next(self._ids[table])

    def _bool(self, probability: float = 0.5) -> bool:
        return self.rng.random() < probability
        
    def _date_between(self, start: date, end: date) -> date:
        days = (end - start).days
        return start + timedelta(days=self.rng.randint(0, days))

    def _make_rooms(self):
        for number, name, area, max_occ, op_time, cl_time in _ROOMS:
            self.tables["room"].append(
                Room(
                    room_id=self._next_id("room"),
                    number=number,
                    name=name,
                    area=Decimal(str(area)),
                    max_occupancy=max_occ,
                    opening_time=op_time,
                    closing_time=cl_time,
                    is_active=True
                )
            )

    def _make_equipment_categories(self):
        for name, description in _EQUIPMENT_CATEGORIES:
            self.tables["equipment_category"].append(
                EquipmentCategory(
                    category_id=self._next_id("equipment_category"),
                    name=name,
                    description=description
                )
            )

    def _make_stations(self):
        rooms = self.tables["room"]
        
        for room in rooms:
            num_stations = self.rng.randint(5, max(5, room.max_occupancy - 2))
            
            for i in range(1, num_stations + 1):
                self.tables["station"].append(
                    Station(
                        station_id=self._next_id("station"),
                        room_id=room.room_id,
                        name=f"Stanowisko {i} ({room.name})",
                        description=f"Stanowisko treningowe nr {i} w sali {room.name}",
                        is_available=True
                    )
                )
    
    def _datetime_between(self, start: datetime, end: datetime) -> datetime:
        seconds = int((end - start).total_seconds())
        return start + timedelta(seconds=self.rng.randint(0, seconds))

    def _make_machine_models(self):
        manufacturers = ["TechnoGym", "LifeFitness", "Matrix", "Precor", "Hammer Strength", "Rogue"]
        created_pairs = set()
        
        for category in self.tables["equipment_category"]:
            num_models = self.rng.randint(2, 8)
            for _ in range(num_models):
                while True:
                    manufacturer = self.rng.choice(manufacturers)
                    model_code = f"{self.rng.choice(['Pro', 'Elite', 'Max', 'Ultra', 'Series'])} {self.rng.randint(1, 9)}00"
                    
                    if (manufacturer, model_code) not in created_pairs:
                        created_pairs.add((manufacturer, model_code))
                        break
                
                self.tables["machine_model"].append(
                    MachineModel(
                        model_id=self._next_id("machine_model"),
                        category_id=category.category_id,
                        manufacturer=manufacturer,
                        model=model_code,
                        name=f"{category.name} {manufacturer} {model_code}"
                    )
                )

    def _make_machines(self):
        models = self.tables["machine_model"]
        stations = self.tables["station"]

        assigned_stations = self.rng.sample(stations, int(len(stations) * 0.9))

        for station in assigned_stations:
            num_machines_at_station = self.rng.randint(1, 3)

            for _ in range(num_machines_at_station):
                model = self.rng.choice(models)
                purchase_date = self._date_between(_GYM_OPENING_DATE, self.now.date())
                maintenance_date = self._date_between(purchase_date, self.now.date() + timedelta(days=365))

                condition = self.rng.choices(
                    ['sprawna', 'uszkodzona', 'w_konserwacji'],
                    weights=[0.9, 0.05, 0.05],
                    k=1
                )[0]

                self.tables["machine"].append(
                    Machine(
                        machine_id=self._next_id("machine"),
                        station_id=station.station_id,
                        model_id=model.model_id,
                        serial_number=self.fake.bothify(text='SN-????-#####', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
                        purchase_date=purchase_date,
                        tech_condition=condition,
                        maintenance_date=maintenance_date
                    )
                )

        #machines in warehouse
        for _ in range(self.warehouse_machines_count):
            model = self.rng.choice(models)
            purchase_date = self._date_between(_GYM_OPENING_DATE, self.now.date())
            self.tables["machine"].append(
                Machine(
                    machine_id=self._next_id("machine"),
                    station_id=None,
                    model_id=model.model_id,
                    serial_number=self.fake.bothify(text='SN-????-#####', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
                    purchase_date=purchase_date,
                    tech_condition="sprawna",
                    maintenance_date=purchase_date + timedelta(days=180)
                )
            )

    def _make_service_requests(self):
        type_descriptions = {
            'rutynowa_konserwacja': 'Planowany przegląd okresowy i konserwacja',
            'uszkodzona_czesc': 'Zgłoszono uszkodzenie podzespołu',
            'brakujaca_czesc': 'Wykryto brak elementu wyposażenia stanowiska',
            'zuzyta_czesc': 'Odnotowano naturalne zużycie części eksploatacyjnych'
        }

        models_dict = {m.model_id: m for m in self.tables["machine_model"]}

        for _ in range(self.n_historical_service_requests):
            machine = self.rng.choice(self.tables["machine"])
            model = models_dict.get(machine.model_id)
            model_name = model.name if model else "Sprzęt ogólny"
            
            reporter = self.rng.choice(self.accounts) if self._bool(0.7) else None
            technician = self.rng.choice(self.technicians)

            req_type = self.rng.choice(list(type_descriptions.keys()))
            base_text = type_descriptions[req_type]

            description = f"{base_text} – model: {model_name} [Nr seryjny: {machine.serial_number}]."

            min_report_time = datetime.combine(machine.purchase_date, time(8, 0))
            max_report_time = max(min_report_time, self.now - timedelta(days=7))
            reported_at = self._datetime_between(min_report_time, max_report_time)
            
            start_date = reported_at + timedelta(hours=self.rng.randint(1, 72))
            end_date = start_date + timedelta(hours=self.rng.randint(1, 48))

            self.tables["service_request"].append(
                ServiceRequest(
                    request_id=self._next_id("service_request"),
                    machine_id=machine.machine_id,
                    reporter_account_id=reporter.account_id if reporter else None,
                    technician_id=technician.technician_id,
                    request_type=req_type,
                    reported_at=reported_at,
                    description=description,
                    start_date=start_date,
                    end_date=end_date
                )
            )

        for machine in self.tables["machine"]:
            if machine.tech_condition != 'sprawna':
                model = models_dict.get(machine.model_id)
                model_name = model.name if model else "Sprzęt ogólny"

                reporter = self.rng.choice(self.accounts) if self._bool(0.7) else None
                technician = self.rng.choice(self.technicians) if self._bool(0.8) else None

                reported_at = self._datetime_between(self.now - timedelta(days=14), self.now - timedelta(hours=1))

                start_date = None
                if technician:
                    start_date = reported_at + timedelta(hours=self.rng.randint(1, 12))

                req_type = 'rutynowa_konserwacja' if machine.tech_condition == 'w_konserwacji' else self.rng.choice(['uszkodzona_czesc', 'brakujaca_czesc', 'zuzyta_czesc'])
                base_text = type_descriptions[req_type]

                description = f"AWARIA: {base_text} – model: {model_name} [Nr seryjny: {machine.serial_number}]."

                self.tables["service_request"].append(
                    ServiceRequest(
                        request_id=self._next_id("service_request"),
                        machine_id=machine.machine_id,
                        reporter_account_id=reporter.account_id if reporter else None,
                        technician_id=technician.technician_id if technician else None,
                        request_type=req_type,
                        reported_at=reported_at,
                        description=description,
                        start_date=start_date,
                        end_date=None
                    )
                )

    def _make_exercises(self):
        for name, desc, difficulty, _ in _EXERCISES:
            self.tables["exercise"].append(
                Exercise(
                    exercise_id=self._next_id("exercise"),
                    name=name,
                    description=desc,
                    difficulty_level=difficulty
                )
            )

    def _make_required_equipment(self):
        category_map = {cat.name: cat for cat in self.tables["equipment_category"]}
        
        for exercise_data, exercise_obj in zip(_EXERCISES, self.tables["exercise"]):
            required_category_names = exercise_data[3]
            
            for cat_name in required_category_names:
                if cat_name in category_map:
                    target_category = category_map[cat_name]
                    self.tables["required_equipment"].append(
                        RequiredEquipment(
                            exercise_id=exercise_obj.exercise_id,
                            category_id=target_category.category_id
                        )
                    )

    def _make_training_plans(self):
        goals = [
            "Budowa masy mięśniowej", 
            "Redukcja tkanki tłuszczowej", 
            "Poprawa kondycji i wydolności", 
            "Powrót do formy po kontuzji",
            "Zwiększenie siły maksymalnej"
        ]

        trainer_recommendations = [
            "Pamiętaj o odpowiednim nawodnieniu w trakcie treningu i rolowaniu mięśni po jego zakończeniu.",
            "W przypadku odczuwania bólu stawów natychmiast przerwij ćwiczenie i skonsultuj się z trenerem.",
            "Skup się na poprawności technicznej wykonywanych powtórzeń, unikaj zrywów i pracy bez kontroli.",
            "Zadbaj o 8 godzin snu każdej nocy oraz zbilansowaną dietę bogatą w pełnowartościowe białko.",
            "Przed każdym treningiem wykonaj 10-minutową rozgrzewkę ogólnorozwojową i mobilizację stawów."
        ]
        
        num_clients_with_plan = int(len(self.clients) * self.training_plan_fraction)
        selected_clients = self.rng.sample(self.clients, num_clients_with_plan)
        
        for client in selected_clients:
            num_plans = self.rng.randint(1, 3)
            trainer = self.rng.choice(self.trainers)
            
            max_start = max(client.registered_at.date(), self.now.date() - timedelta(days=60))
            current_start_date = self._date_between(client.registered_at.date(), max_start)
            
            for _ in range(num_plans):
                duration_weeks = self.rng.randint(4, 12)
                valid_to = current_start_date + timedelta(weeks=duration_weeks)
                
                goal = self.rng.choice(goals)
                
                self.tables["training_plan"].append(
                    TrainingPlan(
                        plan_id=self._next_id("training_plan"),
                        client_id=client.client_id,
                        trainer_id=trainer.trainer_id,
                        name=f"Plan: {goal} ({duration_weeks} tyg.)",
                        goal=goal,
                        valid_from=current_start_date,
                        valid_to=valid_to,
                        recommendations=self.rng.choice(trainer_recommendations)
                    )
                )
                
                current_start_date = valid_to + timedelta(days=self.rng.randint(1, 14))
                if current_start_date > self.now.date() + timedelta(days=180):
                    break

    def _make_plan_exercises(self):
        exercises = self.tables["exercise"]
        
        for plan in self.tables["training_plan"]:
            num_exercises = self.rng.randint(4, min(8, len(exercises)))
            chosen_exercises = self.rng.sample(exercises, num_exercises)
            
            for exercise in chosen_exercises:
                self.tables["plan_exercise"].append(
                    PlanExercise(
                        plan_id=plan.plan_id,
                        exercise_id=exercise.exercise_id,
                        set_count=self.rng.randint(3, 5),
                        rep_count=self.rng.randint(5, 15)
                    )
                )

    def generate(self):
        self._make_rooms()
        self._make_equipment_categories()
        self._make_stations()
        self._make_machine_models()
        self._make_machines()
        self._make_service_requests()
        self._make_exercises()
        self._make_required_equipment()
        self._make_training_plans()
        self._make_plan_exercises()

        return self.tables


def generate_facility_and_training_data(
        accounts: list[UserAccount],
        clients: list[Client],
        trainers: list[Trainer],
        technicians: list[Technician],
        training_plan_fraction: float = 0.20,
        n_historical_service_requests: int = 300,
        warehouse_machines_count: int = 15,
        reference_time: datetime = _DEFAULT_REFERENCE_TIME):
    
    generator = _FacilityGenerator(
        reference_time=reference_time,
        accounts=accounts,
        clients=clients,
        trainers=trainers,
        technicians=technicians,
        training_plan_fraction=training_plan_fraction,
        n_historical_service_requests=n_historical_service_requests,
        warehouse_machines_count=warehouse_machines_count
    )
    return generator.generate()