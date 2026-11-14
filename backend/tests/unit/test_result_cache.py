"""Deterministic TTL, FIFO, mutation and concurrency checks; synthetic results."""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.errors import APIError
from app.services.result_cache import ResultCache
from tests.unit.analysis_fixtures import make_case
from tests.unit.test_analysis_service import service


@pytest.fixture
def result(tmp_path):
    from app.schemas.analysis import AnalysisRequest

    case = make_case(tmp_path)
    return service(case).analyze(AnalysisRequest(**case.request))


def clone(result):
    return result.model_copy(deep=True, update={"analysis_id": uuid4()})


def test_monotonic_expiry_boundary_and_no_sliding_reads(result):
    now = [10.0]
    cache = ResultCache(ttl_seconds=20, clock=lambda: now[0])
    cache.put_many((result,))
    now[0] = 29.999
    assert cache.get(result.analysis_id) == result
    now[0] = 30
    with pytest.raises(APIError) as exc:
        cache.get(result.analysis_id)
    assert (exc.value.status_code, exc.value.code) == (404, "NOT_FOUND")
    assert len(cache) == 0


def test_fifo_capacity_and_expiration_reclaimed(result):
    now = [0]
    cache = ResultCache(ttl_seconds=10, max_entries=2, clock=lambda: now[0])
    second, third = clone(result), clone(result)
    cache.put_many((result, second))
    cache.get(result.analysis_id)  # Reading must not change FIFO eviction order.
    cache.put_many((third,))
    with pytest.raises(APIError):
        cache.get(result.analysis_id)
    assert cache.get(second.analysis_id) == second
    now[0] = 10
    cache.put_many((result,))
    assert len(cache) == 1


def test_cache_copies_both_inserted_and_returned_objects(result):
    original = result.model_dump(mode="json")
    cache = ResultCache()
    cache.put_many((result,))
    result.warnings.append("mutated source")
    retrieved = cache.get(result.analysis_id)
    assert retrieved.model_dump(mode="json") == original
    retrieved.monthly.clear()
    retrieved.warnings.append("mutated reader")
    assert cache.get(result.analysis_id).model_dump(mode="json") == original


def test_invalid_batches_do_not_mutate_cache(result):
    cache = ResultCache(max_entries=2)
    cache.put_many((result,))
    bad = clone(result)
    bad.monthly[0].__dict__["precipitation_total_mm"] = float("nan")
    for batch in (
        (clone(result), bad),
        (result, result),
        (),
        (clone(result), clone(result), clone(result)),
    ):
        with pytest.raises(ValueError):
            cache.put_many(batch)
        assert len(cache) == 1
        assert cache.get(result.analysis_id) == result


def test_entry_and_total_byte_bounds(result, monkeypatch):
    import app.services.result_cache as module

    size = len(result.model_dump_json().encode())
    cache = ResultCache()
    monkeypatch.setattr(module, "MAX_ENTRY_BYTES", size - 1)
    with pytest.raises(ValueError):
        cache.put_many((result,))
    assert len(cache) == 0
    monkeypatch.setattr(module, "MAX_ENTRY_BYTES", size * 2)
    monkeypatch.setattr(module, "MAX_CACHE_BYTES", size * 2 + 2)
    second, third = clone(result), clone(result)
    cache.put_many((result, second))
    cache.put_many((third,))
    assert len(cache) == 2
    with pytest.raises(APIError):
        cache.get(result.analysis_id)
    with pytest.raises(ValueError):
        cache.put_many((result, second, third))
    assert len(cache) == 2


def test_concurrent_writes_and_reads_are_safe(result):
    cache = ResultCache(max_entries=100)
    batches = [(clone(result), clone(result)) for _ in range(20)]

    def publish(batch):
        cache.put_many(batch)
        for item in batch:
            assert cache.get(item.analysis_id) == item

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(publish, batches))
    assert len(cache) == 40


@pytest.mark.parametrize(
    "ttl,capacity",
    [(0, 100), (86401, 100), (True, 100), (10, 0), (10, 1), (10, 1001), (10, True)],
)
def test_invalid_cache_configuration(ttl, capacity):
    with pytest.raises(ValueError):
        ResultCache(ttl_seconds=ttl, max_entries=capacity)


def test_settings_cache_environment_and_bounds(monkeypatch):
    monkeypatch.setenv("RESULT_CACHE_TTL_SECONDS", "30")
    monkeypatch.setenv("RESULT_CACHE_MAX_ENTRIES", "2")
    settings = Settings.from_env()
    assert settings.result_cache_ttl_seconds == 30
    assert settings.result_cache_max_entries == 2
    for values in (
        {"result_cache_ttl_seconds": 0},
        {"result_cache_max_entries": 1},
        {"result_cache_max_entries": 1001},
    ):
        with pytest.raises(ValueError):
            Settings(**values)
