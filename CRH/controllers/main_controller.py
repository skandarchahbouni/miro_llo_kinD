import json
import logging
import CRH.controllers.crd_controller as crd_controller




def handle_delete_msg(app_name,app_id):
    try:
        # app_name = msg.get("app_name")
        # app_id = msg.get("app_id")
        # retrieve from db
        app_resource_name = app_name+"-"+ str(app_id)
        logging.info(f"deleting app {app_resource_name}...")

        #checking if app exists :
        app_resource= crd_controller.get_crd('default','applications',app_resource_name)
        if app_resource : #exists 

            app_resource = crd_controller.get_crd('default','applications',app_resource_name)

            crd_controller.delete_from_crd(namespace="default", plural="applications", name=app_resource_name)

            #retrieving components 
            components =app_resource["spec"]["components"]
            for comp in components:
                logging.info(f"Deleting component {comp['name']} ...")
                crd_controller.delete_from_crd(
                    namespace="default", plural="components", name= comp["name"]
                )
        else : #deosn't exist 
            raise Exception(f"failed while delete app {app_name} : app doesn't exist")


    except KeyError as ke:
        logging.error(
            f"CRDHandler: main_controller.py <<handle_delete_msg>>: Key not found in dictionary, {ke}."
        )
    except Exception as e:
        logging.error(f"CRDHandler: main_controller.py <<handle_delete_msg>> \n{e}")


def handle_update_msg(decision_body,app):
    try:
        # decision_id = msg.get("deployment_id")
        # # retrieve from db
        # decision = crd_controller.retrieve_from_db(decision_id)
        # app = decision["app"]
        components = app["components"]
        # decision_body = decision["decision_body"]
        app_resource_name=app["name"]+"-"+str(app["id"])

        app_resource= crd_controller.get_crd('default','applications',app_resource_name)
        if app_resource : #exists 
            
            new_component_list= crd_controller.getComponentsList(components)
            existing_component_list = crd_controller.getComponentsList(app_resource["spec"]["components"])
            merged_component_list= list(set(new_component_list + existing_component_list))        

            # handling apps :
            app_crd = crd_controller.convert_to_app_crd(app, decision_body)
            logging.info(f"Updating application {app['name']} ...")
            crd_controller.update_from_crd(crd=app_crd,namespace="default", plural="applications", name=app_resource_name)


            for comp in components:
                if comp["name"] in existing_component_list : # update component
                    comp_crd = crd_controller.convert_to_comp_crd(comp=comp, app_name=app_resource_name)
                    logging.info(f"Updating component {comp['name']} ...")
                    crd_controller.update_from_crd(
                        crd=comp_crd, namespace="default", plural="components", name=comp["name"]
                    )
                    merged_component_list.remove(comp["name"])
                elif comp["name"] not in existing_component_list: #create component
                    comp_crd = crd_controller.convert_to_comp_crd(comp=comp, app_name=app_resource_name)
                    logging.info(f"Creating component {comp['name']} ...")
                    crd_controller.create_from_crd(crd=comp_crd, namespace='default', plural="components")
                    merged_component_list.remove(comp["name"])

            for comp in merged_component_list: #delete component
                logging.info(f"Deleting component {comp} ...")
                crd_controller.delete_from_crd(
                    namespace="default", plural="components", name= comp
                )
        else : 
            raise Exception(f"Failed while updating : {app_resource_name} doesn't exist")

    except KeyError as ke:
        logging.error(
            f"CRDHandler: main_controller.py <<handle_update_msg>>: Key not found in dictionary, {ke}."
        )
    except Exception as e:
        logging.error(f"CRDHandler: main_controller.py <<handle_update_msg>> \n{e}")


def handle_create_msg(decision_body,app):
    try:
        # decision_id = msg.get("deployment_id")
        # # retrieve from db
        # decision = crd_controller.retrieve_from_db(decision_id)
        # app = decision["app"]
        components = app["components"]
        # print(components)
        # decision_body = decision["decision_body"]
        app_resource_name=app["name"]+"-"+str(app["id"])
        # handling apps :
        app_resource= crd_controller.get_crd('default','applications',app_resource_name)
        print(app_resource)
        if app_resource : #exists 
            raise Exception(f"failed while creating app {app_resource_name} : app already exists")
        else :
            app_crd = crd_controller.convert_to_app_crd(app, decision_body)
            logging.info(f"creating application {app_resource_name} ...")
            crd_controller.create_from_crd(
                app_crd, "default", "applications"
            )  #'default' is the name of the name space for app

            # handling components crds :
            for comp in components:
                comp_crd = crd_controller.convert_to_comp_crd(comp=comp, app_name=app_resource_name)
                logging.info(f"Creating component {comp['name']} ...")
                crd_controller.create_from_crd(crd=comp_crd, namespace='default', plural="components")


    except KeyError as ke:
        logging.error(
            f"CRDHandler: main_controller.py <<handle_create_msg>>: Key not found in dictionary, {ke}.\n"
        )
    except Exception as e:
        logging.error(f"CRDHandler: main_controller.py <<handle_create_msg>> \n{e}")
