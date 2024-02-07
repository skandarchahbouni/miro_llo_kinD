from fastapi import APIRouter
from be_infra.schemas.link import Link

links_router = APIRouter()

@links_router.post('/links')
def create_link(link: Link):
    print(link)
    return link

@links_router.delete('/links')
def delete_link(link: Link):
    print(link)
    return link