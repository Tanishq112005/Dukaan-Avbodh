import os
import sys
import asyncio
from unittest.mock import patch, AsyncMock

# Ensure backend directory is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from starlette.testclient import TestClient
from services.health_service import health_service, HealthService
from main import app

client = TestClient(app, raise_server_exceptions=False)


def test_system_metrics():
    """Verifies system metrics collection."""
    metrics = health_service.get_system_metrics()
    assert "platform" in metrics
    assert "python_version" in metrics
    assert "pid" in metrics
    assert "threads_count" in metrics
    assert "uptime_seconds" in metrics
    assert "uptime_human" in metrics
    assert metrics["uptime_seconds"] >= 0
    print("[PASS] test_system_metrics passed")


def test_format_uptime():
    """Verifies uptime formatting across second, minute, and hour boundaries."""
    svc = HealthService()
    svc.start_time = 1000.0

    with patch("time.time", return_value=1045.0):
        assert svc.format_uptime() == "45s"

    with patch("time.time", return_value=1125.0):
        assert svc.format_uptime() == "2m 5s"

    with patch("time.time", return_value=4725.0):
        assert svc.format_uptime() == "1h 2m 5s"

    print("[PASS] test_format_uptime passed")


def test_liveness_check():
    """Verifies instant liveness probe."""
    live = health_service.get_liveness()
    assert live["status"] == "healthy"
    assert "uptime_seconds" in live
    assert "timestamp" in live

    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
    print("[PASS] test_liveness_check passed")


def test_html_website_endpoint():
    """Verifies GET /health returns responsive HTML website for browser requests."""
    resp = client.get("/health", headers={"Accept": "text/html,application/xhtml+xml"})
    assert resp.headers["content-type"].startswith("text/html")
    assert "Dukaan Server Health" in resp.text
    assert "Subsystems &amp; Data Stores" in resp.text
    assert "PostgreSQL" in resp.text
    assert "Redis Cache" in resp.text
    assert "MongoDB NoSQL" in resp.text
    assert "RabbitMQ Broker" in resp.text
    assert "autoRefreshSelect" in resp.text
    print("[PASS] test_html_website_endpoint passed")


def test_json_health_endpoint():
    """Verifies GET /health?format=json returns valid diagnostic JSON."""
    resp = client.get("/health?format=json")
    assert resp.status_code in (200, 503)
    data = resp.json()

    assert "status" in data
    assert data["status"] in ("healthy", "degraded", "unhealthy")
    assert "timestamp" in data
    assert "system" in data
    assert "services" in data

    services = data["services"]
    assert "postgresql" in services
    assert "redis" in services
    assert "mongodb" in services
    assert "rabbitmq" in services
    assert "agents" in services
    print("[PASS] test_json_health_endpoint passed")


def test_api_health_endpoint():
    """Verifies GET /api/health returns valid JSON."""
    resp = client.get("/api/health")
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data
    assert "services" in data
    print("[PASS] test_api_health_endpoint passed")


def test_ready_endpoint():
    """Verifies GET /health/ready endpoint structure."""
    resp = client.get("/health/ready")
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data
    assert data["status"] in ("ready", "not_ready")
    assert "checks" in data
    assert "postgresql" in data["checks"]
    assert "redis" in data["checks"]
    print("[PASS] test_ready_endpoint passed")


async def async_mock_checks_healthy():
    """Verifies status computation when all services are healthy."""
    with patch.object(
        health_service, "check_postgres", new_callable=AsyncMock
    ) as mock_pg, patch.object(
        health_service, "check_redis", new_callable=AsyncMock
    ) as mock_rd, patch.object(
        health_service, "check_mongodb", new_callable=AsyncMock
    ) as mock_mg, patch.object(
        health_service, "check_rabbitmq", new_callable=AsyncMock
    ) as mock_rb:

        mock_pg.return_value = {"status": "healthy", "latency_ms": 1.2}
        mock_rd.return_value = {"status": "healthy", "latency_ms": 0.5}
        mock_mg.return_value = {"status": "healthy", "latency_ms": 2.0}
        mock_rb.return_value = {"status": "healthy", "latency_ms": 3.1}

        res = await health_service.get_full_health()
        assert res["status"] == "healthy"
        print("[PASS] async_mock_checks_healthy passed")


async def async_mock_checks_degraded():
    """Verifies status computation when non-critical service is degraded."""
    with patch.object(
        health_service, "check_postgres", new_callable=AsyncMock
    ) as mock_pg, patch.object(
        health_service, "check_redis", new_callable=AsyncMock
    ) as mock_rd, patch.object(
        health_service, "check_mongodb", new_callable=AsyncMock
    ) as mock_mg, patch.object(
        health_service, "check_rabbitmq", new_callable=AsyncMock
    ) as mock_rb:

        mock_pg.return_value = {"status": "healthy", "latency_ms": 1.2}
        mock_rd.return_value = {"status": "healthy", "latency_ms": 0.5}
        mock_mg.return_value = {"status": "unhealthy", "error": "connection failed"}
        mock_rb.return_value = {"status": "degraded", "error": "offline"}

        res = await health_service.get_full_health()
        assert res["status"] == "degraded"
        print("[PASS] async_mock_checks_degraded passed")


def run_all_tests():
    print("=" * 60)
    print("RUNNING HEALTH SERVICE & DASHBOARD SUITE")
    print("=" * 60)
    test_system_metrics()
    test_format_uptime()
    test_liveness_check()
    test_html_website_endpoint()
    test_json_health_endpoint()
    test_api_health_endpoint()
    test_ready_endpoint()
    asyncio.run(async_mock_checks_healthy())
    asyncio.run(async_mock_checks_degraded())
    print("=" * 60)
    print("ALL HEALTH MONITORING TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
