import logging
import os

# API_URL = os.environ.get("API_URL")
API_URL = "localhost:3000"

def create_cluster(clusterData):
    logging.info(f"hitting endpoint: POST {API_URL}/clusters ")

def delete_cluster(cluster_name):
    logging.info(f"hitting endpoint: DELETE {API_URL}/clusters/{cluster_name} ")

def update_cluster(clusterData):
    logging.info(f"hitting endpoint: PATCH {API_URL}/clusters ")

def link_clusters(linkData):
    logging.info(f"hitting endpoint: POST {API_URL}/links ")

def unlink_clusters(linkData):
    logging.info(f"hitting endpoint: DELETE {API_URL}/links ")

def update_links(oldLink, newLink):
    # delete old link
    logging.info(f"hitting endpoint: DELETE {API_URL}/links ")
    # create new link
    logging.info(f"hitting endpoint: POST {API_URL}/links ")