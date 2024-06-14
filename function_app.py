import logging
import azure.functions as func
import psycopg2
import os

app = func.FunctionApp()

@app.schedule(schedule="*/10 * * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:

    logging.info('!!!!!!!!!Python timer trigger function executed.!!!!!!!!')
    logging.error('!!!!!add env!!!!!')

    # SSH_HOST = os.environ['SSH_HOST']
    # SSH_USERNAME = os.environ['SSH_USERNAME']
    # logging.info(f"SSH_HOST: {SSH_HOST}, SSH_USERNAME: {SSH_USERNAME}")
    db_connection_string = os.environ['DB_CONNECTION_STRING']
    logging.info(f"DB_CONNECTION_STRING: {db_connection_string}")

    # connect to azure database
    try:
        con = psycopg2.connect(db_connection_string)
        cur = con.cursor()
        logging.info("Connected to database")

        cur.execute("SELECT * FROM gh_data_item limit 3;")
        rows = cur.fetchall()
        for row in rows:
            logging.info(row)
        cur.close()
        con.close()
    except Exception as e:
        logging.error(f"DB CONNECT Error: {e}")