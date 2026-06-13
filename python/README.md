# wxn0brp-db-conduit

Python bridge for ValtheraDB Conduit.

Install the package:

```bash
pip install wxn0brp-db-conduit
```

Import the package from the `wxn0brp.db` namespace:

```python
from wxn0brp.db import conduit
```

## Quick Start

Create a controller, initialize a DB, then work with collections:

```python
from wxn0brp.db import conduit

controller = conduit.ValtheraConduit("./vendor/vdb", auto_download=True)

db = controller.data.init("./data")
users = db.c("users")

users.add({"name": "Ada"})
print(users.find({"name": "Ada"}))

controller.shutdown()
```

Use a context manager when you want the conduit process to shut down automatically:

```python
from wxn0brp.db import conduit

with conduit.ValtheraConduit("./vendor/vdb", auto_download=True) as controller:
    db = controller.data.init("./data")
    users = db.c("users")

    users.add({"name": "Ada"})
    print(users.find({"name": "Ada"}))
```

## Controller and DB Initialization

`ValtheraConduit` controls the conduit binary process. A DB must be initialized before it can execute operations.

Attribute style:

```python
db = controller.data.init("./data", opts={"numberId": False})
```

Explicit style:

```python
db = controller.init("data", "./data", opts={"numberId": False})
```

## API Shape

Attribute-style DB initialization names the DB from the attribute:

```python
db = controller.data.init("./data")
```

The explicit equivalent is:

```python
db = controller.init("data", "./data")
```

`opts` is optional and defaults to `{}`:

```python
db = controller.data.init("./data", opts={"numberId": False})
```

Collections are available through `db.c(name)`, `db.collection(name)`, or attribute access:

```python
users = db.c("users")
users = db.collection("users")
users = db.users
```

Both Pythonic snake_case and Valthera-style camelCase aliases are available for methods such as `find_one`/`findOne`, `update_one`/`updateOne`, and `update_one_or_add`/`updateOneOrAdd`.

For explicit binary installation, run:

```bash
python -m wxn0brp.db.conduit.install --install-dir ./vendor/vdb
```

## License

MIT
