---
description: Release the application
---

1.  **Update Version**:
    -   Check the current version in `web_app.py`.
    -   Increment the version number (e.g., 1.3 -> 1.4).
    -   Update the `VERSION` variable in `web_app.py`.

2.  **Update Change Log**:
    -   Add a new entry in `CHANGELOG.md` for the new version.
    -   List the key changes and improvements made in this release.
    -   Add the current date.

3.  **Update Documentation**:
    -   Review `README.md` and ensure it reflects the current state of the application.
    -   Update any installation or usage instructions if changed.

4.  **Run Tests**:
    -   Run the test suite to ensure stability.
    -   Command: `python3 -m unittest discover tests`

5.  **Git Commit**:
    -   Stage the modified files: `git add web_app.py CHANGELOG.md README.md`
    -   Commit with a release message: `git commit -m "Release v<VERSION>"`

6.  **Git Tag**:
    -   Create a tag for the new version: `git tag v<VERSION>`
    -   Push changes: `git push && git push --tags`
