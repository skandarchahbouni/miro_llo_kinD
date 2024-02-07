import logging
import os
import requests

# API_URL = os.environ.get("API_URL")
API_URL = "http://localhost:3000"

def create_cluster(clusterData):
    logging.info(f"Hitting endpoint: POST {API_URL}/clusters")
    response = requests.post(f'{API_URL}/clusters',json=clusterData)
    if response.status_code == 200:
        data = response.json()
        logging.info(f"Response: {data}")
    else:
        logging.error(f"Error: {response.status_code}")
        
def update_cluster(cluster_name, cluster_update):
    logging.info(f"Hitting endpoint: PATCH {API_URL}/clusters/{cluster_name}")
    response = requests.patch(f'{API_URL}/clusters/{cluster_name}',json=cluster_update)
    if response.status_code == 200:
        data = response.json()
        logging.info(f"Response: {data}")
    else:
        logging.error(f"Error: {response.status_code}")

def delete_cluster(cluster_name):
    logging.info(f"Hitting endpoint: DELETE {API_URL}/clusters/{cluster_name}")
    response = requests.delete(f'{API_URL}/clusters/{cluster_name}')
    if response.status_code == 200:
        data = response.json()
        logging.info(f"Response: {data}")
    else:
        logging.error(f"Error: {response.status_code}")

def link_clusters(linkData):
    logging.info(f"Hitting endpoint: POST {API_URL}/links")
    response = requests.post(f'{API_URL}/links',json=linkData)
    if response.status_code == 200:
        data = response.json()
        logging.info(f"Response: {data}")
    else:
        logging.error(f"Error: {response.status_code}")

def unlink_clusters(linkData):
    logging.info(f"hitting endpoint: DELETE {API_URL}/links")
    response = requests.delete(f'{API_URL}/links',json=linkData)
    if response.status_code == 200:
        data = response.json()
        logging.info(f"Response: {data}")
    else:
        logging.error(f"Error: {response.status_code}")