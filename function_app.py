import logging
import azure.functions as func
import os
# import sshtunnel
# import psycopg


ssh_host = os.environ["SSH_HOST"]
ssh_username = os.environ["SSH_USERNAME"]
ssh_key = os.environ["SSH_KEY"]
db_host = os.environ["DB_HOST"]
db_name = os.environ["DB_NAME"]
db_user = os.environ["DB_USER"]
db_password = os.environ["DB_PASSWORD"]


app = func.FunctionApp()

# update func
@app.schedule(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    logging.error('Python timer trigger function executed.')

    # try:
    #     logging.info("-------TRY CONNCTION TO DB------")
    #     tunnel = sshtunnel.SSHTunnelForwarder(
    #         (ssh_host, 22),
    #         ssh_username=ssh_username,
    #         ssh_pkey=ssh_key,
    #         remote_bind_address=(db_host, 3306)
    #     )
    #     tunnel.start()

    #     conn = psycopg.connect(
    #         host='localhost',
    #         user=db_user,
    #         password=db_password,
    #         db=db_name,
    #         port=tunnel.local_bind_port
    #     )

    #     logging.info("-------DB CONNECTION SUCCESS------")

    # except Exception as e:
    #     logging.error(f"DB CONNECTION ERROR: {e}")