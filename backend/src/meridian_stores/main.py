import uvicorn

from meridian_stores.settings import settings


def run() -> None:
    uvicorn.run(
        "hello_world.app:app",
        host=settings.api_host,
        port=settings.api_port,
        factory=False,
    )


if __name__ == "__main__":
    run()
