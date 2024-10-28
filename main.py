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
    click.echo(f"""unknown option: {arg}

USAGE:
-c, --create    |    Create new Django project
-d, --docker    |    Build docker container from existing Django project""")
    sys.exit(0)


class DjangoProjectManager:
    BASE_DIR: str
    TEMP_DIR: str
    ASSETS: str
    DJANGO_PROJECT_DIR: str
    VENV_DIR: str
    SETTINGS_PATH: str
    URLS_PATH: str

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
    postgresql_db = {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "<db_name>",
        "USER": "<db_username>",
        "PASSWORD": "<password>",
        "HOST": "<db_hostname_or_ip>",
        "PORT": "<db_port>",
    }
    urlpatterns = [
        "path('admin/', admin.site.urls)",
    ]

    def __init__(self):
        self.BASE_DIR = Path(sys.argv[0]).resolve().parent
        self.TEMP_DIR = sys._MEIPASS  # noqa: SLF001

    def set_project_name(self, project_name: str):
        self.PROJECT_NAME = project_name
        self.ASSETS = os.path.join(self.TEMP_DIR, "assets.zip")
        self.DJANGO_PROJECT_DIR = os.path.join(self.BASE_DIR, self.PROJECT_NAME)
        self.VENV_DIR = os.path.join(self.DJANGO_PROJECT_DIR, "venv")
        self.SETTINGS_PATH = os.path.join(self.DJANGO_PROJECT_DIR, "config", "settings.py")
        self.URLS_PATH = os.path.join(self.DJANGO_PROJECT_DIR, "config", "urls.py")
        self.__check_project_dir()

    def __check_project_dir(self):
        if os.path.exists(self.DJANGO_PROJECT_DIR):
            click.echo(click.style(">> [WARNING] Found Django project in directory, deleting...", fg="yellow"), color=True)
            shutil.rmtree(self.DJANGO_PROJECT_DIR)
        click.echo(f">> [INFO] Project directory -> {self.DJANGO_PROJECT_DIR}")

    def __pip_install(self, libs: str):
        pip = f"{self.VENV_DIR}/bin/pip"
        return os.system(f"'{pip}' install {libs}")

    def __django_admin(self, args: str) -> int:
        django_admin = f"'{self.VENV_DIR}/bin/django-admin'"
        click.echo(self.DJANGO_PROJECT_DIR)
        click.echo(django_admin)
        return os.system(f"cd '{self.DJANGO_PROJECT_DIR}' && {django_admin} {args}")

    def __install_libraries(self):
        install_string = " ".join(self.to_install)
        click.echo(f">> [INFO] Installing libraries: {install_string}")
        if self.__pip_install(install_string) != 0:
            click.echo(click.style(">> [ERROR] Libraries cannot be installed", fg="red"), color=True, err=True)
            sys.exit(1)
        click.echo(click.style(">> [RESULT] Libraries installed successfully", fg="green"), color=True)

    def start_django_project(self):
        click.echo(">> [INFO] Creating new Django project")
        if self.__django_admin(args="startproject config .") != 0:
            click.echo(click.style(">> [ERROR] Django project cannot be created", fg="red"), color=True, err=True)
            sys.exit(1)
        if self.include_custom_user:
            self.__add_custom_user()

        click.echo(click.style(">> [RESULT] Django project successfully created", fg="green"), color=True)

    def create_venv(self):
        click.echo(">> [INFO] Creating virtual environment")
        if os.system(f"python3 -m venv '{self.VENV_DIR}'") != 0:
            click.echo(click.style(">> [ERROR] Virtual environment cannot be created", fg="red"), color=True, err=True)
            sys.exit(1)
        click.echo(click.style(">> [RESULT] Virtual environment created", fg="green"), color=True)

    def __add_custom_user(self):
        users_module_path = os.path.join(self.TEMP_DIR, ".django_users")
        if os.path.exists(os.path.join(users_module_path)):
            shutil.rmtree(os.path.join(users_module_path))
        with zipfile.ZipFile(self.ASSETS, "r") as _zip:
            _zip.extractall(users_module_path)
        shutil.copytree(users_module_path, os.path.join(self.DJANGO_PROJECT_DIR, "users"))

    def __update_url_file(self):
        if self.include_next_js:
            self.urlpatterns.append("path('', include('django_nextjs.urls'))")
            self.urlpatterns.append("re_path(r'^.*', nextjs_page(), name='frontpage')")
            with open(self.URLS_PATH, "r+") as urls:
                content = urls.read()
                urlpatterns_str = "\n".join(f"    {u}," for u in self.urlpatterns)
                content = re.sub(r"(urlpatterns = \[)([\s\S]*?)(\])", rf"\1\n{urlpatterns_str}\n\3", content)
                content = content.replace("from django.urls import path", "from django.urls import path, include, re_path\nfrom django_nextjs.views import nextjs_page\n")
                urls.seek(0)
                urls.write(content)
                urls.truncate()

    def update_project_files(self):
        self.__update_settings_file()
        self.__update_url_file()

    def __update_settings_file(self):
        click.echo(">> [INFO] Updating project settings file")
        with open(self.SETTINGS_PATH, "r+") as settings:
            content = settings.read()
            secret_key = str(uuid.uuid4())
            set_key(os.path.join(self.DJANGO_PROJECT_DIR, ".env"), "SECRET_KEY", secret_key)
            content = content.replace("from pathlib import Path", "from pathlib import Path\nfrom decouple import config\nimport os\n")
            content = re.sub(r"^SECRET_KEY = .*", r'SECRET_KEY = config("SECRET_KEY")', content)
            if self.include_rest:
                self.installed_apps.append("rest_framework")
                self.installed_apps.append("rest_framework.authtoken")

            if self.include_cors:
                self.installed_apps.append("corsheaders")

                middleware_str = "\n".join(f'    "{m}",' for m in self.middleware)
                content = re.sub(r"(MIDDLEWARE = \[)([\s\S]*?)(\])", rf"\1\n{middleware_str}\n\3", content)
                content += "\nCORS_ALLOW_ALL_ORIGINS = True\n"  # adding at end

            if self.include_next_js:
                self.installed_apps.append("django_nextjs.apps.DjangoNextJSConfig")

            if self.include_custom_user:
                self.installed_apps.append("users")
                content += '\nAUTH_USER_MODEL = "users.User"\n'

            installed_apps_str = "\n".join(f'    "{m}",' for m in self.installed_apps)
            content = re.sub(r"(INSTALLED_APPS = \[)([\s\S]*?)(\])", rf"\1\n{installed_apps_str}\n\3", content)

            if self.include_postgres_sql:
                content = re.sub(r"(DATABASES = \{)([\s\S]*?)(\})([\s\S]*?)(\})", rf"\1\n{self.postgresql_db}\n\3", content)

            static = """STATIC_URL = "static/"
MEDIA_URL = "media/"
# STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)
STATIC_ROOT = os.path.join(BASE_DIR, "public", "static")
MEDIA_ROOT = os.path.join(BASE_DIR, "public", "media")\n"""
            content = content.replace("STATIC_URL = 'static/'", static)
            content = content.replace("LANGUAGE_CODE = 'en-us'", "LANGUAGE_CODE = 'pl-PL'")
            content = content.replace("TIME_ZONE = 'UTC'", "TIME_ZONE = 'Europe/Warsaw'")
            content = content.replace("ALLOWED_HOSTS = []", "ALLOWED_HOSTS = ['*']")
            # content += '\nsubprocess.Popen("npm run dev", shell=True, cwd=f"{BASE_DIR}/frontend/")\n'
            settings.seek(0)
            settings.write(content)
            settings.truncate()

        click.echo(click.style(">> [RESULT] Project settings file updated successfully", fg="green"), color=True)

    def select_and_install_libraries(self):
        self.include_ninja = click.confirm(click.style("Include DjangoNinja? https://django-ninja.dev", fg="cyan"), default=True)
        if self.include_ninja:
            self.to_install.append("django-ninja")

        self.include_rest = click.confirm(click.style("Include Rest Framework?", fg="cyan"), default=True)
        if self.include_rest:
            self.to_install.append("djangorestframework")

        self.include_cors = click.confirm(click.style("Include Cors Headers?", fg="cyan"), default=True)
        if self.include_cors:
            self.to_install.append("django-cors-headers")

        self.include_postgres_sql = click.confirm(click.style("Include PostgreSQL?", fg="cyan"), default=False)
        if self.include_postgres_sql:
            self.to_install.append("psycopg2")

        self.include_next_js = click.confirm(click.style("Include Next.js? https://pypi.org/project/django-nextjs/", fg="cyan"), default=True)
        if self.include_next_js:
            self.to_install.append("django-nextjs")
            self.nextjs_project_name = click.prompt(click.style("Enter Next.js project name", fg="cyan"), default="frontend")

        self.include_custom_user = click.confirm(click.style("Include Custom User Model?", fg="cyan"), default=True)
        self.__install_libraries()

    def start_nextjs_project(self):
        os.system(f"cd '{self.BASE_DIR}' && npx create-next-app@latest {self.nextjs_project_name}")

    def make_migrations_and_migrate(self):
        return os.system(f"cd '{self.DJANGO_PROJECT_DIR}' && '{self.VENV_DIR}/bin/python' manage.py makemigrations && '{self.VENV_DIR}/bin/python' manage.py migrate")

    def create_project(self, project_name):
        self.set_project_name(project_name)
        self.create_venv()
        self.select_and_install_libraries()
        self.start_django_project()
        self.update_project_files()
        self.make_migrations_and_migrate()

        if self.include_next_js:
            self.start_nextjs_project()

        click.echo(click.style(">> [RESULT] Succes!", fg="green"), color=True)
        sys.exit(0)


@click.group()
def main() -> None:
    pass


@click.command("start-project")
@click.option("--name", default="backend", help="Create new django project")
def start_project(name):
    manager = DjangoProjectManager()
    manager.create_project(name)


@click.command("docker-build")
@click.option("--test", help="Build Docker container from existing Django project")
def docker_build(test):
    click.echo("Not available at this moment -> https://testdriven.io/blog/django-docker-traefik/")
    sys.exit(0)


main.add_command(start_project)
main.add_command(docker_build)

if __name__ == "__main__":
    main()
