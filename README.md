# ThinkTank-Python-Template
Python setup to get you started experimenting with ThinkTank and Target GenAI solutions


export UV_EXTRA_INDEX_URL="https://binrepo.target.com/artifactory/api/pypi/pypi-remote/simple"


# Using UV

1. **Install uv (one-time):**

   ~~~bash
   pipx install uv
   ~~~

2. **Create the environment from `uv.lock`:**

   ~~~bash
   uv sync
   ~~~

3. **Run anything inside the env:**

   ~~~bash
   uv run python -m your_app
   ~~~

4. **Add / remove a dependency (auto-locks + installs):**

   ~~~bash
   uv add <package>
   uv remove <package>
   ~~~

5. **Change Python version:**

   ~~~bash
   uv python install 3.13     # fetch interpreter once
   uv python pin 3.13         # writes .python-version
   uv sync                    # rebuilds .venv on 3.13
   ~~~

6. **VS Code** picks up the `.venv/` folder automatically.  
   If it doesn’t: open the Command Palette → **“Python: Select Interpreter”** and choose the interpreter ending in `.venv/bin/python` (macOS/Linux) or `.venv\Scripts\python.exe` (Windows).


> **Ignore** `.venv/`—every collaborator just runs `uv sync` to reproduce the exact environment.





# Run the refresh after you save
tgt_cert_refresh


gunicorn -b 0.0.0.0:8000 server:app   