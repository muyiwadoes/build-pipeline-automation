from flask import Flask

app = Flask(__name__)


@app.get("/")
def health():
    return {"status": "ok", "service": "pipeline-service"}


@app.get("/run")
def run_pipeline():
    return {"message": "Pipeline trigger endpoint (replace with real logic if needed)"}


def main():
    # IMPORTANT: bind to 0.0.0.0 so ECS/ALB can reach it
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
