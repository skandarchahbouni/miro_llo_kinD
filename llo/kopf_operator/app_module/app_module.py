import requests
import os
import logging

# API_URL = "http://orch-backend.orchestration.miro.onesource.pt/v1"
API_URL = os.environ.get("API_URL")


# -------------------------------------------------------------------- #
def create_app(spec: dict) -> requests.Response | None:
    logging.info("create_app function is called.")
    url = API_URL + "/apps"
    try:
        response = requests.post(url=url, json=spec)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [create_app function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [create_app function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [create_app function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [create_app function]")
    return None


def delete_app(spec: dict) -> requests.Response | None:
    logging.info("delete_app function is called.")
    url = API_URL + f"/apps/{spec['name']}"
    try:
        response = requests.delete(url=url, json=spec)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [delete_app function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [delete_app function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [delete_app function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [delete_app function]")
    return None


def update_app(spec: dict, old: list, new: list) -> requests.Response | None:
    logging.info("update_app function is called.")
    url = API_URL + f"/apps/{spec['name']}"
    try:
        response = requests.put(url=url, json={"spec": spec, "old": old, "new": new})
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [update_app function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [update_app function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [update_app function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [update_app function]")
    return None


# -------------------------------------------------------------------- #
def create_comp(spec: dict) -> requests.Response | None:
    logging.info("create_comp function is called.")
    url = API_URL + "/comps"
    try:
        response = requests.post(url=url, json=spec)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [create_comp function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [create_comp function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [create_comp function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [create_comp function]")
    return None


def delete_comp(spec: dict) -> requests.Response | None:
    logging.info("delete_comp function is called.")
    url = API_URL + f"/comps/{spec['name']}"
    try:
        response = requests.delete(url=url, json=spec)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [delete_comp function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [delete_comp function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [delete_comp function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [delete_comp function]")
    return None


def update_comp_deployment(spec: dict) -> requests.Response | None:
    logging.info("update_comp_deployment function is called.")
    url = API_URL + f"/comps/{spec['name']}/deployment"
    try:
        response = requests.put(url=url, json=spec)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [update_comp_deployment function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [update_comp_deployment function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [update_comp_deployment function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [update_comp_deployment function]")
    return None


def update_comp_expose_field(
    spec: dict, old: list, new: list
) -> requests.Response | None:
    logging.info("update_comp_expose_field function is called.")
    url = API_URL + f"/comps/{spec['name']}/expose"
    try:
        response = requests.put(url=url, json={"spec": spec, "old": old, "new": new})
        return response
    except requests.exceptions.ConnectionError:
        logging.error(
            "A connection error occurred. [update_comp_expose_field function]"
        )
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [update_comp_expose_field function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [update_comp_expose_field function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [update_comp_expose_field function]")
    return None
