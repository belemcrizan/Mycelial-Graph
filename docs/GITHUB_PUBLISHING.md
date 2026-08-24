# Publishing from VS Code to GitHub

Repository: `https://github.com/belemcrizan/Mycelial-Graph`

Open the new V1 folder in VS Code, then use a PowerShell terminal.

## If this folder is not yet a Git repository

```powershell
git init
git branch -M main
git add .
git status
git commit -m "feat: add Mycelial Graph V1 research edition"
git remote add origin https://github.com/belemcrizan/Mycelial-Graph.git
git push -u origin main
```

If `origin` already exists:

```powershell
git remote set-url origin https://github.com/belemcrizan/Mycelial-Graph.git
git push -u origin main
```

## If the remote already contains another V0

Do not force-push. First preserve the current repository and add V1 on a branch:

```powershell
git checkout -b feature/v1-research-edition
git add .
git commit -m "feat: add Mycelial Graph V1 research edition"
git push -u origin feature/v1-research-edition
```

Then review the GitHub diff before merging into `main`.

## Important checks

```powershell
git status
git remote -v
git log -3 --oneline
```

If PowerShell says `not a git repository`, confirm that the terminal is open in the folder containing `.git`. Activating `.venv` does not change the Git working directory.

