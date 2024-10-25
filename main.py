import os
import re
import shutil
import sys
import uuid
import zipfile
from pathlib import Path

import click
from dotenv import set_key


def __help():
    arg = " ".join(sys.argv[1:])
    print(f"""unknown option: {arg}

USAGE:
-c, --create    |    Create new Django project
-d, --docker    |    Build docker container from existing Django project""")
    sys.exit(0)


def __create_project() -> None:
    print("[INFO] Creating new Django project")
    BASE_DIR = Path(sys.argv[0]).resolve().parent
    TEMP_DIR = sys._MEIPASS
    ASSETS = os.path.join(TEMP_DIR, "assets.zip")
    project_dir = os.path.join(BASE_DIR, "django")
    print(f"[INFO] Project directory -> {project_dir}")
    if os.path.exists(project_dir):
        print("[INFO] Found Django project in directory, deleting...")
        shutil.rmtree(project_dir)

    venv_dir = os.path.join(project_dir, "venv")

    print("[INFO] Creating virtual environment")
    if os.system(f"python3 -m venv '{venv_dir}'") != 0:
        print("[ERROR] Virtual environment cannot be created")
        sys.exit(1)
    print("[RESULT] Virtual environment created")

    print("[INFO] Activating virtual environment")
    if os.system(f"source '{venv_dir}/bin/activate'") != 0:
        print("[ERROR] Virtual environment cannot be activated")
        sys.exit(1)
    print("[RESULT] Virtual environment activated")

    pip = f"{venv_dir}/bin/pip"
    python = f"{venv_dir}/bin/python"

    to_install = ["django", "python-decouple"]

    installed_apps = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
    ]
    middleware = [
        "corsheaders.middleware.CorsMiddleware",
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    ]
    sqlite_db = """    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }"""
    postgresql_db = """    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '<db_name>',
        'USER': '<db_username>',
        'PASSWORD': '<password>',
        'HOST': '<db_hostname_or_ip>',
        'PORT': '<db_port>',
    }"""

    org_urls = """urlpatterns = [
    path('admin/', admin.site.urls),
]"""
    include_ninja = click.confirm("Include DjangoNinja? https://django-ninja.dev", default=True)
    if include_ninja:
        to_install.append("django-ninja")

    include_rest = click.confirm("Include Rest Framework?", default=True)
    if include_rest:
        to_install.append("djangorestframework")

    include_cors = click.confirm("Include Cors Headers?", default=True)
    if include_cors:
        to_install.append("django-cors-headers")

    include_postgres_sql = click.confirm("Include PostgreSQL?", default=False)
    if include_postgres_sql:
        to_install.append("psycopg2")

    include_next_js = click.confirm("Include Next.js? https://pypi.org/project/django-nextjs/", default=True)
    if include_next_js:
        to_install.append("django-nextjs")

    include_custom_user = click.confirm("Include Custom User Model?", default=True)

    install_string = " ".join(to_install)
    if os.system(f"'{pip}' install {install_string}") != 0:
        print("[ERROR] Libraries cannot be installed")
        sys.exit(1)
    print("[RESULT] Libraries successfully installed")

    # run([python, "-m", "django", "startproject", "config", project_dir], cwd=project_dir, check=False)

    print("[INFO] Creating Django project")
    if os.system(f"cd '{project_dir}' &&'{python}' -m django startproject config .") != 0:
        print("[ERROR] Django project cannot be created")
        sys.exit(1)
    print("[RESULT] Django project successfully created")

    # print("[INFO] Creating .env file")
    # if os.system("touch .env") != 0:
    #     print("[ERROR] Cannot create .env file")
    #     sys.exit(1)
    # print("[RESULT] .env file successfully created")

    if include_custom_user:
        users_module_path = os.path.join(TEMP_DIR, ".django_users")

        if os.path.exists(os.path.join(users_module_path)):
            shutil.rmtree(os.path.join(users_module_path))

        with zipfile.ZipFile(ASSETS, "r") as _zip:
            _zip.extractall(users_module_path)

        shutil.copytree(users_module_path, os.path.join(project_dir, "users"))

    settings_path = os.path.join(project_dir, "config", "settings.py")
    urls_path = os.path.join(project_dir, "config", "urls.py")
    new_settings_lines = []

    with open(settings_path) as settings:
        for line in settings.readlines():
            if "from pathlib import Path" in line:
                line = "from pathlib import Path\nfrom decouple import config\nimport os\n"

            if "SECRET_KEY" in line:
                secret_key = str(uuid.uuid4())
                set_key(os.path.join(project_dir, ".env"), "SECRET_KEY", secret_key)
                line = 'SECRET_KEY = config("SECRET_KEY")'

            new_settings_lines.append(line)

    with open(settings_path, "w") as settings:
        settings.writelines(new_settings_lines)

    with open(settings_path, "r+") as settings:
        content = settings.read()
        if include_rest:
            installed_apps.append("rest_framework")
            installed_apps.append("rest_framework.authtoken")

        if include_cors:
            installed_apps.append("rest_framework")

            middleware_str = "\n".join(f'    "{m}",' for m in middleware)
            content = re.sub(r"(MIDDLEWARE = \[)([\s\S]*?)(\])", rf"\1\n{middleware_str}\n\3", content)
            content += "\nCORS_ALLOW_ALL_ORIGINS = True\n"  # adding at end

        if include_next_js:
            installed_apps.append("django_nextjs.apps.DjangoNextJSConfig")

        if include_custom_user:
            installed_apps.append("users")
            content += '\nAUTH_USER_MODEL = "users.User"\n'

        installed_apps_str = "\n".join(f'    "{m}",' for m in installed_apps)
        content = re.sub(r"(INSTALLED_APPS = \[)([\s\S]*?)(\])", rf"\1\n{installed_apps_str}\n\3", content)

        if include_postgres_sql:
            content = re.sub(r"(DATABASES = \{)([\s\S]*?)(\})([\s\S]*?)(\})", rf"\1\n{postgresql_db}\n\3", content)

        content = re.sub(r"(INSTALLED_APPS = \[)([\s\S]*?)(\])", rf"\1\n{installed_apps_str}\3", content)
        org_static = "STATIC_URL = 'static/'"
        new_static = """STATIC_URL = "static/"
MEDIA_URL = "media/"
# STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)
STATIC_ROOT = os.path.join(BASE_DIR, "public", "static")
MEDIA_ROOT = os.path.join(BASE_DIR, "public", "media")\n"""
        content = content.replace(org_static, new_static)
        content = content.replace("LANGUAGE_CODE = 'en-us'", "LANGUAGE_CODE = 'pl-PL'")
        content = content.replace("TIME_ZONE = 'UTC'", "TIME_ZONE = 'Europe/Warsaw'")
        content = content.replace("ALLOWED_HOSTS = []", "ALLOWED_HOSTS = ['*']")

        settings.seek(0)
        settings.write(content)
        settings.truncate()

        if include_next_js:
            with open(urls_path, "r+") as urls:
                content = urls.replace(
                    org_urls,
                    """urlpatterns = [
        path('admin/', admin.site.urls),
        path('', include('django_nextjs.urls'))
    ]""",
                )
                content = content.replace("from django.urls import path", "from django.urls import path, include")
                urls.seek(0)
                urls.write(content)
                urls.truncate()
    print("[RESULT] Succes!")
    sys.exit(0)


def __build_docker() -> None:
    print("Not available at this moment -> https://testdriven.io/blog/django-docker-traefik/")
    sys.exit(0)


def main() -> None:
    CREATE = ["-c", "--create"]
    BUILD_DOCKER = ["-d", "--docker "]

    if len(sys.argv) > 1:
        if sys.argv[1] in CREATE + BUILD_DOCKER:
            if sys.argv[1] in CREATE:
                __create_project()
            elif sys.argv[1] in BUILD_DOCKER:
                __build_docker()
        else:
            __help()
    else:
        __help()


if __name__ == "__main__":
    main()
