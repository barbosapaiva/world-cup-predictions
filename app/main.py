from fastapi import FastAPI

app = FastAPI(
    title="World Cup Predictions API",
    version="0.1.0",
)


@app.get("/")
def health_check():
    return {"status": "ok"}