import logging
import azure.functions as func
import psycopg2
import sshtunnel
import os
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()

def getCon():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ssh_key_path = os.path.join(current_dir, 'ssh_key.pem')

    logging.info(f"ssh_key_path: {ssh_key_path}")

    SSH_HOST = os.environ['SSH_HOST']
    SSH_USERNAME = os.environ['SSH_USERNAME']
    SSH_KEY = os.environ['SSH_KEY']
    logging.info(f"SSH_HOST: {SSH_HOST}, SSH_USERNAME: {SSH_USERNAME}")
    DB_HOST = os.environ['DB_HOST']
    DB_USER = os.environ['DB_USER']
    DB_NAME = os.environ['DB_NAME']
    DB_PASSWORD = os.environ['DB_PASSWORD']
    logging.info(f'DB_HOST: {DB_HOST}, DB_USER: {DB_USER}, DB_NAME: {DB_NAME}, DB_PASSWORD: {DB_PASSWORD}')
    
    tunnel = sshtunnel.SSHTunnelForwarder(
        (SSH_HOST, 22),
        ssh_username = SSH_USERNAME,
        ssh_pkey = ssh_key_path,
        remote_bind_address = (DB_HOST, 5432),
    ) 

    tunnel.start()

    con = psycopg2.connect(
        host='localhost',
        port=tunnel.local_bind_port,
        user=DB_USER,
        database=DB_NAME,
        password=DB_PASSWORD
    )

    return con

@app.schedule(schedule="*/10 * * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:

    logging.info('!!!!!!!!!Python timer trigger function executed.!!!!!!!!')
    logging.error('!!!!!GET CONNECTION TO DATABASE WITH SSHTUNNEL< PSYCOPG2!!!!!')

    # connect to azure database
    try:
        con = getCon()
        # cur = con.cursor()
        logging.info("!!!!!!!!!!DATABSE CONNECTED SUCCESSFULLY!!!!!!!!!!")
        try:
            # Create BlobServiceClient
            blob_service_client = BlobServiceClient.from_connection_string(os.environ['AzureWebJobsStorage'])

            # Get the container Client
            container_client = blob_service_client.get_container_client("data")

            # List the blobs in the container
            blob_list = container_client.list_blobs(name_starts_with="todo-")

            # Read the blob content
            for blob in blob_list:
                logging.info(f"Blob name: {blob.name}")
        except Exception as e:
            logging.error(f"AZURE STORAGE ERROR: {e}")
        # cur.execute("SELECT * FROM gh_data_item limit 3;")
        # rows = cur.fetchall()
        # for row in rows:
        #     logging.info(row)
        # cur.close()
        # con.close()
    except Exception as e:
        logging.error(f"DATABASE CONNECT ERROR: {e}")