from pydantic import BaseModel
from typing import Optional

class ClusterUpdate(BaseModel):
    workerMachineCount: Optional[int] = None
    controlPlaneCount: Optional[int] = None