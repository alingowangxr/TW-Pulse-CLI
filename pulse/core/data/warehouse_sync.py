from __future__ import annotations

import asyncio
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pulse.core.config import settings
from pulse.core.data.local_warehouse import LocalWarehouseFetcher
from pulse.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class WarehouseSyncResult:
    """Result of syncing a local warehouse DB."""

    success: bool
    market: str
    mode: str
    source_dir: str | None = None
    source_db: str | None = None
    local_db: str | None = None
    copied: bool = False
    ran_downloader: bool = False
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


class WarehouseSyncService:
    """Synchronize the local warehouse DB from the current repository."""

    SUPPORTED_MARKETS = {"tw"}

    def __init__(
        self,
        source_dir: str | Path | None = None,
        target_dir: str | Path | None = None,
    ) -> None:
        self.source_dir = Path(source_dir) if source_dir else settings.base_dir
        self.target_dir = Path(target_dir) if target_dir else self._default_target_dir()

    def _default_target_dir(self) -> Path:
        return settings.base_dir / "data" / "local_warehouse"

    def _source_db_path(self, market: str) -> Path:
        return self.source_dir / f"{market}_stock_warehouse.db"

    def _local_db_path(self, market: str) -> Path:
        return self.target_dir / f"{market}_stock_warehouse.db"

    def _run_downloader(self, market: str) -> tuple[bool, str]:
        downloader_map = {
            "tw": "downloader_tw.py",
        }
        script_name = downloader_map.get(market)
        if not script_name:
            return False, f"market '{market}' is not supported"

        script_path = self.source_dir / script_name
        if not script_path.exists():
            return False, f"downloader script not found: {script_path}"

        try:
            downloader_mode = "full"
            completed = subprocess.run(
                [sys.executable, str(script_path), "--mode", downloader_mode],
                cwd=str(self.source_dir),
                capture_output=True,
                text=True,
                check=False,
            )
            output = "\n".join(
                part for part in [completed.stdout.strip(), completed.stderr.strip()] if part
            )
            if completed.returncode != 0:
                return False, output or f"downloader exited with code {completed.returncode}"
            return True, output
        except Exception as e:
            return False, str(e)

    async def _run_downloader_stream(self, market: str):
        downloader_map = {
            "tw": "downloader_tw.py",
        }
        script_name = downloader_map.get(market)
        if not script_name:
            yield {"type": "error", "message": f"market '{market}' is not supported"}
            return

        script_path = self.source_dir / script_name
        if not script_path.exists():
            yield {"type": "error", "message": f"downloader script not found: {script_path}"}
            return

        yield {"type": "progress", "message": f"開始執行 {script_name} (--mode full)..."}

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                "-u",
                str(script_path),
                "--mode",
                "full",
                cwd=str(self.source_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            assert proc.stdout is not None
            seen_messages: set[str] = set()
            buffer = ""

            while True:
                chunk = await proc.stdout.read(1024)
                if not chunk:
                    break

                text = chunk.decode("utf-8", errors="replace")
                buffer += text

                normalized = buffer.replace("\r\n", "\n")
                parts = normalized.split("\n")
                tail = parts[-1]

                for part in parts[:-1]:
                    message = part.replace("\r", "").strip()
                    if message and message not in seen_messages:
                        seen_messages.add(message)
                        yield {"type": "progress", "message": message}

                tail_message = tail.replace("\r", "").strip()
                if tail_message and tail_message not in seen_messages:
                    seen_messages.add(tail_message)
                    yield {"type": "progress", "message": tail_message}

            returncode = await proc.wait()

            if returncode != 0:
                yield {
                    "type": "error",
                    "message": f"{script_name} exited with code {returncode}",
                }
                return

            yield {"type": "progress", "message": f"{script_name} 完成，正在同步資料庫..."}
        except Exception as e:
            yield {"type": "error", "message": str(e)}

    def sync_market(
        self,
        market: str = "tw",
        mode: str = "copy",
    ) -> WarehouseSyncResult:
        market = market.lower().strip()
        mode = mode.lower().strip()

        if market not in self.SUPPORTED_MARKETS:
            return WarehouseSyncResult(
                success=False,
                market=market,
                mode=mode,
                message=f"unsupported market: {market}",
            )

        self.target_dir.mkdir(parents=True, exist_ok=True)
        local_db = self._local_db_path(market)
        source_db = self._source_db_path(market)

        ran_downloader = False
        downloader_output = ""
        if mode == "run":
            ran_downloader = True
            ok, output = self._run_downloader(market)
            downloader_output = output
            if not ok:
                return WarehouseSyncResult(
                    success=False,
                    market=market,
                    mode=mode,
                    source_dir=str(self.source_dir),
                    source_db=str(source_db),
                    local_db=str(local_db),
                    ran_downloader=True,
                    message=output,
                )

        if not source_db.exists():
            return WarehouseSyncResult(
                success=False,
                market=market,
                mode=mode,
                source_dir=str(self.source_dir),
                source_db=str(source_db),
                local_db=str(local_db),
                ran_downloader=ran_downloader,
                message="source warehouse database not found",
            )

        try:
            if source_db.resolve() != local_db.resolve():
                shutil.copy2(source_db, local_db)
            fetcher = LocalWarehouseFetcher(local_db)
            status = fetcher.get_status()
            status["downloader_output"] = downloader_output[-2000:] if downloader_output else ""
            return WarehouseSyncResult(
                success=True,
                market=market,
                mode=mode,
                source_dir=str(self.source_dir),
                source_db=str(source_db),
                local_db=str(local_db),
                copied=True,
                ran_downloader=ran_downloader,
                message="synced successfully",
                details=status,
            )
        except Exception as e:
            log.error(f"Warehouse sync failed: {e}")
            return WarehouseSyncResult(
                success=False,
                market=market,
                mode=mode,
                source_dir=str(self.source_dir),
                source_db=str(source_db),
                local_db=str(local_db),
                copied=False,
                ran_downloader=ran_downloader,
            message=str(e),
            )

    async def sync_market_stream(
        self,
        market: str = "tw",
        mode: str = "copy",
    ):
        market = market.lower().strip()
        mode = mode.lower().strip()

        if market not in self.SUPPORTED_MARKETS:
            yield {"type": "error", "message": f"unsupported market: {market}"}
            return

        self.target_dir.mkdir(parents=True, exist_ok=True)
        local_db = self._local_db_path(market)
        source_db = self._source_db_path(market)

        if mode == "run":
            async for event in self._run_downloader_stream(market):
                if event.get("type") == "error":
                    yield event
                    return
                yield event

        if not source_db.exists():
            yield {"type": "error", "message": "source warehouse database not found"}
            return

        try:
            if source_db.resolve() != local_db.resolve():
                shutil.copy2(source_db, local_db)
            fetcher = LocalWarehouseFetcher(local_db)
            status = fetcher.get_status()
            status["downloader_output"] = ""
            yield {
                "type": "response",
                "message": "倉庫同步完成",
                "result": {
                    "market": market,
                    "mode": mode,
                    "source_dir": str(self.source_dir),
                    "source_db": str(source_db),
                    "local_db": str(local_db),
                    "details": status,
                },
            }
        except Exception as e:
            log.error(f"Warehouse sync failed: {e}")
            yield {"type": "error", "message": str(e)}
