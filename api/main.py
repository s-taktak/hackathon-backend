from fastapi import FastAPI

from api.routers import auth, item, me, search,comment,users

app = FastAPI()
app.include_router(auth.router)
app.include_router(item.router)
app.include_router(search.router)
app.include_router(me.router)
app.include_router(comment.router)
app.include_router(users.router)