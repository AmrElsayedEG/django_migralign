from django.core.management.base import BaseCommand
from django.conf import settings
from .helper import *

class Command(BaseCommand, Helper):
    help = """
            This command helps to resolve potential migration conflict, It also helps to align migration files across environments. \n
            Run this command before migrate command on server, Don't deploy max_migration.txt files into any environment \n
            Make the server create it's own maxx_migration.txt files. \n
            This command needs a variable in your settings file called INSTALLED_PROJECT_APPS that holds your django apps that has migrations \n
            Note: The dependencies could be different than what's in your Git because this is the only way to have the same migration names does the same thing.
        """
    
    def __init__(self, *args, **kwargs):
         super().__init__(*args, **kwargs)
         self.project_apps = settings.INSTALLED_PROJECT_APPS if 'INSTALLED_PROJECT_APPS' in dir(settings) else None
         self.max_migration_file_name = 'max_migration.txt'

    def handle(self, *args, **options):
        if not self.project_apps:
             self.stdout.write("Please set variable INSTALLED_PROJECT_APPS in settings file and assign your apps to it.")
             return
        self.stdout.write("Stating to check migration files ...")

        self.stdout.write("STEP 1 ---> Recreating max_migration.txt Files")
        self.generate_max_migration_files()

        self.stdout.write("STEP 2 ---> Checking Unapplied Migration Changes")
        unapplied_migrations = self.get_unapplied_changes()
        if len(unapplied_migrations) == 0:
            self.stdout.write("Finished: No new migrations found")
            return
        self.stdout.write(f"We got the following migrations to check : {unapplied_migrations}")
        
        self.stdout.write("STEP 3 ---> Check & Fix Migration Files")
        result = self.fix_migration_files(unapplied_migrations)
        
        self.stdout.write("Finished: Files ready to be migrated to the database!" if result else "Failed: An Error Occured")