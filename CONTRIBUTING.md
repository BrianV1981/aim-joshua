# Contributing to J.O.S.H.U.A.

Welcome to the J.O.S.H.U.A. repository! We strictly enforce a GitOps-based workflow for all contributions to maintain stability and prevent collisions.

## The 3-Step GitOps Pipeline

To contribute, you must use our native CLI tools to manage your workflow. **Do not develop directly on `main`**.

### 1. `aim bug` (Report an Issue)
If you find a bug or want to request a feature, use the `aim bug` command to create a tracked issue on the GitHub board.
```bash
./aim bug "Description of the issue or feature request"
```
*(Alternatively, you can claim an existing issue using `./aim projects in-progress <issue_id>`)*

### 2. `aim fix` (Spawn a Workspace)
Once you have an issue ID, spawn an isolated `git worktree` to begin your development. This prevents branch collisions and keeps your primary repository clean.
```bash
./aim fix <issue_id>
cd workspace/issue-<issue_id>
```
Make your code changes, write tests, and ensure everything works empirically within this isolated workspace. You should stage your changes manually using `git add` and `git commit`.

### 3. `aim promote` (Merge and Clean)
Once your code is tested and committed, promote your isolated workspace back to `main`. This command will automatically:
- Back up the current `main` branch.
- Merge your worktree's branch into `main`.
- Deploy the new baseline.
- Clean up and delete your local workspace directory.

From within your `workspace/issue-<issue_id>` directory, run:
```bash
../aim promote
```

Finally, mark your issue as done on the board:
```bash
./aim projects done <issue_id>
```

Thank you for contributing!
