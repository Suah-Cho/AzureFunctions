import logging
import azure.functions as func
import os

app = func.FunctionApp()

@app.schedule(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    logging.error('Python timer trigger function executed.')

    logging.info('Python timer trigger function executed.')