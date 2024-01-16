# venv ... creating the clusters ...

# Setting peresistan env variables 
- echo "export API_URL='http://127.0.0.1:8000/api/v1'" >> ~/.bashrc
- echo "export TEMPLATE_DIR='YOUR_PATH_TO_TEMPLATES_HERE'" >> ~/.bashrc
    - Example: 
    - echo "export TEMPLATE_DIR='/mnt/c/Users/skand/Downloads/PFE/miro_llo_kinD/miro_llo_kinD/templates'" >> ~/.bashrc 
- echo "export CRD_GROUP='charity-project.eu'" >> ~/.bashrc
- echo "export CRD_VERSION='v1'" >> ~/.bashrc
- echo "export MANAGEMENT_CLUSTER='YOUR_MANAGEMENT_CLUSTER_NAME'" >> ~/.bashrc
    - Example: 
    - echo "export MANAGEMENT_CLUSTER='management-cluster'" >> ~/.bashrc
# Loading the env variables 
source ~/.bashrc

# Confirme that the env variables exists 
echo $API_URL
echo $TEMPLATE_DIR
echo $CRD_GROUP
echo $CRD_VERSION
echo $MANAGEMENT_CLUSTER
# Activate Venv
source venv/bin/activate

# Start the rest api 
cd be
uvicorn main:app --reload

# Start the operator 
cd llo/kopf_operator
kopf run k8s-operator.py