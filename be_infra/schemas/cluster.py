from pydantic import BaseModel
from typing import Optional

class Cluster(BaseModel):
    # required fields
    infraProvider: str
    infraProviderConfig: str
    clusterName: str
    kubernetesVersion: str
    workerMachineCount: int
    # # optional fields
    bootstrapProvider: Optional[str] = None
    flavor: Optional[str] = None
    controlPlaneCount: Optional[int] = None
    controlPlaneFlavor: Optional[str] = None
    workerMachineFlavor: Optional[str] = None
    image: Optional[str] = None