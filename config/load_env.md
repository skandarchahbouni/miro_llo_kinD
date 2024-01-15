# Setting peresistan env variables 
- echo "export API_URL='http://127.0.0.1:8000/api/v1'" >> ~/.bashrc
- echo "export TEMPLATE_DIR='YOUR_PATH_TO_TEMPLATES_HERE'" >> ~/.bashrc
<!-- echo "export TEMPLATE_DIR='/mnt/c/Users/skand/Downloads/PFE/miro_llo_kinD/miro_llo_kinD/templates'" >> ~/.bashrc -->
- echo "export CRD_GROUP='charity-project.eu'" >> ~/.bashrc
- echo "export CRD_VERSION='v1'" >> ~/.bashrc

# Loading the env variables 
source ~/.bashrc

# Confirme that the env variables exists 
echo $API_URL
echo $TEMPLATE_DIR
echo $CRD_GROUP
echo $CRD_VERSION