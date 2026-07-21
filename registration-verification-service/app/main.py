from fastapi import FastAPI

app = FastAPI(
    title="Registration and Verification Service",
    description="Registration and Verification Microservice",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Registration and Verification Service is ready"
    }