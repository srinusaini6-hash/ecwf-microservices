from fastapi import FastAPI

app = FastAPI(
    title="Notification Service",
    description="Notification Service for Enterprise Collaboration Workflow",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Notification Service is ready"
    }