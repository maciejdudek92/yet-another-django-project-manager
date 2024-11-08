import subprocess
import sys
import threading

import click


def django_app(path: str):
    subprocess.run(["venv/bin/python", "manage.py", "runserver"], cwd=path, check=False)


def next_js_app(path: str):
    subprocess.run(["npm", "run", "dev"], cwd=path, check=False)


@click.command()
@click.option("--django", required=True)
@click.option("--nextjs", required=True)
def main(django, nextjs):
    DJANGO_BASE_DIR = f"'{django}'"
    NEXTJS_BASE_DIR = f"'{nextjs}'"
    print(sys.argv)

    thread_1 = threading.Thread(target=django_app, kwargs={"path": DJANGO_BASE_DIR})
    thread_2 = threading.Thread(target=next_js_app, kwargs={"path": NEXTJS_BASE_DIR})
    thread_1.start()
    thread_2.start()

    thread_1.join()
    thread_2.join()


if __name__ == "__main__":
    main()
