import shutil
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

    service = WarehouseSyncService(source_dir=source_dir, target_dir=target_dir)
    result = service.sync_market(mode="copy")

    assert result.success is True
    assert result.local_db is not None
    assert source_db.exists()
    assert result.local_db.endswith("tw_stock_warehouse.db")
    shutil.rmtree(base, ignore_errors=True)
