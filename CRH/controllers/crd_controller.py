import logging
import os
import requests
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.config.config_exception import ConfigException
from jinja2 import Environment, FileSystemLoader
# from app.exceptions.crd_conroller_exception import Exception
import yaml,json

log = logging.getLogger("app")
API_DOMAIN = os.environ["CRD_GROUP"]
API_VERSION = os.environ["CRD_VERSION"]
crd_templates='/home/khaled/miro_llo_kinD/CRH/crd_templates'
app_template_name='app-crd.yaml'
comp_template_name='comp-crd.yaml'

def convert_to_app_crd(app, decision):
    try:
        environment = Environment(
            loader=FileSystemLoader(crd_templates)
        )
        deployment_template = environment.get_template(app_template_name)
        
        api_domaine_version=API_DOMAIN + "/" + API_VERSION
        cluster_comp_list = find_cluster_for_components(decision)
        crd = deployment_template.render(
            version=api_domaine_version,
            name=app["name"]+ "-" + str(app["id"]),
            owner=app["owner"],
            cluster="blue",
            components=[
                {"name": comp["name"], "cluster": cluster_comp_list[comp["name"]]}
                for comp in app["components"]
            ],
        )
        output_crd = yaml.safe_load(crd)
        return output_crd
    except TypeError as e:

        raise Exception(f"CRDHandler: crd_controller.py <<convert_to_app_crd>>: TypeError, Please ensure to set env variables, {e}")
    except KeyError as ke:
 
        raise Exception( f"CRDHandler: crd_controller.py <<convert_to_app_crd>>: Key not found in dictionary, {ke}.")
    except Exception as e:

        raise Exception(f"CRDHandler: crd_controller.py <<convert_to_app_crd>>: \n{e}")


def convert_to_comp_crd(comp, app_name):
    try:
        environment = Environment(
            loader=FileSystemLoader(crd_templates)
        )

       
        api_domaine_version=API_DOMAIN + "/" + API_VERSION
        deployment_template = environment.get_template(comp_template_name)
        service = comp.get("service",{})
        if service is None : 
            service = {}
        crd = deployment_template.render(
            version=api_domaine_version,
            name=comp["name"],
            image_name=comp["image"],
            app_name=app_name,
            is_public=service.get("is_public", False),
            is_peered=service.get("is_peered", False),
            is_exposing_metrics=service.get("is_exposing", False), #doesn't exist in datamodel
            container_port=service.get("container_port", 0),
            cluster_port=service.get("cluster_port", 0)
        )
        output_crd = yaml.safe_load(crd)
        return output_crd
    except TypeError:

        raise Exception("CRDHandler: crd_controller.py <<convert_to_comp_crd>>: TypeError, Please ensure to set env variables.")
    except KeyError as ke:

        raise Exception(f"CRDHandler: crd_controller.py <<convert_to_comp_crd>>: Key not found in dictionary, {ke}.")
    except Exception as e:

        raise Exception(f"CRDHandler: crd_controller.py <<convert_to_comp_crd>>: \n{e}")


def convert_to_link_crd(clusters_names, link):
    try:
        environment = Environment(
            loader=FileSystemLoader(app_template_name)
        )

        api_domaine_version=API_DOMAIN + "/" + API_VERSION
        deployment_template = environment.get_template(os.environ["LINK_CRD"])
        if len(clusters_names) > 1:
            crd = deployment_template.render(
                version=api_domaine_version,
                name=link["id"],
                local_cluster=clusters_names[0],
                remote_cluster=clusters_names[1],
            )
            output_crd = yaml.safe_load(crd)
            return output_crd
        else:
            log.info(f" link {link['id']} belongs to only one cluster")
    except TypeError:

        raise Exception( f"CRDHandler: crd_controller.py <<convert_to_link_crd>>: TypeError, Please ensure to set env variables.")
    except KeyError as ke:

        raise Exception(f"CRDHandler: crd_controller.py <<convert_to_link_crd>>: Key not found in dictionary, {ke}.")
    except IndexError:

        raise Exception("CRDHandler: crd_controller.py <<convert_to_link_crd>>: Index out of bounds, 'cluster_names' list.")
    except Exception as e:

        raise Exception(f"CRDHandler: crd_controller.py <<convert_to_link_crd>>: \n{e}")


def convert_to_cluster_crd(cluster):
    try:
        environment = Environment(
            loader=FileSystemLoader(app_template_name)
        )

        api_domaine_version=API_DOMAIN + "/" + API_VERSION
        deployment_template = environment.get_template(os.environ["CLUSTER_CRD"])
        crd = deployment_template.render(
            version=api_domaine_version,
            name=cluster["name"],
            infra_provider=cluster["infra_provider"],
            conf_map_name=cluster["infra_provider"] + "-config",
            bootstrap_provider=cluster["bootstrap_provider"],
            kubernetes_version=cluster["kubernetes_version"],
            control_plane_count=cluster["control_plane_count"],
            control_plane_flavor=cluster["control_plane_flavor"],
            worker_machine_count=cluster["worker_machine_count"],
            worker_machine_flavor=cluster["worker_machine_flavor"],
            image=cluster["image"],
        )
        output_crd = yaml.safe_load(crd)
        return output_crd
    except TypeError:

        raise Exception("CRDHandler: crd_controller.py <<convert_to_cluster_crd>>: TypeError, Please ensure to set env variables.")
    except KeyError as ke:

        raise Exception(f"CRDHandler: crd_controller.py <<convert_to_cluster_crd>>: Key not found in dictionary, {ke}.")
    except Exception as e:

        raise Exception(f"CRDHandler: crd_controller.py <<convert_to_cluster_crd>>: \n{e}")


def update_from_crd(crd, namespace, plural, name):
    try:
        config.load_kube_config()

        api_client = client.ApiClient()
        api_instance = client.CustomObjectsApi(api_client)
        api_instance.patch_namespaced_custom_object(
            group=API_DOMAIN,
            version=API_VERSION,
            namespace=namespace,
            plural=plural,
            name=name,
            body=crd,
        )
        log.info(f"crd {name} updated succefully")
    except KeyError as ke:

        raise Exception( f"CRDHandler: crd_controller.py <<update_from_crd>>: Key not found in dictionary, {ke}.")
    except IndexError:

        raise Exception("CRDHandler: crd_controller.py <<update_from_crd>>: Index out of bounds, api_version.split('/')[1].")
    except ConfigException as _:

        raise Exception( "CRDHandler: crd_controller.py <<update_from_crd>>: load_kube_config.")
    except ApiException as ae:

        raise Exception(f"CRDHandler: crd_controller.py <<update_from_crd>>: patch_namespaced_custom_object. \n{ae}")
    except Exception as e:

        raise Exception(f"CRDHandler: crd_controller.py <<update_from_crd>>: \n{e}")


def create_from_crd(crd, namespace, plural):
    try:
        
        config.load_kube_config()
        
        
        log.info(crd)        
        api_client = client.ApiClient()
        api_instance = client.CustomObjectsApi(api_client)
        api_instance.create_namespaced_custom_object(
            group=API_DOMAIN,
            version=API_VERSION,
            namespace=namespace,
            plural=plural,
            body=crd,
        )
        log.info(f"crd {plural} created succefully")
    except KeyError as ke:

        raise Exception(f"CRDHandler: crd_controller.py <<create_from_crd>>: Key not found in dictionary, {ke}.")
    except IndexError:

        raise Exception(f"CRDHandler: crd_controller.py <<create_from_crd>>: Index out of bounds, api_version.split('/')[1].")
    except ConfigException as _:

        raise Exception( "CRDHandler: crd_controller.py <<create_from_crd>>: load_kube_config.")
    except ApiException as ae:

        raise Exception(f"CRDHandler: crd_controller.py <<create_from_crd>>: create_namespaced_custom_object. \n{ae}")
    except Exception as e:
        
        raise Exception(f"CRDHandler: crd_controller.py <<create_from_crd>>: \n{e}")


def delete_from_crd(namespace, plural, name):
    try:
        config.load_kube_config()
        api_client = client.ApiClient()
        api_instance = client.CustomObjectsApi(api_client)
        api_instance.delete_namespaced_custom_object(
            group=API_DOMAIN,
            version=API_VERSION,
            namespace=namespace,
            plural=plural,
            name=name,
        )
        log.info(f"crd {name} delete succefully")
    except KeyError as ke:

        raise Exception(f"CRDHandler: crd_controller.py <<delete_from_crd>>: Key not found in dictionary, {ke}.")
    except IndexError:

        raise Exception(f"CRDHandler: crd_controller.py <<delete_from_crd>>: Index out of bounds, api_version.split('/')[1].")
    except ConfigException as _:

        raise Exception("CRDHandler: crd_controller.py <<delete_from_crd>>: load_kube_config.")
    except ApiException as ae:

        raise Exception(f"CRDHandler: crd_controller.py <<delete_from_crd>>: delete_namespaced_custom_object. \n{ae}")
    except Exception as e:

        raise Exception(f"CRDHandler: crd_controller.py <<delete_from_crd>> \n{e}")


def get_crd(namespace, plural, name):
    try:
        config.load_kube_config()

        # Create an instance of the Kubernetes API client
        api_client = client.ApiClient()
        api_instance = client.CustomObjectsApi(api_client)
        resource = api_instance.get_namespaced_custom_object(
            group=API_DOMAIN,
            version=API_VERSION,
            namespace=namespace,
            plural=plural,
            name=name,
        )
        return resource
    
        
    except KeyError as ke:

        raise Exception(f"CRDHandler: crd_controller.py <<get_crd>>: Key not found in dictionary, {ke}.")
    except IndexError:

        raise Exception(f"CRDHandler: crd_controller.py <<get_crd>>: Index out of bounds, api_version.split('/')[1].")
    except ConfigException as _:

        raise Exception("CRDHandler: crd_controller.py <<get_crd>>: load_kube_config.")
    except ApiException as ae:
        exception_body = json.loads(ae.body)
        if ae.reason =="Not Found" and exception_body.get("details",{}).get("name",{})==name :
          log.info(f" resouece {name} not found\n")
          return None
        else : 
            raise Exception(f"CRDHandler: crd_controller.py <<get_crd>>: get_namespaced_custom_object. \n{ae}")
    except Exception as e:
            
            raise Exception(f"CRDHandler: crd_controller.py <<get_crd>> \n{e}")
    


# ------ helper functions ------#


def find_cluster_for_components(
    decision,
):  # this  return { "comp1":"cluster1","comp2":"cluster2"..etc}
    try:
        cluster_of_comp = {}
        for cluster, components in decision.items():
            for component in components:
                cluster_of_comp[component] = cluster
        return cluster_of_comp
    except Exception as e:

        raise e("CRDHandler: crd_controller.py <<find_cluster_for_components>>.")


def get_cluster_for_link(clusters, link_name):
    try:
        related_clusters = []
        for cluster in clusters:
            links_names = [link["id"] for link in cluster["cluster_links"]]
            if link_name in links_names:
                related_clusters.append(cluster["name"])
        return related_clusters
    except KeyError as ke:
        raise ke("CRDHandler: crd_controller.py <<get_cluster_for_link>>.")
    except Exception as e:
        raise e("CRDHandler: crd_controller.py <<get_cluster_for_link>>.")

def getComponentsList(components):
    comp_list=[comp["name"] for comp in components]
    return comp_list