"""Validate security/port/mount invariants in rendered default Compose variants."""

import json
import os
import subprocess
from pathlib import Path


def check_compose() -> None:
    root = Path(__file__).resolve().parents[1]
    environment = dict(os.environ)
    # Test only the committed examples, never print or inspect operator approvals.
    for line in (root / ".env.example").read_text().splitlines():
        if line and not line.startswith("#"):
            environment.pop(line.split("=", 1)[0], None)
    for mode in ("production", "development"):
        command = [
            "docker",
            "compose",
            "--env-file",
            ".env.example",
            "-f",
            "compose.yaml",
        ]
        if mode == "development":
            command.extend(["-f", "compose.dev.yaml"])
        rendered = subprocess.check_output(
            [*command, "config", "--format", "json"],
            cwd=root,
            env=environment,
            text=True,
        )
        services = json.loads(rendered)["services"]
        assert set(services) == {"backend", "frontend"}, "unexpected service/database"
        for service in services.values():
            assert service["build"]["target"] == mode
            assert "ALL" in service["cap_drop"]
            assert any(
                v.startswith("no-new-privileges") for v in service["security_opt"]
            )
            assert all(port["host_ip"] == "127.0.0.1" for port in service["ports"])
        backend, frontend = services["backend"], services["frontend"]
        assert backend["read_only"] is True
        assert backend["environment"]["APP_ENV"] == mode
        assert json.loads(backend["environment"]["SNAPSHOT_APPROVALS"]) == []
        assert json.loads(backend["environment"]["SNAPSHOT_QUALITY_POLICIES"]) == []
        assert any(
            v["target"] == "/data/demo" and v["read_only"] for v in backend["volumes"]
        )
        assert frontend["depends_on"]["backend"]["condition"] == "service_healthy"
        frontend_port = 8080 if mode == "production" else 5173
        assert [p["target"] for p in frontend["ports"]] == [frontend_port]
        if mode == "production":
            assert frontend["read_only"] is True
            assert all(v["read_only"] for v in frontend["volumes"])
            assert all(v["target"] != "/app/app" for v in backend["volumes"])
        else:
            assert any(
                v["target"] == "/app/app" and v["read_only"] for v in backend["volumes"]
            )
            assert {v["target"] for v in frontend["volumes"]} == {
                "/app/src",
                "/app/public",
            }
        print(f"PASS {mode} Compose security, mounts, ports and empty review defaults")


if __name__ == "__main__":
    check_compose()
