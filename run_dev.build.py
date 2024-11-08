import os
from pathlib import Path

import PyInstaller.__main__


def build() -> None:
    script_path = os.path.join(Path(__file__).resolve().parent, "run_dev.py")
    build_path = os.path.join(Path(__file__).resolve().parent, "assets")
    pyi_args = [script_path, "--name=dev", "--onefile", "--noconfirm", "--console", f"--distpath={build_path}"]
    PyInstaller.__main__.run(
        pyi_args,
    )


if __name__ == "__main__":
    build()
