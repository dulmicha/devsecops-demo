# DevSecOps demo

[English](README.md) / [Polski](README.pl.md)

---

A FastAPI microservice for managing security vulnerability findings, built with a Shift-Left CI/CD pipeline, automated container delivery, structured JSON logging with correlation IDs, and a local Grafana + Loki observability stack.

---

## 1. How to Run the Application

The entire ecosystem (FastAPI application, Loki log store, Promtail log scraper, and Grafana dashboard) runs locally via Docker Compose.

### Quickstart

```bash
# Start all services
docker compose up --build -d

# View live logs in console
docker compose logs -f app
```

### Accessing Endpoints & Services

* **API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Diagnostic Probe:** [http://localhost:8000/health](http://localhost:8000/health)
* **Grafana Observability Dashboard:** [http://localhost:3000](http://localhost:3000)
  * Pre-configured with live application log streams, log rate charts, and HTTP method/status code filters. Default credentials: `admin` / `admin`.

### Local Development & Testing

```bash
# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run test suite with coverage enforcement
pytest

# Run pre-commit checks locally
pre-commit run --all-files
```

### Stopping the Stack

```bash
docker compose down
```

---

## 2. Tool Selection & Rationale

### Application & Runtime
* **FastAPI & Uvicorn:** Chosen for high async throughput, strict type safety via Pydantic, and automatic OpenAPI schema generation. The service uses an in-memory dictionary pre-seeded with 2,500 realistic findings on startup, providing pagination and multi-field filtering without external database overhead.
* **Debian-Slim Dockerfile:** Uses multi-stage builds (`python:3.12-slim-bookworm`), runs as an unprivileged user (`appuser:10001:10001`), prunes build-time tools (`setuptools`, `pip`, `wheel`) from the runtime image to eliminate attack surface, and implements native container health checks.

### Shift-Left Security Scanners
* **Ruff (Linting & Formatting):** Replaces Black, Flake8, and isort with a single Rust tool. Configured both as a local pre-commit hook and in CI to enforce consistent code standards before execution.
* **Gitleaks (Secret Detection):** Prevents hardcoded API tokens, credentials, and private keys from entering version control. Runs client-side on git commit and server-side in CI.
* **Bandit (SAST):** Static Application Security Testing tool analyzing Python AST for insecure coding practices (e.g., `subprocess` with `shell=True`, unsafe `eval`, weak crypto).
* **pip-audit (SCA):** Software Composition Analysis auditing dependencies against the Open Source Vulnerabilities database to catch known CVEs before deployment.
* **Trivy (Container Security):** Scans the Dockerfile for configuration defects and the final built image for OS and package vulnerabilities.

### Telemetry & Observability
* **python-json-logger & Context Middleware:** Emits structured JSON logs to `stdout`. An asynchronous correlation middleware extracts or generates a unique `X-Request-ID` per request and binds it to Python `contextvars`, ensuring every log entry is traceable across async operations.
* **Grafana + Loki + Promtail:** Promtail captures container logs from Docker, extracts structured fields (`status_code`, `http_method`, `request_id`), and ships them to Loki. An auto-provisioned Grafana dashboard provides real-time log search, method gauges, and stats breakdown out of the box without manual query setup.

### CI/CD - Quality Gate & Continuous Delivery
* **GitHub Actions Quality Gate (`ci.yml`):** Runs all scanners (Ruff, Gitleaks, Bandit, pip-audit, Pytest coverage, Trivy) in parallel on every pull request. An aggregate `quality-gate` job evaluates all checks and blocks merging if any scanner fails. There must be a PR to merge to main, which enforces compliance.
* **Automated CD Pipeline (`cd.yml`):** Automatically builds and publishes container images to the GitHub Container Registry **only** upon successful Quality Gate completion on `main` (`:latest`, `:<sha>`) or when pushing semantic version tags (`:v0.1.0`).

---

## 3. Production Hardening & Long-Term Roadmap

For an enterprise production deployment, the following enhancements would be planned:

1. **Persistent Database & Migrations:**
   * Replace the in-memory data store with PostgreSQL using SQLAlchemy and Alembic for schema migrations.
2. **Authentication & Role-Based Access Control:**
   * Integrate authentication (e.g. OAuth2) to protect endpoints and enforce granular roles.
3. **Supply Chain Security:**
   * Generate **SLSA Level 3 build provenance** attestations and attach SPDX SBOMs to published images in GHCR during CD.
4. **Metrics Export:**
   * Expose Prometheus metrics (`/metrics`) to monitor request latency percentiles (p95/p99) and error rates.
5. **Elaborated protection rules**
   * Extend branch protection rules for secure team development by adding required number of approvers, CODEOWNERS.

---

## 4. Demonstration Pull Requests

* **[PR #2 (Green Gate):](https://github.com/dulmicha/devsecops-demo/pull/2)** Introduces safe `/api/v1/findings/metrics/summary` implementation with unit tests. All 6 scanners pass, so the **Quality Gate PASSED** and it's free to merge.
* **[PR #3 (Blocked Gate):](https://github.com/dulmicha/devsecops-demo/pull/3)** Introduces intentional flaws (hardcoded secret, shell injection, vulnerable dependency). **Quality Gate FAILED**, and merge button is blocked by GitHub Branch Protection.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
