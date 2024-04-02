  
app_info={"app": {
"id": 72,
    "tosca": None,
    "updated_at": None,
    "cluster_id": None,
    "name": "cyango-cloud-studio",
    "owner": "cyango-xr-developer",
    "created_at": "2024-02-12T16:29:12",

 "components": [
    {
      "placement": "CLOUD",
      "replicas": 1,
      "cluster_id": None,
      "id": 356,
      "name": "cyango-backend",
      "image": "repository.charity-project.eu/dotes/cyango-backend:beta",
      "app_id": 72,
      "environment_variables": [],
      "service": {
        "is_public": True,
        "is_peered": True,
        "container_port": 32777,
        "protocol": "TCP",
        "id": 97,
        "cluster_port": 32777,
        "component_id": 356
      }
    },
    {
      "placement": "CLOUD",
      "replicas": 1,
      "cluster_id": None,
      "id": 357,
      "name": "cyango-database",
      "image": "repository.charity-project.eu/dotes/cyango-database:beta",
      "app_id": 72,
      "environment_variables": [],
      "service": {
        "is_public": False,
        "is_peered": True,
        "container_port": 27017,
        "protocol": "TCP",
        "id": 98,
        "cluster_port": 27017,
        "component_id": 357
      }
    }
  ]

}
}

app= {"app_info": {
"app": {
"id": 72,
    "tosca": None,
    "updated_at": None,
    "cluster_id": None,
    "name": "cyango-cloud-studio",
    "owner": "cyango-xr-developer",
    "created_at": "2024-02-12T16:29:12",

},
"components":  [
    {
        "placement": "CLOUD",
        "replicas": 1,
        "cluster_id": None,
        "id": 356,
        "name": "cyango-backend",
        "image": "repository.charity-project.eu/dotes/cyango-backend:beta",
        "app_id": 72,
        "environment_variables": [],
         "service": {
         "is_public": True,
         "is_peered": True,
         "container_port": 32777,
         "protocol": "TCP",
         "id": 97,
         "cluster_port": 32777,
         "component_id": 356
        } },
        
        {"placement": "CLOUD",
        "replicas": 1,
        "cluster_id": None,
        "id": 357,
        "name": "cyango-database",
        "image": "repository.charity-project.eu/dotes/cyango-database:beta",
        "app_id": 72,
        "environment_variables": [],      
        "service": {
        "is_public": False,
        "is_peered": True,
        "container_port": 27017,
        "protocol": "TCP",
        "id": 98,
        "cluster_port": 27017,
        "component_id": 357
        }
}
]

}
}

print(app_info["app"]["id"])