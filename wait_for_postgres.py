import time

import psycopg2

from IonInspector.settings import DATABASES


def connect_postgres(dbname, host, user, password):
    try:
        conn = psycopg2.connect(dbname=dbname, host=host, user=user, password=password)
        conn.cursor()
    except Exception as e:
        print("Waiting for postgres: {}".format(e))
        return False
    finally:
        time.sleep(1)
    return True


connected = False
while not connected:
    connected = connect_postgres(
        host=DATABASES["default"]["HOST"],
        user=DATABASES["default"]["USER"],
        password=DATABASES["default"]["PASSWORD"],
        dbname=DATABASES["default"]["NAME"]
    )
