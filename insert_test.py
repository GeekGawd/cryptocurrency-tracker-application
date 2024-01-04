import psycopg
conn = psycopg.connect(dbname='tanxfi',
        user='postgres',
        password='admin',
        host='localhost',
        port='5432', autocommit=True)
conn.execute("LISTEN tracker_coinsymbol")
gen = conn.notifies()
for notify in gen:
    print(notify.payload)