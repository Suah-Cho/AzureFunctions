import logging
import azure.functions as func
import os
import sshtunnel
import psycopg

app = func.FunctionApp()

ssh_host = os.environ["SSH_HOST"]
ssh_username = os.environ["SSH_USERNAME"]
ssh_key = os.environ["SSH_KEY"]
db_host = os.environ["DB_HOST"]
db_name = os.environ["DB_NAME"]
db_user = os.environ["DB_USER"]
db_password = os.environ["DB_PASSWORD"]

@app.schedule(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:

    logging.info('Python timer trigger function executed.')
    logging.error('!!This is an error message!!')

    try:
        # Connect to the database
        tunnel = sshtunnel.SSHTunnelForwarder(
                (ssh_host, 22),
                ssh_username=ssh_username,
                ssh_pkey=ssh_key,
                remote_bind_address=(db_host, 5432)
            )

        tunnel.start()

        con = psycopg.connect(
            host='localhost',
            port=tunnel.local_bind_port,
            database=db_name,
            user=db_user,
            password=db_password
        )

        logging.info("Connection established")
    except Exception as e:
        # Failed to connect to the database
        logging.error(f"Database Connections Failed!!!: {e}")