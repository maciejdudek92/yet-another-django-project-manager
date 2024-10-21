import os
import shutil
from pathlib import Path

import PyInstaller.__main__


def prepare_assets():
    zip_file = os.path.join(Path(__file__).resolve().parent, "assets")
    folder = os.path.join(Path(__file__).resolve().parent, ".django_users")

    if os.path.exists(zip_file):
        os.remove(zip_file)

    shutil.make_archive(zip_file, "zip", folder)


def build() -> None:
    prepare_assets()
    script_path = os.path.join(Path(__file__).resolve().parent, "main.py")
    build_path = os.path.join(Path(__file__).resolve().parent, "release")
    pyi_args = [script_path, "--name=create-django-project", "--onefile", "--noconfirm", "--console", f"--distpath={build_path}", "--add-data=assets.zip:."]

    PyInstaller.__main__.run(
        pyi_args,
    )


if __name__ == "__main__":
    build()
