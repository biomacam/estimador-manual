from fastapi import FastAPI

from app.routers import estimations

app = FastAPI(
    title="Estimador Manual",
    description=(
        "AI-powered software estimation service that generates project estimations "
        "from meeting transcriptions using a Cache Augmented Generation (CAG) architecture."
    ),
)
app.include_router(estimations.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
