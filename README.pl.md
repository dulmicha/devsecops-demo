# DevSecOps demo

[English](README.md) / [Polski](README.pl.md)

---

Mikroserwis oparty na frameworku FastAPI, służący do zarządzania podatnościami bezpieczeństwa (security findings). Zbudowany z wykorzystaniem pipeline CI/CD w podejściu Shift-Left, zautomatyzowanego wdrażania kontenerów, strukturyzowanego logowania JSON z identyfikatorami korelacji oraz lokalnego stosu observability opartego na Grafanie i Loki.

---

## 1. Jak uruchomić aplikację

Cały ekosystem (aplikacja FastAPI, baza logów Loki, scraper logów Promtail oraz dashboard Grafany) uruchamia się lokalnie za pomocą Docker Compose.

### Szybki start

```bash
# Uruchomienie wszystkich serwisów w tle
docker compose up --build -d

# Podgląd logów aplikacji na żywo w konsoli
docker compose logs -f app
```

### Dostęp do endpointów i serwisów

* Dokumentacja API (Swagger UI): http://localhost:8000/docs
* Endpoint diagnostyczny stanu usługi (Health Check): http://localhost:8000/health
* Dashboard Grafana: http://localhost:3000
  * Wstępnie skonfigurowany z widokiem logów na żywo, wykresami przepustowości (log rate) oraz filtrami metod HTTP i kodów odpowiedzi. Domyślne dane logowania: `admin` / `admin`.

### Lokalne środowisko deweloperskie i testy

```bash
# Konfiguracja środowiska wirtualnego Python
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Uruchomienie zestawu testów z wymogiem minimalnego pokrycia
pytest

# Uruchomienie lokalnych weryfikacji pre-commit
pre-commit run --all-files
```

### Zatrzymywanie środowiska

```bash
docker compose down
```

---

## 2. Dobór narzędzi i uzasadnienie architektoniczne

### Aplikacja i środowisko uruchomieniowe
* **FastAPI & Uvicorn**: Wybrane ze względu na wysoką przepustowość asynchroniczną, ścisłą kontrolę typów za pomocą Pydantic oraz automatyczne generowanie schematów OpenAPI. Usługa korzysta z pamięci podręcznej, która przy starcie jest inicjalizowana 2500 realistycznymi rekordami podatności, zapewniając paginację i zaawansowane filtrowanie bez konieczności stawiania zewnętrznej bazy danych.
* **Dockerfile oparty na Debian-Slim**: Wykorzystuje wieloetapowe budowanie (multi-stage build na bazie `python:3.12-slim-bookworm`), działa jako użytkownik bez uprawnień roota (`appuser:10001:10001`), usuwa narzędzia budowania (`setuptools`, `pip`, `wheel`) z końcowego obrazu w celu zminimalizowania powierzchni ataku oraz posiada natywną definicję HEALTHCHECK.

### Skanery bezpieczeństwa (Shift-Left Security)
* **Ruff (Linting i formatowanie)**: Zastępuje Black, Flake8 oraz isort pojedynczym, szybkim narzędziem napisanym w Rust. Skonfigurowany zarówno jako lokalny hook pre-commit, jak i krok w CI do wymuszania spójnych standardów kodu.
* **Gitleaks (Wykrywanie sekretów)**: Zapobiega przypadkowemu umieszczaniu w repozytorium kluczy API, danych logowania i kluczy prywatnych. Działa po stronie klienta przy operacji git commit oraz po stronie serwera w pipeline CI.
* **Bandit (SAST)**: Statyczna analiza kodu pod kątem bezpieczeństwa, badająca AST Pythona w poszukiwaniu niebezpiecznych praktyk programistycznych (np. `subprocess` z `shell=True`, niebezpieczne wywołania `eval`, słaba kryptografia).
* **pip-audit (SCA)**: Analiza składników oprogramowania weryfikująca zależności względem bazy Open Source Vulnerabilities w celu wychwycenia znanych podatności CVE przed wdrożeniem.
* **Trivy (Bezpieczeństwo kontenerów)**: Skanuje plik Dockerfile pod kątem błędów konfiguracyjnych oraz gotowy obraz kontenera pod kątem podatności w pakietach systemowych i bibliotekach.

### Telemetria i obserwowalność
* **python-json-logger i middleware kontekstowy**: Generuje ustrukturyzowane logi JSON na standardowe wyjście. Asynchroniczny middleware wyodrębnia lub generuje unikalny nagłówek `X-Request-ID` dla każdego żądania i wiąże go z `contextvars` w Pythonie, zapewniając pełną korelację logów w operacjach asynchronicznych.
* **Grafana + Loki + Promtail**: Promtail zbiera logi kontenera z Dockera, wyciąga kluczowe pola (`status_code`, `http_method`, `request_id`) i przesyła je do Loki. Automatycznie zainicjalizowany dashboard w Grafanie umożliwia wyszukiwanie logów w czasie rzeczywistym oraz podgląd statystyk ruchu od razu po starcie.

### CI/CD - Quality Gate i ciągłe dostarczanie
* **CI Quality Gate (`ci.yml`)**: Uruchamia równolegle wszystkie skanery (Ruff, Gitleaks, Bandit, pip-audit, Pytest z pokryciem kodu, Trivy) przy każdym Pull Requeście. Zbiorczy job `quality-gate` ewaluuje wyniki i blokuje możliwość scalenia zmian w przypadku niepowodzenia któregokolwiek ze skanerów. Zmiany w gałęzi main wymagają Pull Requesta, co wymusza przejście walidacji.
* **Automatyczny pipeline CD (`cd.yml`)**: Automatycznie buduje i publikuje obraz kontenera w GitHub Container Registry **wyłącznie** po poprawnym przejściu Quality Gate na gałęzi `main` (`:latest`, `:<sha>`) lub po opublikowaniu tagu wersji semantycznej (`:v0.1.0`).

---

## 3. Dostosowanie produkcyjne i dalszy rozwój

W przypadku wdrożenia produkcyjnego potrzebne byłyby następujące ulepszenia:

1. **Trwała baza danych i migracje**:
   * Zastąpienie mechanizmu in-memory relacyjną bazą danych PostgreSQL z wykorzystaniem biblioteki SQLAlchemy oraz Alembic do obsługi migracji schematów.
2. **Uwierzytelnianie i kontrola dostępu oparta na rolach**:
   * Integracja mechanizmu uwierzytelniania (np. OAuth2) w celu zabezpieczenia endpointów i wymuszenia szczegółowych uprawnień.
3. **Bezpieczeństwo łańcucha dostaw**:
   * Generowanie atestów pochodzenia kompilacji SLSA Level 3 oraz dołączanie zestawień komponentów SBOM (SPDX) do obrazów publikowanych w GHCR.
4. **Eksport metryk**:
   * Udostępnienie endpointu metryk Prometheus (/metrics) do monitorowania percentyli opóźnień żądań (p95/p99) oraz wskaźników błędów.
5. **Rozszerzone reguły ochrony gałęzi**:
   * Wdrożenie wymogu minimalnej liczby akceptacji Pull Requestów od wyznaczonych właścicieli kodu (CODEOWNERS).

---

## 4. Przykładowe Pull Requesty

* **[PR #2 (Zdany Quality Gate):](https://github.com/dulmicha/devsecops-demo/pull/2)** - Wprowadza poprawną implementację endpointu `/api/v1/findings/metrics/summary` wraz z testami jednostkowymi. Wszystkie 6 skanerów zakończyło się sukcesem (**Quality Gate PASSED**), umożliwiając scalenie kodu.
* **[PR #3 (Zablokowany Quality Gate)](https://github.com/dulmicha/devsecops-demo/pull/3)** - Wprowadza celowe błędy bezpieczeństwa (zahardkodowany sekret, podatność na shell injection, zależność ze znanym CVE). Skanery zgłaszają błędy (**Quality Gate FAILED**), a mechanizm GitHub Branch Protection blokuje możliwość scalenia zmian.

---

## Licencja

Licencja MIT. Szczegółowe informacje znajdują się w pliku [LICENSE](LICENSE).