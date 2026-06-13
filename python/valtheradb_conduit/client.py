from __future__ import annotations

import subprocess
import threading
from concurrent.futures import Future
from pathlib import Path
from typing import Any

from .install import DEFAULT_INSTALL_DIR, ensure_binary
from .protocol import Frame, encode_frame, read_frame

INIT_DB = 1
EXECUTE_JSON = 2
CLOSE_DB = 3
LIST_DBS = 4
PING = 5
SHUTDOWN = 6

READY = 100
RESULT = 101
ERROR = 102
PONG = 104


class ValtheraConduitError(RuntimeError):
    def __init__(self, code: str, message: str, details: Any = None):
        super().__init__(message)
        self.code = code
        self.details = details


class ValtheraConduit:
    def __init__(
        self,
        install_dir: str | Path = DEFAULT_INSTALL_DIR,
        *,
        binary_path: str | Path | None = None,
        auto_download: bool = False,
        repository: str = "wxn0brP/ValtheraDB-conduit",
        version: str | None = None,
        cwd: str | Path | None = None,
    ):
        binary = Path(binary_path) if binary_path else ensure_binary(
            install_dir,
            auto_download=auto_download,
            repository=repository,
            version=version,
        )
        self._pending: dict[str, list[Future[Any]]] = {}
        self._db_locks: dict[str, threading.Lock] = {}
        self._write_lock = threading.Lock()
        self._process = subprocess.Popen(
            [str(binary)],
            cwd=str(cwd) if cwd else None,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        ready = read_frame(self._process.stdout)
        if ready.frame_type != READY:
            raise ValtheraConduitError("NOT_READY", "ValtheraDB Conduit did not send READY")
        self.ready = ready.payload.get("result", {})
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def db(self, name: str) -> ValtheraDbNamespace:
        return ValtheraDbNamespace(self, name)

    def init(self, name: str, directory: str | Path, opts: dict[str, Any] | None = None) -> ValtheraDb:
        return self.db(name).init(directory, opts)

    def __getattr__(self, name: str) -> ValtheraDbNamespace:
        if name.startswith("_"):
            raise AttributeError(name)
        return self.db(name)

    def open_db(self, name: str, directory: str | Path, options: dict[str, Any] | None = None) -> ValtheraDb:
        return self.init(name, directory, options)

    def close_db(self, name: str) -> Any:
        return self._request(name, CLOSE_DB, {})

    def list_dbs(self) -> list[str]:
        return self._request("", LIST_DBS, {})

    def ping(self) -> Any:
        return self._request("", PING, {})

    def execute(self, db: str, op: str, body: Any = None) -> Any:
        payload = {"op": op}
        if body is not None:
            payload["body"] = body
        return self._request(db, EXECUTE_JSON, payload)

    def shutdown(self) -> None:
        if self._process.poll() is None:
            try:
                self._request("", SHUTDOWN, {})
            finally:
                self._process.wait(timeout=5)

    def close(self) -> None:
        self.shutdown()

    def __enter__(self) -> "ValtheraConduit":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _request(self, db_name: str, frame_type: int, payload: dict[str, Any]) -> Any:
        if not self._process.stdin:
            raise ValtheraConduitError("CLOSED", "stdin is closed")

        lock = self._lock_for(db_name)
        with lock:
            future: Future[Any] = Future()
            self._pending.setdefault(db_name, []).append(future)
            data = encode_frame(frame_type, db_name, payload)
            with self._write_lock:
                self._process.stdin.write(data)
                self._process.stdin.flush()
            return future.result(timeout=30)

    def _lock_for(self, db_name: str) -> threading.Lock:
        if db_name not in self._db_locks:
            self._db_locks[db_name] = threading.Lock()
        return self._db_locks[db_name]

    def _read_loop(self) -> None:
        assert self._process.stdout is not None
        while self._process.poll() is None:
            try:
                frame = read_frame(self._process.stdout)
                self._resolve(frame)
            except Exception as exc:
                for queue in self._pending.values():
                    for future in queue:
                        if not future.done():
                            future.set_exception(exc)
                return

    def _resolve(self, frame: Frame) -> None:
        queue = self._pending.get(frame.db_name, [])
        future = queue.pop(0) if queue else None
        if future is None:
            return
        payload = frame.payload
        if frame.frame_type == ERROR or payload.get("ok") is False:
            future.set_exception(ValtheraConduitError(
                payload.get("code", "ERROR"),
                payload.get("message", "ValtheraDB Conduit error"),
                payload.get("details"),
            ))
            return
        future.set_result(payload.get("result"))


class ValtheraDbNamespace:
    def __init__(self, controller: ValtheraConduit, name: str):
        self.controller = controller
        self.name = name

    def init(self, directory: str | Path, opts: dict[str, Any] | None = None) -> "ValtheraDb":
        self.controller._request(self.name, INIT_DB, {"dir": str(directory), "opts": opts or {}})
        return ValtheraDb(self, self.name)


class ValtheraDb:
    def __init__(self, namespace: ValtheraDbNamespace, name: str):
        self.controller = namespace.controller
        self.name = name

    def execute(self, op: str, body: Any = None) -> Any:
        return self.controller.execute(self.name, op, body)

    def c(self, collection: str) -> "Collection":
        return Collection(self, collection)

    def collection(self, collection: str) -> "Collection":
        return self.c(collection)

    def __getattr__(self, collection: str) -> "Collection":
        if collection.startswith("_"):
            raise AttributeError(collection)
        return self.c(collection)

    def get_collections(self) -> list[str]:
        return self.execute("getCollections")

    def getCollections(self) -> list[str]:
        return self.get_collections()

    def ensure_collection(self, collection: str) -> bool:
        return self.execute("ensureCollection", collection)

    def ensureCollection(self, collection: str) -> bool:
        return self.ensure_collection(collection)

    def isset_collection(self, collection: str) -> bool:
        return self.execute("issetCollection", collection)

    def issetCollection(self, collection: str) -> bool:
        return self.isset_collection(collection)

    def remove_collection(self, collection: str) -> bool:
        return self.execute("removeCollection", collection)

    def removeCollection(self, collection: str) -> bool:
        return self.remove_collection(collection)

    def add(self, query: dict[str, Any]) -> Any:
        return self.execute("add", query)

    def find(self, query: dict[str, Any]) -> Any:
        return self.execute("find", query)

    def find_one(self, query: dict[str, Any]) -> Any:
        return self.execute("findOne", query)

    def findOne(self, query: dict[str, Any]) -> Any:
        return self.find_one(query)

    def update(self, query: dict[str, Any]) -> Any:
        return self.execute("update", query)

    def update_one(self, query: dict[str, Any]) -> Any:
        return self.execute("updateOne", query)

    def updateOne(self, query: dict[str, Any]) -> Any:
        return self.update_one(query)

    def remove(self, query: dict[str, Any]) -> Any:
        return self.execute("remove", query)

    def remove_one(self, query: dict[str, Any]) -> Any:
        return self.execute("removeOne", query)

    def removeOne(self, query: dict[str, Any]) -> Any:
        return self.remove_one(query)

    def update_one_or_add(self, query: dict[str, Any]) -> Any:
        return self.execute("updateOneOrAdd", query)

    def updateOneOrAdd(self, query: dict[str, Any]) -> Any:
        return self.update_one_or_add(query)

    def toggle_one(self, query: dict[str, Any]) -> Any:
        return self.execute("toggleOne", query)

    def toggleOne(self, query: dict[str, Any]) -> Any:
        return self.toggle_one(query)

    def close(self) -> Any:
        return self.controller.close_db(self.name)


class Collection:
    def __init__(self, db: ValtheraDb, name: str):
        self.db = db
        self.name = name

    def add(self, data: dict[str, Any], id_gen: bool = True) -> Any:
        return self.db.add({"collection": self.name, "data": data, "id_gen": id_gen})

    def find(
        self,
        search: dict[str, Any] | None = None,
        db_find_opts: dict[str, Any] | None = None,
        find_opts: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> Any:
        return self.db.find({
            "collection": self.name,
            "search": search or {},
            "dbFindOpts": db_find_opts or {},
            "findOpts": find_opts or {},
            "context": context or {},
        })

    def find_one(
        self,
        search: dict[str, Any] | None = None,
        find_opts: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> Any:
        return self.db.find_one({
            "collection": self.name,
            "search": search or {},
            "findOpts": find_opts or {},
            "context": context or {},
        })

    def findOne(self, *args: Any, **kwargs: Any) -> Any:
        return self.find_one(*args, **kwargs)

    def update(self, search: dict[str, Any], updater: dict[str, Any], context: dict[str, Any] | None = None) -> Any:
        return self.db.update({"collection": self.name, "search": search, "updater": updater, "context": context or {}})

    def update_one(self, search: dict[str, Any], updater: dict[str, Any], context: dict[str, Any] | None = None) -> Any:
        return self.db.update_one({"collection": self.name, "search": search, "updater": updater, "context": context or {}})

    def updateOne(self, *args: Any, **kwargs: Any) -> Any:
        return self.update_one(*args, **kwargs)

    def remove(self, search: dict[str, Any], context: dict[str, Any] | None = None) -> Any:
        return self.db.remove({"collection": self.name, "search": search, "context": context or {}})

    def remove_one(self, search: dict[str, Any], context: dict[str, Any] | None = None) -> Any:
        return self.db.remove_one({"collection": self.name, "search": search, "context": context or {}})

    def removeOne(self, *args: Any, **kwargs: Any) -> Any:
        return self.remove_one(*args, **kwargs)

    def update_one_or_add(
        self,
        search: dict[str, Any],
        updater: dict[str, Any],
        add_arg: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        id_gen: bool = True,
    ) -> Any:
        return self.db.update_one_or_add({
            "collection": self.name,
            "search": search,
            "updater": updater,
            "add_arg": add_arg or {},
            "context": context or {},
            "id_gen": id_gen,
        })

    def updateOneOrAdd(self, *args: Any, **kwargs: Any) -> Any:
        return self.update_one_or_add(*args, **kwargs)

    def toggle_one(
        self,
        search: dict[str, Any],
        data: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> Any:
        return self.db.toggle_one({
            "collection": self.name,
            "search": search,
            "data": data or {},
            "context": context or {},
        })

    def toggleOne(self, *args: Any, **kwargs: Any) -> Any:
        return self.toggle_one(*args, **kwargs)
