from pydantic import BaseModel

class Link(BaseModel):
    localCluster: str
    remoteCluster: str