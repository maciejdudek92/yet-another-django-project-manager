import os
import re
import shutil
import sys
import uuid
import zipfile
from pathlib import Path

import click
from dotenv import set_key
from InquirerPy import get_style, inquirer
from InquirerPy.base.control import Choice


class DjangoProjectManager:
    # console: Console
    BASE_DIR: str
    PROJECT_NAME: str
    PROJECT_DIR: str
    TEMP_DIR: str
    ASSETS_ZIP: str
    ASSETS_DIR: str
    DJANGO_DIR: str
    VENV_DIR: str
    SETTINGS_PATH: str
    URLS_PATH: str
    NEXTJS_DIR: str
    # django libs
    include_ninja: bool
    include_rest_auth: bool
    include_postgres_sql: bool
    # nextjs
    create_next_js: bool
    nextjs_project_name: str | None
    # deploy
    deploy_option: str

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
        self._question_style = get_style({"question": "#7df7fa", "questionmark": "#7df7fa"}, style_override=True)

        # self.console = Console()
        self.BASE_DIR = Path(sys.argv[0]).resolve().parent
        self.TEMP_DIR = self.BASE_DIR
        if hasattr(sys, "_MEIPASS"):
            self.TEMP_DIR = sys._MEIPASS  # noqa: SLF001
        self.ASSETS_ZIP = os.path.join(self.TEMP_DIR, "assets.zip")
        self.__prepare_assets()

    def __check_project_dir(self):
        if os.path.exists(self.PROJECT_DIR):
            if self.PROJECT_NAME == "." and len(os.listdir(self.PROJECT_DIR)) > 0:
                click.echo(click.style(f">> [ERROR] Folder '{self.PROJECT_DIR}' is not empty", fg="red"))
                sys.exit(1)

            if click.confirm(click.style(f">> [WARNING] Found folder '{self.PROJECT_NAME}' in directory, delete?", fg="yellow"), default=True):
                shutil.rmtree(self.PROJECT_DIR)
            else:
                click.echo(click.style("Aborted!", fg="red"), default=True)
                sys.exit(1)
        click.echo(f">> [INFO] Project directory -> {self.PROJECT_DIR}")

    def set_project_name(self):
        self.PROJECT_NAME = click.prompt(click.style("Enter project name", fg="cyan"), default=".")
        if self.PROJECT_NAME == ".":
            self.PROJECT_DIR = self.BASE_DIR
        else:
            self.PROJECT_DIR = os.path.join(self.BASE_DIR, self.PROJECT_NAME)

        self.__check_project_dir()
        os.mkdir(self.PROJECT_DIR)

    def __pip_install(self, libs: str):
        pip = f"{self.VENV_DIR}/bin/pip"
        return os.system(f"'{pip}' install {libs}")

    def __django_admin(self, args: str) -> int:
        django_admin = f"'{self.VENV_DIR}/bin/django-admin'"
        click.echo(self.DJANGO_DIR)
        click.echo(django_admin)
        return os.system(f"cd '{self.DJANGO_DIR}' && {django_admin} {args}")

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

    def start_django_app(self):
        if click.confirm(click.style("Would you like to start django app?", fg="cyan"), default=True):
            name = click.prompt(click.style("Enter app name", fg="cyan"))
            click.echo(f">> [INFO] Creating new django app -> {name}")
            if self.__django_admin(args=f"startapp {name}") != 0:
                click.echo(click.style(">> [ERROR] Django app cannot be created", fg="red"), color=True, err=True)
                sys.exit(1)
            click.echo(click.style(">> [RESULT] Django app successfully created", fg="green"), color=True)

    def create_venv(self):
        click.echo(">> [INFO] Creating virtual environment")
        if os.system(f"python3 -m venv '{self.VENV_DIR}'") != 0:
            click.echo(click.style(">> [ERROR] Virtual environment cannot be created", fg="red"), color=True, err=True)
            sys.exit(1)
        click.echo(click.style(">> [RESULT] Virtual environment created", fg="green"), color=True)

    def __prepare_assets(self):
        self.ASSETS_DIR = os.path.join(self.TEMP_DIR, "temp_assets")
        if os.path.exists(self.ASSETS_DIR):
            shutil.rmtree(self.ASSETS_DIR)

        with zipfile.ZipFile(self.ASSETS_ZIP, "r") as _zip:
            _zip.extractall(self.ASSETS_DIR)

    def __add_custom_user(self):
        users_module_path = os.path.join(self.ASSETS_DIR, ".django_users")
        shutil.copytree(users_module_path, os.path.join(self.DJANGO_DIR, "users"))

    def add_run_dev(self):
        run_dev_path = os.path.join(self.ASSETS_DIR, "run_dev.sh")
        dest_run_dev_path = os.path.join(self.BASE_DIR, "run_dev.sh")
        with open(run_dev_path, "r+") as file:
            content = file.read()
            content = content.replace(
                "{{django_path}}",
                f"'{self.DJANGO_DIR}'",
            )
            content = content.replace(
                "{{next_js_path}}",
                f"'{self.NEXTJS_DIR}'",
            )
            file.seek(0)
            file.write(content)
            file.truncate()
        dev_exe_path = os.path.join(self.ASSETS_DIR, "dev")
        dest_dev_exe_path = os.path.join(self.BASE_DIR, "dev")
        shutil.copyfile(run_dev_path, dest_run_dev_path)
        shutil.copyfile(dev_exe_path, dest_dev_exe_path)
        os.system(f"chmod +x '{dest_run_dev_path}'")
        os.system(f"chmod +x '{dest_dev_exe_path}'")

    def __update_url_file(self):
        # if self.create_next_js:
        #     self.urlpatterns.append("path('', include('django_nextjs.urls'))")
        #     self.urlpatterns.append("re_path(r'^.*', nextjs_page(), name='frontpage')")
        #     with open(self.URLS_PATH, "r+") as urls:
        #         content = urls.read()
        #         urlpatterns_str = "\n".join(f"    {u}," for u in self.urlpatterns)
        #         content = re.sub(r"(urlpatterns = \[)([\s\S]*?)(\])", rf"\1\n{urlpatterns_str}\n\3", content)
        #         content = content.replace("from django.urls import path", "from django.urls import path, include, re_path\nfrom django_nextjs.views import nextjs_page\n")
        #         urls.seek(0)
        #         urls.write(content)
        #         urls.truncate()
        pass

    def update_project_files(self):
        self.__update_settings_file()
        self.__update_url_file()

    def __update_settings_file(self):
        click.echo(">> [INFO] Updating project settings file")
        with open(self.SETTINGS_PATH, "r+") as settings:
            content = settings.read()
            secret_key = str(uuid.uuid4())
            set_key(os.path.join(self.DJANGO_DIR, ".env"), "SECRET_KEY", secret_key)

            content = content.replace("from pathlib import Path", "from pathlib import Path\nfrom decouple import config\nimport os\n")
            content = re.sub(r"(SECRET_KEY = )(.*)", r"\1config('SECRET_KEY')", content)
            if self.include_rest_auth:
                self.installed_apps.append("rest_framework.authtoken")

            if self.include_cors:
                self.installed_apps.append("corsheaders")

                middleware_str = "\n".join(f'    "{m}",' for m in self.middleware)
                content = re.sub(r"(MIDDLEWARE = \[)([\s\S]*?)(\])", rf"\1\n{middleware_str}\n\3", content)
                content += "\nCORS_ALLOW_ALL_ORIGINS = True\n"  # adding at end

            if self.include_custom_user:
                self.installed_apps.append("users")
                content += '\nAUTH_USER_MODEL = "users.User"\n'

            installed_apps_str = "\n".join(f'    "{m}",' for m in self.installed_apps)
            content = re.sub(r"(INSTALLED_APPS = \[)([\s\S]*?)(\])", rf"\1\n{installed_apps_str}\n\3", content)

            if self.include_postgres_sql:
                content = re.sub(r"(DATABASES = \{)([\s\S]*?)(\})([\s\S]*?)(\})", rf"\1\n{self.postgresql_db}\n\3", content)

            static = """STATIC_URL = "static/"
MEDIA_URL = "media/"
# STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "static")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")\n"""
            content = content.replace("STATIC_URL = 'static/'", static)
            content = content.replace("LANGUAGE_CODE = 'en-us'", "LANGUAGE_CODE = 'pl-PL'")
            content = content.replace("TIME_ZONE = 'UTC'", "TIME_ZONE = 'Europe/Warsaw'")
            content = content.replace("ALLOWED_HOSTS = []", "ALLOWED_HOSTS = ['*']")
            settings.seek(0)
            settings.write(content)
            settings.truncate()

        click.echo(click.style(">> [RESULT] Django settings file updated", fg="green"), color=True)

    def select_and_install_python_packages(self):
        packages = [
            Choice("django-ninja", name="Django Ninja", enabled=True),
            Choice("djangorestframework", name="Rest Auth", enabled=True),
            Choice("django-cors-headers", name="Cors Headers", enabled=True),
            Choice("users", name="Custom User Model", enabled=False),
            Choice("psycopg2", name="PostgreSQL", enabled=False),
        ]
        self.to_install.extend(
            inquirer.checkbox(
                message="Select packages to install:",
                choices=packages,
                cycle=False,
            ).execute(),
        )

        self.include_ninja = "django-ninja" in self.to_install
        self.include_rest_auth = "djangorestframework" in self.to_install
        self.include_cors = "django-cors-headers" in self.to_install
        self.include_postgres_sql = "psycopg2" in self.to_install
        self.include_custom_user = "users" in self.to_install
        self.__install_libraries()

    def start_nextjs_project(self):
        if os.system(f"cd '{self.PROJECT_DIR}' && npx create-next-app@latest {self.nextjs_project_name}") == 0:
            self.NEXTJS_DIR = os.path.join(self.PROJECT_DIR, self.nextjs_project_name)
        else:
            click.echo(click.style(">> [ERROR] NextJS project cannot be created", fg="red"), color=True, err=True)
            sys.exit(1)

    def make_migrations_and_migrate(self):
        return os.system(f"cd '{self.DJANGO_DIR}' && '{self.VENV_DIR}/bin/python' manage.py makemigrations && '{self.VENV_DIR}/bin/python' manage.py migrate")

    def createsuperuser(self):
        click.echo(">> [INFO] Creating admin")

        if self.include_custom_user:
            email = click.prompt(click.style("Enter email", fg="cyan"), default="admin@example.com")
            password = click.prompt(click.style("Enter password", fg="cyan"), default="!@#qwerty", hide_input=True)
            createsuper_user = f'from django.contrib.auth import get_user_model;User = get_user_model();User.objects.create_superuser("{email}","{password}");'
            if (
                os.system(
                    f"cd '{self.DJANGO_DIR}' && '{self.VENV_DIR}/bin/python' manage.py shell -c '{createsuper_user}'",  # noqa: E501
                )
                == 0
            ):
                click.echo(click.style(">> [RESULT] Admin created successfully", fg="green"), color=True)
            else:
                click.echo(click.style(">> [ERROR] Admin user cannot be created", fg="red"), color=True, err=True)
                sys.exit(1)
        else:
            login = click.prompt(click.style("Enter username", fg="cyan"), default="admin")
            email = click.prompt(click.style("Enter email", fg="cyan"), default="admin@example.com")
            password = click.prompt(click.style("Enter password", fg="cyan"), default="!@#qwerty", hide_input=True)
            createsuper_user = f'from django.contrib.auth.models import User; User.objects.create_superuser("{login}","{email}","{password}");'
            if (
                os.system(
                    f"cd '{self.DJANGO_DIR}' && '{self.VENV_DIR}/bin/python' manage.py shell -c '{createsuper_user}'",  # noqa: E501
                )
                == 0
            ):
                click.echo(click.style(">> [RESULT] Admin created successfully", fg="green"), color=True)
            else:
                click.echo(click.style(">> [ERROR] Admin user cannot be created", fg="red"), color=True, err=True)
                sys.exit(1)

    def prepare_folder_structure(self):
        self.DJANGO_DIR = os.path.join(self.PROJECT_DIR, "django")
        if self.deploy_option == "mydevil":
            self.DJANGO_DIR = os.path.join(self.PROJECT_DIR, "public_python")

        self.VENV_DIR = os.path.join(self.DJANGO_DIR, "venv")
        self.SETTINGS_PATH = os.path.join(self.DJANGO_DIR, "config", "settings.py")
        self.URLS_PATH = os.path.join(self.DJANGO_DIR, "config", "urls.py")

    def select_deploy_option(self):
        options = ["mydevil", "docker", "standalone"]
        self.deploy_option = inquirer.select(message="Choose deploy option:", choices=options, default="mydevil", style=self._question_style).execute()

    def __build_for_my_devil(self):
        # click.echo(">> [INFO] Renaming Django project to public_python")
        # public_python_path = os.path.join(self.PROJECT_DIR, "public_python")
        # os.rename(self.DJANGO_DIR, public_python_path)
        # self.DJANGO_DIR = public_python_path
        self.SETTINGS_PATH = os.path.join(self.DJANGO_DIR, "config", "settings.py")
        with open(self.SETTINGS_PATH, "r+") as settings:
            content = settings.read()
            content = re.sub(r"(STATIC_ROOT = )(.*)", r'\1os.path.join(BASE_DIR, "public", "static")', content)
            content = re.sub(r"(MEDIA_ROOT = )(.*)", r'\1os.path.join(BASE_DIR, "public", "static")', content)


        if self.create_next_js:
            click.echo(">> [INFO] Creating app.js in public_nodejs")
            shutil.copyfile(os.path.join(self.ASSETS_DIR, ".nextjs", "app.js"), os.path.join(self.NEXTJS_DIR, "app.js"))
            # edit npm build in package.json
            with open(os.path.join(self.NEXTJS_DIR, "package.json"), "r+") as package_json:
                content = package_json.read()
                content = content.replace("next build", "npm install --cpu=wasm32 sharp && next build")
                package_json.seek(0)
                package_json.write(content)
                package_json.truncate()

        click.echo(">> [INFO] Preparing passenger_wsgi.py file")
        content = """import os
    import sys
    from urllib.parse import unquote

    from django.core.wsgi import get_wsgi_application

    sys.path.append(os.getcwd())
    os.environ['DJANGO_SETTINGS_MODULE'] = "config.settings"


    def application(environ, start_response):
        _application = get_wsgi_application()
        return _application(environ, start_response)"""

        with open(os.path.join(self.DJANGO_DIR, "passenger_wsgi.py"), "w+") as passenger:
            passenger.write(content)

    def __build_for_docker(self):
        django_dockerfile_path = os.path.join(self.ASSETS_DIR, "Dockerfile.django_only")
        treafik_dockerfile_path = os.path.join(self.ASSETS_DIR, "Dockerfile.treafik")
        nextjs_dockerfile_path = os.path.join(self.ASSETS_DIR, "Dockerfile.nextjs")

        dockecompose_path = os.path.join(self.ASSETS_DIR, "docker-compose_django_only.yaml")

        app_dir = os.path.join(self.BASE_DIR, "apps")

        treafik_path = os.path.join(app_dir, "treafik")
        django_path = os.path.join(app_dir, "www")
        nextjs_path = os.path.join(app_dir, "www")

        os.mkdir(app_dir)
        os.mkdir(treafik_path)

        if self.create_next_js:
            shutil.move(self.NEXTJS_DIR, nextjs_path)
            self.NEXTJS_DIR = nextjs_path
            django_path = os.path.join(app_dir, "django")
            django_dockerfile_path = os.path.join(self.ASSETS_DIR, "Dockerfile.django_nextjs")
            shutil.copyfile(nextjs_dockerfile_path, os.path.join(self.NEXTJS_DIR, "Dockerfile"))
            dockecompose_path = os.path.join(self.ASSETS_DIR, "docker-compose_django_nextjs.yaml")

        shutil.move(self.DJANGO_DIR, django_path)
        self.DJANGO_DIR = django_path
        shutil.copyfile(django_dockerfile_path, os.path.join(self.DJANGO_DIR, "Dockerfile"))
        shutil.copyfile(treafik_dockerfile_path, os.path.join(treafik_path, "Dockerfile"))

        shutil.copyfile(dockecompose_path, os.path.join(app_dir, "docker-compose.yaml"))

    def create_project(self):
        self.set_project_name()
        self.select_deploy_option()
        self.prepare_folder_structure()
        self.create_venv()
        self.select_and_install_python_packages()
        self.start_django_project()
        # self.start_django_app()
        self.update_project_files()
        self.make_migrations_and_migrate()
        self.createsuperuser()

        self.create_next_js = click.confirm(click.style("Create Next.js project?", fg="cyan"), default=True)
        if self.create_next_js:
            if self.deploy_option == "mydevil":
                self.nextjs_project_name = "public_nodejs"
            else:
                self.nextjs_project_name = click.prompt(click.style("Enter Next.js project name", fg="cyan"), default="frontend")
            self.start_nextjs_project()

        match self.deploy_option:
            # static files larger than 4kb to uploadthing!!!!!
            case "mydevil":
                click.echo(">> [INFO] Prepating project for MyDevil")
                # sourcefiles public/static/
                self.__build_for_my_devil()
            case "docker":
                click.echo(">> [INFO] Prepating project for Docker")
                self.__build_for_docker()
                # sourcefiles static/

                # $PROJECT_ROOT
                # ├── apps/treafik  # Load Balancer
                # ├── apps/postgres ??

                # if next_js
                # ├── apps/django  # Django Backend
                # ├── apps/django/requirements # Python Requirements
                # ├── apps/django/manage.py # Run Django Commands
                # ├── apps/django/package.json # npm commands.
                # ├── apps/www  # Django

                # if not next_js
                # ├── apps/www  # Django
                # ├── apps/www/requirements # Python Requirements
                # ├── apps/www/manage.py # Run Django Commands

            case _:
                pass

        # creating requirements
        with open(os.path.join(self.DJANGO_DIR, "requirements.txt"), "w+") as requirements_txt:
            requirements_txt.writelines(self.to_install, "\n")


        click.echo(click.style(">> [RESULT] Succes!", fg="green"), color=True)
        sys.exit(0)


@click.group()
def main() -> None:
    pass


@click.command("start-project", help="Create new django project")
@click.option("--template", help="Feature not available")
def start_project(template):
    manager = DjangoProjectManager()
    manager.create_project()


@click.command("docker-build")
@click.option("--test", help="Build Docker container from existing Django project")
def docker_build(test):
    click.echo("Not available at this moment -> https://testdriven.io/blog/django-docker-traefik/")
    sys.exit(0)


main.add_command(start_project)
main.add_command(docker_build)

if __name__ == "__main__":
    main()
