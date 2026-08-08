"""Unit tests for CPU %, memory %, and network rate calculations in DockerMetricsProvider."""
from __future__ import annotations

from app.services.observability.docker_metrics import (
    calculate_block_io_bytes,
    calculate_cpu_percent,
    calculate_memory_metrics,
    calculate_network_bytes,
)


def test_calculate_cpu_percent_normal():
    stats = {
        "cpu_stats": {
            "cpu_usage": {"total_usage": 2000000000},
            "system_cpu_usage": 10000000000,
            "online_cpus": 2,
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": 1000000000},
            "system_cpu_usage": 5000000000,
        },
    }
    # cpu_delta = 1000000000, sys_delta = 5000000000, ratio = 0.2, cpus = 2 -> 40.0%
    cpu_pct = calculate_cpu_percent(stats)
    assert cpu_pct == 40.0


def test_calculate_cpu_percent_zero_delta():
    stats = {
        "cpu_stats": {"cpu_usage": {"total_usage": 100}, "system_cpu_usage": 100},
        "precpu_stats": {"cpu_usage": {"total_usage": 100}, "system_cpu_usage": 100},
    }
    assert calculate_cpu_percent(stats) == 0.0


def test_calculate_memory_metrics():
    stats = {
        "memory_stats": {
            "usage": 200 * 1024 * 1024,
            "limit": 512 * 1024 * 1024,
            "stats": {"cache": 10 * 1024 * 1024},
        }
    }
    # rss = 190 MB, limit = 512 MB, pct ~37.11%
    rss, limit, pct = calculate_memory_metrics(stats)
    assert rss == 190 * 1024 * 1024
    assert limit == 512 * 1024 * 1024
    assert 36.0 < pct < 38.0


def test_calculate_network_bytes():
    stats = {
        "networks": {
            "eth0": {"rx_bytes": 1000, "tx_bytes": 500},
            "eth1": {"rx_bytes": 2000, "tx_bytes": 1000},
        }
    }
    rx, tx = calculate_network_bytes(stats)
    assert rx == 3000
    assert tx == 1500


def test_calculate_block_io_bytes():
    stats = {
        "blkio_stats": {
            "io_service_bytes_recursive": [
                {"op": "Read", "value": 4096},
                {"op": "Write", "value": 8192},
            ]
        }
    }
    r, w = calculate_block_io_bytes(stats)
    assert r == 4096
    assert w == 8192
