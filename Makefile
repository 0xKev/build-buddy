.PHONY: run docker-run

run:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker build -t build-buddy .

docker-run:
	docker run -p 8000:8000 --env-file .env build-buddy

