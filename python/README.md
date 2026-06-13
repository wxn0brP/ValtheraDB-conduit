# ValtheraDB Conduit Python Bridge

The Python bridge mirrors ValtheraDB's object style where possible while keeping Python naming conventions available.

```python
from valtheradb_conduit import ValtheraConduit

controller = ValtheraConduit("./vendor/vdb", auto_download=True)

db = controller.data.init("./data", opts={"numberId": False})
users = db.c("users")

created = users.add({"name": "Ada"})
found = users.find({"name": "Ada"})

print(created)
print(found)

controller.shutdown()
```

Equivalent explicit style:

```python
with ValtheraConduit(binary_path="./dist/valtheradb-conduit") as controller:
    db = controller.init("data", "./data")
    db.add({"collection": "users", "data": {"name": "Ada"}})
    print(db.find({"collection": "users", "search": {"name": "Ada"}}))
```

## API Shape

- `ValtheraConduit()` uses `./vendor/vdb/` as the default binary install directory.
- `ValtheraConduit("/custom/install/dir")` uses a custom install directory.
- `ValtheraConduit(binary_path="...")` bypasses install-dir resolution and runs an exact binary path.
- `auto_download=True` shells out to `curl -fsSL` and downloads the matching GitHub Release asset on first run if the binary is missing.
- `python -m valtheradb_conduit.install --install-dir ./vendor/vdb` can be used as an explicit install/postinstall step.
- `controller.<name>.init(dir, opts=None)` initializes an internal DB name.
- `controller.init(name, dir, opts=None)` is the explicit equivalent.
- `db.execute(op, body=None)` maps directly to Conduit's `EXECUTE_JSON` frame.
- `db.c("users")` and `db.collection("users")` return a `Collection`.
- Collection methods build Valthera query objects for the collection.

Both Pythonic snake_case and Valthera-style camelCase aliases are available for methods such as `find_one`/`findOne`, `update_one`/`updateOne`, and `update_one_or_add`/`updateOneOrAdd`.

The bridge serializes calls per internal DB name because the protocol uses the DB name as the response correlation key.
