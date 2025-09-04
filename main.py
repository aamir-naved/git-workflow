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

    print("Main branch updated! Testing sync with release/phase2...")

    # 1. Clone repo
    tmpdir = tempfile.mkdtemp()
    repo_url = payload["repository"]["clone_url"]
    repo = pygit2.clone_repository(repo_url, tmpdir)

    # 2. Fetch all branches
    for remote in repo.remotes:
        remote.fetch()

    # 3. Ensure release/phase2 exists
    try:
        release_branch = repo.lookup_reference("refs/remotes/origin/release/phase2")
    except KeyError:
        print("❌ release/phase2 branch not found on remote")
        return {"status": "error", "message": "branch missing"}

    # 4. Create local tracking branch
    if "refs/heads/release/phase2" not in repo.references:
        repo.create_branch("release/phase2", release_branch.peel())

    # 5. Lookup commits
    main_commit = repo.lookup_reference("refs/heads/main").peel()
    release_commit = repo.lookup_reference("refs/heads/release/phase2").peel()

    # 6. Merge main → release/phase2
    repo.checkout("refs/heads/release/phase2")
    # Try merge
    try:
        repo.merge(main_commit.id)

        if repo.index.conflicts is not None:
            conflicts = [c[0].path for c in repo.index.conflicts]
            print("❌ Conflict detected in files:", conflicts)
            return {"status": "conflict", "files": conflicts}
        else:
            print("✅ No conflicts, merge successful")
            return {"status": "merged"}
    except Exception as e:
        print("❌ Merge error:", str(e))
        return {"status": "error", "detail": str(e)}

