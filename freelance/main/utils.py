from django.conf import settings
from django.db import connections

def change_database_credentials(new_user, new_password):
    settings.DATABASES['default']['USER'] = new_user
    settings.DATABASES['default']['PASSWORD'] = new_password
    connections['default'].close()

def test_db_credentials(username, password):
    """Перевірка, чи можна з'єднатись з базою від імені користувача."""
    from psycopg2 import connect, OperationalError
    try:
        conn = connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=username,
            password=password,
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
        )
        conn.close()
        return True
    except OperationalError:
        return False