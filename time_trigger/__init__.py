import azure.functions as func
import logging

def main(myTimer: func.TimerRequest) -> None:
    logging.error("!!!!Python time trigger ERROR!!!!!")