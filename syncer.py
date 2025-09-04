import os
import tempfile
import pygit2
from dotenv import load_dotenv

load_dotenv()

REPO_URL = os.getenv("GITHUB_REPO_URL")
TOKEN = os.getenv("GITHUB_TOKEN")

def clone_repo():
    """
    Clone the repo into a temporary directory with authentication.
    Returns the repo object and path.
    """
    tmpdir = tempfile.mkdtemp()
    callbacks = pygit2.RemoteCallbacks(
        credentials=pygit2.UserPass("x-access-token", TOKEN)
    )
    repo = pygit2.clone_repository(REPO_URL, tmpdir, callbacks=callbacks)
    return repo, tmpdir

def try_merge(branch_name: str):
    repo, path = clone_repo()

    # Checkout target branch
    ref_name = f"refs/remotes/origin/{branch_name}"
    target_commit = repo.lookup_reference(ref_name).peel()
    repo.checkout_tree(target_commit)
    repo.set_head(ref_name)

    # Merge main into this branch
    main_commit = repo.lookup_reference("refs/remotes/origin/main").peel()
    repo.merge(main_commit.oid)

    if repo.index.conflicts is not None:
        return {"status": "conflict", "branch": branch_name}

    # Create new commit for the merge
    tree = repo.index.write_tree()
    author = pygit2.Signature("AutoSync Bot", "bot@example.com")
    committer = author
    repo.create_commit(
        "HEAD",
        author,
        committer,
        f"Auto-merge main into {branch_name}",
        tree,
        [repo.head.target, main_commit.oid]
    )

    return {"status": "merged", "branch": branch_name}
