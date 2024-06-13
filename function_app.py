import logging
import azure.functions as func
import os

ssh_host = os.environ["SSH_HOST"]
ssh_username = os.environ["SSH_USERNAME"]
ssh_key = os.environ["SSH_KEY"]
db_host = os.environ["DB_HOST"]
db_name = os.environ["DB_NAME"]
db_user = os.environ["DB_USER"]
db_password = os.environ["DB_PASSWORD"]

app = func.FunctionApp()

@app.schedule(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    logging.error('Python timer trigger function executed.')

    logging.info('Python timer trigger function executed.')