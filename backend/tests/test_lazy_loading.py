import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from services.crop_service import CropService, crop_service
from services.fertilizer_service import FertilizerService, fertilizer_service
from services.lazy_resource import LazyResource, ResourceLoadError
from services.season_service import SeasonService, season_service
from services.soil_service import SoilService, soil_service


def test_service_construction_does_not_load_resources():
    services = (
        SoilService(),
        CropService(),
        FertilizerService(),
        SeasonService(),
    )

    assert [service.initialization_status["status"] for service in services] == [
        "not_loaded",
        "not_loaded",
        "not_loaded",
        "not_loaded",
    ]


def test_health_does_not_initialize_services():
    services = (
        soil_service,
        crop_service,
        fertilizer_service,
        season_service,
    )
    before = [service.initialization_status for service in services]

    response = app.test_client().get("/api/health")
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "online"
    assert data["initialization"] == {
        key: state["status"]
        for key, state in zip(
            ("soil_model", "crop_disease_model", "fertilizer_model", "crop_season_dataset"),
            before,
        )
    }
    assert [service.initialization_status for service in services] == before


def test_lazy_resource_loads_once_for_concurrent_requests():
    resource = LazyResource("test resource")
    call_lock = Lock()
    calls = 0

    def loader():
        nonlocal calls
        with call_lock:
            calls += 1
        time.sleep(0.02)
        return object()

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: resource.get(loader), range(16)))

    assert calls == 1
    assert all(result is results[0] for result in results)
    assert resource.status == {"status": "loaded"}


def test_lazy_resource_reports_failure_without_reloading():
    resource = LazyResource("test resource")
    calls = 0

    def loader():
        nonlocal calls
        calls += 1
        raise FileNotFoundError("weights file missing")

    with pytest.raises(ResourceLoadError, match="weights file missing"):
        resource.get(loader)
    with pytest.raises(ResourceLoadError, match="weights file missing"):
        resource.get(loader)

    assert calls == 1
    assert resource.status["status"] == "failed"
