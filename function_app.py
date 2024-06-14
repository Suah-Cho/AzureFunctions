import logging
import azure.functions as func
# import psycopg2
import os

app = func.FunctionApp()

@app.schedule(schedule="*/10 * * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:

    logging.info('!!!!!!!!!Python timer trigger function executed.!!!!!!!!')
    logging.error('!!!!!add env!!!!!')

    # SSH_HOST = os.environ('SSH_HOST')
    # SSH_USERNAME = os.environ('SSH_USERNAME')
    # logging.info(f"SSH_HOST: {SSH_HOST}, SSH_USERNAME: {SSH_USERNAME}")