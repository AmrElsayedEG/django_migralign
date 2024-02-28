import re
import os
from django.db.migrations.recorder import MigrationRecorder
from django.apps import apps

class Helper():
    def get_max_migration(self, app_name, migration_files_dir):
        """
            Implemented By: Amr Elsayed

            Retrieves the maximum migration number for a given app and migration files directory.

            Parameters:
                app_name (str): The name of the Django app.
                migration_files_dir (str): The path to the directory containing migration files.

            Returns:
                str: The maximum migration number found in the migration files directory for the specified app.
                    Returns None if no maximum migration is found.

            This function queries the database to find the maximum migration applied to the specified app,
            then reads the content of a file named 'max_migration.txt' located in the given migration files directory.
            It returns the first line of the file, which is assumed to contain the maximum migration number.
        """
        migration_model = MigrationRecorder.Migration
        max_migration = migration_model.objects.filter(app=app_name).order_by('-applied').first()
        if not max_migration:
            return None
        with open(str(migration_files_dir)+'/max_migration.txt', 'r') as file:
                    return file.read().split('\n')[0]
        
    def get_app_config_by_name(self, app_name):
        """
            Implemented By: Amr Elsayed

            Retrieves the AppConfig object of a Django app by its name.

            Parameters:
                app_name (str): The name of the Django app to retrieve the AppConfig for.

            Returns:
                AppConfig or None: The AppConfig object of the specified app if found, 
                                otherwise returns None.

            This function iterates over all installed app configurations using apps.get_app_configs(),
            and checks if the name attribute of each AppConfig matches the provided app_name.
            If a match is found, the corresponding AppConfig object is returned.
            If no match is found, None is returned.
        """
        for app_config in apps.get_app_configs():
            if app_config.name == app_name:
                return app_config
        return None

    def write_migration_file_dependencies(self, migration_files_dir, migration_name, values:list):
        """
            Implemented By: Amr Elsayed

            Writes new values to the dependencies list in a Django migration file.

            Parameters:
                migration_files_dir (str): The directory path where migration files are located.
                migration_name (str): The name of the migration file (without the '.py' extension).
                values (list): A list of tuples representing the new dependencies to be written to the migration file.

            Returns:
                bool: True if the operation is successful, otherwise False.

            This function reads the content of a Django migration file located in the specified directory.
            It searches for the 'dependencies' list within the file content using regular expressions.
            Once found, it replaces the existing dependencies with the new values provided.
            The modified content is then written back to the migration file.

            Note: The 'dependencies' list is assumed to be properly formatted and enclosed in square brackets.
        """
        migration_file_path = migration_files_dir + migration_name + '.py'
        self.stdout.write(f"New value {values}")
        with open(migration_file_path, 'r') as file:
                content = file.read()

        dependencies_match = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL | re.MULTILINE)
        dependencies_string = dependencies_match.group(0).strip()
        new_dependencies_string = f"dependencies = {repr(values)}"
        content = content.replace(dependencies_string, new_dependencies_string)
        with open(migration_file_path, 'w') as file:
                    file.write(content)
        return True
        
    def fix_migration_files(self, unapplied_migrations):
        """
            Implemented By: Amr Elsayed

            Fixes migration files by updating dependencies and max_migration files.

            Parameters:
                unapplied_migrations (list): A list of tuples representing unapplied migrations, 
                                            where each tuple contains the app name and migration name.

            Returns:
                bool: True if the operation is successful, otherwise False.

            This function iterates over unapplied migrations, updates their dependencies in the migration files,
            and updates the max_migration file for each app. It also checks for corrupted max_migration files
            and handles errors gracefully.

            Note: The function assumes that migration files are located in the 'migrations' directory of each app and this should be created automatically.
        """
        try:
            copy_unapplied_migrations = unapplied_migrations.copy()
            for migrationFile in unapplied_migrations:
                app_name, migration_name = migrationFile
                if not app_name:
                     return self.stdout.write(f"[Error] Can't find app with label {app_name}")
                migration_files_dir = apps.get_app_config(app_name.label).path + "/migrations/"

                try:
                    max_migration = self.get_max_migration(app_name.label, migration_files_dir)
                    if max_migration in str(copy_unapplied_migrations):
                        self.stdout.write(f"Warning: You have a corrupted max_migration.txt file in app {app_name}")
                        continue
                except FileNotFoundError:
                    self.stdout.write(f"[Error] Can't find max_migration file for {app_name}")
                    continue
                if max_migration is not None:
                    new_dependency = [(app_name.label, max_migration)]
                    override_migration_file = self.write_migration_file_dependencies(migration_files_dir, migration_name, new_dependency)
                    if not override_migration_file:
                        self.stdout.write(f"Error on ({app_name}, {max_migration})")
                        continue
                with open(str(migration_files_dir)+'/max_migration.txt', 'w') as file:
                        file.write(migration_name)
                
                copy_unapplied_migrations.remove(migrationFile)
            return True
        except Exception as e:
            self.stdout.write(f"Error: {e}")
            return False
    
    def get_unapplied_changes(self):
        """
            Implemented By: Amr Elsayed

            Retrieves unapplied changes from migration files for all available apps.

            Returns:
                list: A list of tuples representing unapplied changes, where each tuple contains the app name and migration name.

            This function iterates over all available apps and retrieves unapplied changes from their migration files.
            It compares the list of migration files with applied migrations in the database to find unapplied migrations.
            The unapplied changes are then returned as a list of tuples containing the app name and migration name.
        """
        available_apps = self.project_apps
        general_unapplied_migrations = []
        for my_app_name in available_apps:
            app_name = self.get_app_config_by_name(my_app_name)
            if not app_name:
                    return self.stdout.write(f"[Error] Can't find app with label {my_app_name}")
            dir_content = os.listdir(f'{apps.get_app_config(app_name.label).path}/migrations')
            migration_files = [file.split('.')[0] for file in dir_content \
                            if file.endswith('.py') and file != '__init__.py' \
                                and not file.startswith('0001_') and file.startswith('0')]
            migration_model = MigrationRecorder.Migration
            applied_migrations = list(migration_model.objects.filter(app=app_name.label).values_list('name', flat=True))
            unapplied_migrations = list(set(migration_files) - set(applied_migrations))
            general_unapplied_migrations += [(app_name, migration_name) for migration_name in unapplied_migrations]
        general_unapplied_migrations = sorted(general_unapplied_migrations, key=lambda x: x[1])
        return general_unapplied_migrations
    
    def generate_max_migration_files(self):
        """
            Implemented By: Amr Elsayed

            Generates max_migration files for all available apps.

            This function iterates over all available apps and generates max_migration files.
            It retrieves the latest applied migration for each app from the database and writes it to the max_migration file.
            If a max_migration file already exists, it is replaced with the latest migration.
        """
        available_apps = self.project_apps
        migration_model = MigrationRecorder.Migration
        created_files = 0
        for my_app in available_apps:
            try:
                app = self.get_app_config_by_name(my_app)
                if not app:
                     return
                migration_path = apps.get_app_config(app.label).path + "/" + "migrations/"
                dir_list = os.listdir(migration_path)
                if self.max_migration_file_name in dir_list:
                    os.remove(migration_path + self.max_migration_file_name)
                max_migration = migration_model.objects.filter(app=app.label).order_by('-applied').first()
                if max_migration:
                    with open(str(migration_path)+'max_migration.txt', 'w') as file:
                        file.write(max_migration.name)
                    self.stdout.write(f"Created Max Migration file for app: {app.label}")
                    created_files += 1
            except:
                self.stdout.write(f"[Error] Creating Max Migration file for app: {app}")
                continue
        self.stdout.write(f"Finished: Created {created_files} Max Migration Files")