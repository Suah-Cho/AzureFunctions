import logging
import azure.functions as func
import os

storage_connection_string = os.environ["CONNECT_STRING"]

ssh_host = os.environ["SSH_HOST"]
ssh_username = os.environ["SSH_USERNAME"]
ssh_key = os.environ["SSH_KEY"]
db_host = os.environ["DB_HOST"]
db_name = os.environ["DB_NAME"]
db_user = os.environ["DB_USER"]
db_password = os.environ["DB_PASSWORD"]

app = func.FunctionApp()

logging.info("-----------------Python timer trigger function-----------------")
@app.schedule(schedule="*/30 * * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('!!!!!!The timer is past due!!!!!!!')

    logging.info('!!!!!!!!!Python timer trigger function executed.!!!!!!!!')