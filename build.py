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

    # with zipfile.ZipFile(zip_file, "w") as _zip:
    #     for folder_name, subfolders, filenames in os.walk(folder):
    #         for filename in filenames:
    #             # Create complete filepath of file in directory
    #             file_path = os.path.join(folder_name, filename)
    #             # Add file to zip
    #             _zip.write(file_path, filename)


def build() -> None:
    prepare_assets()
    script_path = os.path.join(Path(__file__).resolve().parent, "main.py")
    build_path = os.path.join(Path(__file__).resolve().parent, "release")
    pyi_args = [script_path, "--name=django_project_cli", "--onefile", "--noconfirm", "--console", f"--distpath={build_path}", "--add-data=assets.zip:."]

    PyInstaller.__main__.run(
        pyi_args,
    )


if __name__ == "__main__":
    build()
