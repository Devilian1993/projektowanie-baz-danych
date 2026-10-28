from people_and_access_data import *
from models import *

with SessionLocal() as session:
    # clear the database, be careful or sth
    names = inspect(session.connection()).get_table_names()
    tables = ", ".join(f'"{name}"' for name in names)
    session.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY"))

    print(f"\nCleared {len(names)} tables\n")

    result = generate_people_and_access_data(
        n_accounts=15000,
        n_failed_logins=1000,
        n_entries=30000,
        user_account_fractions={
            "client": 0.80,
            "trainer": 0.08,
            "receptionist": 0.05,
            "technician": 0.04,
            "administrator": 0.03
        }
    )

    session.add_all([row for rows in result.values() for row in rows])
    session.flush()

    for statement in SEQUENCE_RESET_SQL:
        session.execute(text(statement))

    session.commit()

    print("Rows now in the database:")
    for table in result:
        count = session.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
        print(f"  {table}: {count}")
