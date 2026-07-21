from fastapi import FastAPI

app = FastAPI(
    title="Identity Authentication Service"
)

@app.get("/")
def home():
    return {"message": "Service Ready"}