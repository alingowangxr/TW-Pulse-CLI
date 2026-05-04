import shutil
import subprocess
from pathlib import Path
from uuid import uuid4


def test_warehouse_sync_copy_mode():
    from pulse.core.data.warehouse_sync import WarehouseSyncService

    base = Path(__file__).resolve().parent / f"_warehouse_tmp_{uuid4().hex}"
    source_dir = base / "warehouse"
    target_dir = base / "local"
    source_dir.mkdir(parents=True)
    target_dir.mkdir(parents=True)

    source_db = source_dir / "tw_stock_warehouse.db"
    source_db.write_bytes(b"sqlite-placeholder")
    (source_dir / "downloader_tw.py").write_text("print('downloader ok')", encoding="utf-8")

    service = WarehouseSyncService(source_dir=source_dir, target_dir=target_dir)
    result = service.sync_market(mode="copy")

    assert result.success is True
    assert result.local_db is not None
    assert source_db.exists()
    assert result.local_db.endswith("tw_stock_warehouse.db")
    shutil.rmtree(base, ignore_errors=True)


def test_warehouse_sync_run_mode_invokes_downloader(monkeypatch):
    from pulse.core.data.warehouse_sync import WarehouseSyncService

    base = Path(__file__).resolve().parent / f"_warehouse_tmp_{uuid4().hex}"
    source_dir = base / "warehouse"
    target_dir = base / "local"
    source_dir.mkdir(parents=True)
    target_dir.mkdir(parents=True)

    source_db = source_dir / "tw_stock_warehouse.db"
    source_db.write_bytes(b"sqlite-placeholder")
    (source_dir / "downloader_tw.py").write_text("print('downloader ok')", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_run(cmd, cwd=None, capture_output=None, text=None, check=None):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=0,
            stdout="downloader ok",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    service = WarehouseSyncService(source_dir=source_dir, target_dir=target_dir)
    result = service.sync_market(mode="run")

    assert result.success is True
    assert result.ran_downloader is True
    assert captured["cwd"] == str(source_dir)
    assert captured["cmd"][0].endswith("python.exe") or captured["cmd"][0].endswith("python")
    assert captured["cmd"][1].endswith("downloader_tw.py")
    assert captured["cmd"][2:4] == ["--mode", "full"]
    shutil.rmtree(base, ignore_errors=True)
