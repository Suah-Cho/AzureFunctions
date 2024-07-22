import logging
import azure.functions as func
import psycopg2
import sshtunnel
import os
from azure.storage.blob import BlobServiceClient
from io import StringIO
import pandas as pd
import paramiko

app = func.FunctionApp()

@app.event_grid_trigger(arg_name="azeventgrid")
def EventGridTrigger(azeventgrid: func.EventGridEvent):
    logging.info('Python EventGrid trigger processed an event')
    logging.info(f"EventGridEvent: {azeventgrid.get_json()}")

    host = os.environ['SSH_HOST']
    username = os.environ['SSH_USERNAME']
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ssh_key_path = os.path.join(current_dir, 'ssh_key.pem')

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(host, username=username, key_filename=ssh_key_path)

        acr_registry = os.environ['ACR_REGISTRY']
        acr_username = os.environ['ACR_USERNAME']
        acr_password = os.environ['ACR_PASSWORD']
        pat = os.environ['PAT']
        repo = os.environ['GITHUB_REPO']

        command = f"""
        az acr login --name {acr_registry} --username {acr_username} --password {acr_password}
        cd /home/azueruser/cicd
        if [ -d "/home/azueruser/cicd" ]; then
          echo "Directory exists"
          cd /home/azueruser/cicd
          git pull
          cd resources
        else
          echo "Directory does not exist"
          git clone https://{pat}@github.com/{repo}.git /home/azureuser/cicd
          cd /home/azureuser/cicd/resources
        fi
        """

        stdin, stdout, stderr = client.exec_command(command)

        output = stdout.read().decode('utf-8')
        logging.info(f"Output: {output}")

        client.close()
    except Exception as e:
        logging.error(f"SSH ERROR: {e}")



def getCon():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ssh_key_path = os.path.join(current_dir, 'ssh_key.pem')

    # logging.info(f"ssh_key_path: {ssh_key_path}")

    SSH_HOST = os.environ['SSH_HOST']
    SSH_USERNAME = os.environ['SSH_USERNAME']

    # logging.info(f"SSH_HOST: {SSH_HOST}, SSH_USERNAME: {SSH_USERNAME}")
    DB_HOST = os.environ['DB_HOST']
    DB_USER = os.environ['DB_USER']
    DB_NAME = os.environ['DB_NAME']
    DB_PASSWORD = os.environ['DB_PASSWORD']
    # logging.info(f'DB_HOST: {DB_HOST}, DB_USER: {DB_USER}, DB_NAME: {DB_NAME}, DB_PASSWORD: {DB_PASSWORD}')
    
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


def insert_blob_to_database(df, con, blob, blob_service_client, container_client):
    try:
        cur = con.cursor()

        # Insert DataFrame records one by one.
        for index, row in df.iterrows():
            cur.execute("SELECT name FROM devices WHERE device_id = %s;", (row['device_id'],))
            device_name = cur.fetchone()[0]
            cur.execute("SELECT kr_name FROM data_types WHERE id = %s;", (row['data_type'],))
            data_type_name = cur.fetchone()[0]
            # logging.info(f"Device name: {device_name} - Data type name: {data_type_name}")
            cur.execute("INSERT INTO gh_data_item (device_id, device_name, value, data_type_id, data_type_name) VALUES (%s, %s, %s, %s, %s);",
                        (row['device_id'], device_name, row['value'], row['data_type'], data_type_name))
            
        con.commit()

        logging.info(f"----------------Blob {blob.name} inserted to database successfully.------------")
        cur.close()

        # Move the blob to the done folder
        try:
            blob_client = container_client.get_blob_client(blob.name)
            new_blob_name = "done/" + blob.name[len("todo-"):]
            new_blob_client = blob_service_client.get_blob_client("data", new_blob_name)
            new_blob_client.start_copy_from_url(blob_client.url)
            blob_client.delete_blob()

            logging.info(f"-------------------Blob {blob.name} moved to done folder.---------------")
        except Exception as e:
            logging.error(f"BLOB MOVE ERROR: {e}")
    except Exception as e:
        logging.error(f"DATABASE INSERT ERROR: {e}")
        raise e



# @app.schedule(schedule="* */1 * * * *", arg_name="myTimer", run_on_startup=True,
#               use_monitor=False) 
# def timer_trigger(myTimer: func.TimerRequest) -> None:

#     logging.info('!!!!!!!!!Python timer trigger function executed.!!!!!!!!')

#     # connect to azure database
#     try:
#         con = getCon()
#         # cur = con.cursor()
#         logging.info("!!!!!!!!!!DATABSE CONNECTED SUCCESSFULLY!!!!!!!!!!")
#         try:
#             # Create BlobServiceClient
#             blob_service_client = BlobServiceClient.from_connection_string(os.environ['AzureWebJobsStorage'])

#             # Get the container Client
#             container_client = blob_service_client.get_container_client("data")

#             # List the blobs in the container
#             blob_list = container_client.list_blobs(name_starts_with="todo-")

#             # Read the blob content
#             for blob in blob_list:
#                 logging.info(f"Blob name: {blob.name}")
#                 blob_client = container_client.get_blob_client(blob.name)
#                 blob_content = StringIO(blob_client.download_blob().readall().decode('utf-8'))
#                 df = pd.read_csv(blob_content)
#                 insert_blob_to_database(df, con, blob, blob_service_client, container_client)
#         except Exception as e:
#             logging.error(f"AZURE STORAGE ERROR: {e}")
#     except Exception as e:
#         logging.error(f"DATABASE CONNECT ERROR: {e}")


