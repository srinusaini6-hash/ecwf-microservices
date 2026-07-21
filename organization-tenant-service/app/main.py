from fastapi import FastAPI

app = FastAPI(
    title="Organization and Tenant Service",
    description="Organization and Tenant Management Microservice",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Organization and Tenant Service is ready"
    }