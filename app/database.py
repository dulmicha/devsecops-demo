import random
import uuid
from datetime import UTC, datetime

from app.models import FindingCreate, FindingResponse, FindingUpdate, Severity, Status


class InMemoryFindingStore:
    """In-memory data store for Security Findings with seed generation."""

    def __init__(self) -> None:
        self._store: dict[str, FindingResponse] = {}
        self._ordered_ids: list[str] = []

    def seed(self, count: int = 2500) -> None:
        """Preload synthetic findings."""
        if self._store:
            return

        rng = random.Random(42)
        assets = [
            "payment-service",
            "auth-api",
            "user-portal",
            "db-primary",
            "db-replica-01",
            "ingress-gateway",
            "redis-cache",
            "notification-worker",
            "billing-service",
            "vault-cluster",
            "k8s-control-plane",
            "analytics-pipeline",
        ]
        titles = [
            "Outdated OpenSSL cryptographic library",
            "Missing Content-Security-Policy header",
            "Insecure direct object reference (IDOR)",
            "Unrestricted CORS wildcard configuration",
            "Missing rate limiting on authentication endpoint",
            "Weak TLS 1.0/1.1 cipher suite enabled",
            "Exposed debugging endpoint in production",
            "SQL injection risk in legacy search filter",
            "Hardcoded default secret key detected",
            "Remote code execution via unsafe deserialization",
            "Privilege escalation risk in background daemon",
            "Server-side request forgery (SSRF) in webhook handler",
        ]
        severities = list(Severity)
        statuses = list(Status)

        now = datetime.now(UTC)

        for i in range(count):
            finding_id = str(uuid.uuid4())
            cve_year = rng.randint(2021, 2024)
            cve_num = rng.randint(1000, 99999)
            cve_id = f"CVE-{cve_year}-{cve_num}" if rng.random() > 0.15 else None
            title = f"{rng.choice(titles)} [Sample #{i + 1}]"
            asset = rng.choice(assets)
            severity = rng.choice(severities)
            status = rng.choice(statuses)

            finding = FindingResponse(
                id=finding_id,
                title=title,
                severity=severity,
                asset_name=asset,
                cve_id=cve_id,
                status=status,
                description=f"Automated finding detected on asset {asset}. Requires review and triage.",
                created_at=now,
                updated_at=now,
            )
            self._store[finding_id] = finding
            self._ordered_ids.append(finding_id)

    def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
        severity: Severity | None = None,
        status: Status | None = None,
        search: str | None = None,
    ) -> tuple[list[FindingResponse], int]:
        """Fetch paginated findings with optional filtering."""
        # Not filters applied
        if severity is None and status is None and not search:
            total = len(self._ordered_ids)
            page_ids = self._ordered_ids[offset : offset + limit]
            return [self._store[item_id] for item_id in page_ids], total

        # Filtered path
        filtered = []
        search_lower = search.lower() if search else None

        for item_id in self._ordered_ids:
            item = self._store.get(item_id)
            if not item:
                continue
            if severity and item.severity != severity:
                continue
            if status and item.status != status:
                continue
            if search_lower and (
                search_lower not in item.title.lower()
                and search_lower not in item.asset_name.lower()
                and (not item.cve_id or search_lower not in item.cve_id.lower())
            ):
                continue
            filtered.append(item)

        total = len(filtered)
        return filtered[offset : offset + limit], total

    def get_by_id(self, finding_id: str) -> FindingResponse | None:
        """Retrieve a finding by its unique ID."""
        return self._store.get(finding_id)

    def create(self, data: FindingCreate) -> FindingResponse:
        """Create and store a new security finding."""
        finding_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        finding = FindingResponse(
            id=finding_id,
            title=data.title,
            severity=data.severity,
            asset_name=data.asset_name,
            cve_id=data.cve_id,
            status=data.status,
            description=data.description or "",
            created_at=now,
            updated_at=now,
        )
        self._store[finding_id] = finding
        self._ordered_ids.insert(0, finding_id)  # newest first
        return finding

    def update(self, finding_id: str, data: FindingUpdate) -> FindingResponse | None:
        """Update an existing finding with provided fields."""
        existing = self._store.get(finding_id)
        if not existing:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            return existing

        current_dict = existing.model_dump()
        current_dict.update(update_dict)
        current_dict["updated_at"] = datetime.now(UTC)

        updated = FindingResponse(**current_dict)
        self._store[finding_id] = updated
        return updated

    def delete(self, finding_id: str) -> bool:
        """Delete a finding from the store."""
        if finding_id in self._store:
            del self._store[finding_id]
            if finding_id in self._ordered_ids:
                self._ordered_ids.remove(finding_id)
            return True
        return False

    def count(self) -> int:
        """Return total number of stored findings."""
        return len(self._store)

    def clear(self) -> None:
        """Clear all stored data (useful for test isolation)."""
        self._store.clear()
        self._ordered_ids.clear()


# Global database instance
db = InMemoryFindingStore()
