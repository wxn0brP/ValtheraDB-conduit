from pathlib import Path
import shutil
from valtheradb_conduit import ValtheraConduit

ROOT = Path(__file__).resolve().parent
INSTALL_DIR = ROOT / "vendor" / "vdb"
DB_DIR = ROOT / "data" / "main"

def reset_data_dir():
    if DB_DIR.exists():
        shutil.rmtree(DB_DIR)
    DB_DIR.mkdir(parents=True, exist_ok=True)


def main():
    reset_data_dir()

    print("starting conduit from:", INSTALL_DIR)
    controller = ValtheraConduit(INSTALL_DIR)

    print("ready:", controller.ready)
    print("ping:", controller.ping())

    db = controller.data.init(DB_DIR, opts={"numberId": False})
    users = db.users

    ada = users.add({"name": "Ada", "lang": "python"})
    bob = users.add({"name": "Bob", "lang": "go"})

    print("inserted:", ada, bob)
    print("collections:", db.get_collections())
    print("find Ada:", users.find({"name": "Ada"}))
    print("find one Bob:", users.find_one({"name": "Bob"}))

    updated = users.update_one({"name": "Ada"}, {"lang": "python-bridge"})
    print("updated Ada:", updated)
    print("all users:", users.find())

    removed = users.remove_one({"name": "Bob"})
    print("removed Bob:", removed)
    print("after remove:", users.find())

    print("dbs:", controller.list_dbs())
    controller.shutdown()
    print("shutdown ok")

if __name__ == "__main__":
    main()
