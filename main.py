from fastapi import FastAPI, Request
from pydantic import BaseModel
import os
import tempfile
import pygit2

# Create FastAPI app
app = FastAPI()

# Simple GET
@app.get("/")
def root():
    return {"message": "Hello from FastAPI on macOS M1!"}

# GET with path param
@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello, {name}!"}

# POST with body validation
class Item(BaseModel):
    name: str
    price: float

@app.post("/items/")
def create_item(item: Item):
    return {"received": item.dict()}

@app.post("/webhook")
async def webhook_receiver(request: Request):
    payload = await request.json()

    ref = payload.get("ref")
    if ref != "refs/heads/main":
        return {"status": "ignored"}

    print("Main branch updated! Testing sync with release/phase3...")

    # 1. Clone repo
    tmpdir = tempfile.mkdtemp()
    repo_url = payload["repository"]["clone_url"]
    repo = pygit2.clone_repository(repo_url, tmpdir)

    # 2. Fetch all branches
    for remote in repo.remotes:
        remote.fetch()

    # 3. Ensure release/phase3 exists
    try:
        release_branch = repo.lookup_reference("refs/remotes/origin/release/phase3")
    except KeyError:
        print("❌ release/phase3 branch not found on remote")
        return {"status": "error", "message": "branch missing"}

    # 4. Create local tracking branch
    if "refs/heads/release/phase3" not in repo.references:
        repo.create_branch("release/phase3", release_branch.peel())

    # 5. Lookup commits
    main_commit = repo.lookup_reference("refs/heads/main").peel()
    release_commit = repo.lookup_reference("refs/heads/release/phase3").peel()

    # 6. Merge main → release/phase3
    repo.checkout("refs/heads/release/phase3")
    try:
        repo.merge(main_commit.id)

        if repo.index.conflicts is not None:
            conflicts = [c[0].path for c in repo.index.conflicts]
            print("❌ Conflict detected in files:", conflicts)
            return {"status": "conflict", "files": conflicts}
        else:
            # ✅ NEW CODE: finalize merge commit
            tree_id = repo.index.write_tree()
            merge_commit = repo.create_commit(
                "refs/heads/release/phase3",
                repo.default_signature,
                repo.default_signature,
                "Merge main into release/phase3",
                tree_id,
                [release_commit.id, main_commit.id],
            )
            repo.state_cleanup()

            # ✅ Push changes to remote
            remote = repo.remotes["origin"]
            remote.push(["refs/heads/release/phase3"])

            print("✅ No conflicts, merge committed & pushed")
            return {"status": "merged", "commit": str(merge_commit)}
    except Exception as e:
        print("❌ Merge error:", str(e))
        return {"status": "error", "detail": str(e)}