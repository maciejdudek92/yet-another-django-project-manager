# {{site_name}}
# {{server_admin}}
import os
import shutil
import sys
import uuid
import zipfile
from pathlib import Path

import click
from dotenv import set_key

BASE_DIR = Path(sys.argv[0]).resolve().parent
TEMP_DIR = sys._MEIPASS
# TEMP_DIR = os.path.join(BASE_DIR, "temp")
ASSETS = os.path.join(TEMP_DIR, "assets.zip")


def main() -> None:
    print("Creating new Django project")

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

    libs = ["django", "python-decouple"]
    org_installed_apps = """INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
"""
    org_databases = """DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}"""
    org_middleware = """MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]"""

    include_ninja_api = click.confirm("Include NinjaApi?", default=True)
    if include_ninja_api:
        libs.append("django-ninja")

    include_rest = click.confirm("Include Rest Framework?", default=True)
    if include_rest:
        libs.append("djangorestframework")

    include_cors = click.confirm("Include Cors Headers?", default=True)
    if include_cors:
        libs.append("django-cors-headers")

    include_postgres_sql = click.confirm("Include PostgreSQL?", default=False)
    if include_postgres_sql:
        libs.append("psycopg2")

    include_custom_user = click.confirm("Include Custom User Model?", default=True)

    # for lib in libs:
    #     # run([pip, "install", lib], cwd=project_dir, check=False)
    libs_string = " ".join(libs)
    if os.system(f"'{pip}' install {libs_string}") != 0:
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
        new_installed_apps = """INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',"""

        if include_rest:
            new_installed_apps += "\n    'rest_framework',"
            new_installed_apps += "\n    'rest_framework.authtoken',"

        if include_cors:
            new_installed_apps += "\n    'corsheaders',"

            new_middleware = """MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True"""
        content = content.replace(org_middleware, new_middleware)

        new_installed_apps += "\n]\n"
        if include_custom_user:
            new_installed_apps += '\nAUTH_USER_MODEL = "users.User"\n'

        if include_postgres_sql:
            new_databases = """DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': ‘<db_name>’,
        'USER': '<db_username>',
        'PASSWORD': '<password>',
        'HOST': '<db_hostname_or_ip>',
        'PORT': '<db_port>',
    }
} """
            content = content.replace(org_databases, new_databases)

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
        settings.write(content.replace(org_installed_apps, new_installed_apps))
        settings.truncate()
    print("[RESULT] Succes!")
    sys.exit(0)


if __name__ == "__main__":
    main()
