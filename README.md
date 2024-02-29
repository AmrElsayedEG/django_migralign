
django_migralign
========================

Imagine you fall into situation where you are working in a big team, Both teams are working on different branchs **BUT** when both of you deploy one of you will get conflict because there will be 2 migrations point to the same dependency.

Or another situation where you deploy migration 002 and 003 on DEV and the other team deploy 004 and 005, But the other team deployed first on UAT or Prod, they will need to change the file name and dependency as well, And when u deploy your files you gonna do the exact same thing, So your migration order will not be the same across the servers.

----
Make sure your migration files are stable and linear across different environments with django-migralign.
----

Requirements
============

Python 3 and upwards.


Installation
============

**First,** install with pip:



    python -m pip install django_migralign

**Second,** add the app to your ``INSTALLED_APPS`` setting:



    INSTALLED_APPS = [
        ...,
        "django_migralign",
        ...,
    ]

The package is a middle command that should run between ``makemigrations`` and ``migrate``, the package expects a variable in your settings file called **INSTALLED_PROJECT_APPS**, That variable should have all your apps that contain migration files.



    # project/settings/base.py
    INSTALLED_PROJECT_APPS = ['first_app', 'second_app', ...]

    INSTALLED_APPS = INSTALLED_PROJECT_APPS + THIRD_PARTY_APPS + ...
        ...

The package goes through your project as the following:

**First** : It get's all you project apps and goes into each app migration folder and start creating a max_migration.txt file and then query the database to get the last migration applied within the app and saves it inside max_migration.txt file
``NOTE: max_migration.txt file gets reset each time the command run, But we don't remove it after the command finish working for logging purposes that could help``

**Second** : The app get's all unapplied migrations in the system and order then by **file number**

**Third** : After that the package overide the dependencies value to the latest migration applied, And after that it set's that migration name as the max migration in the txt file so it can be used for the next migration in that app (If any!).

**Fourth** : After handling all migration files you will see prompt with status and will keep the ``max_migration.txt`` file in case you need to track or log anything, But the next time you run the command to fix the migration it will get removed and recreated with the correct max migration from database.

Why This Package?
============

This package focus on solving the migration errors by making sure each migratino file is depending on the last committed migration in the database, So all Nodes will be correct, **You** Could just edit it manually and regenerate or rename the migration file and change the dependencies but this is going to cause another problem.
When doing that you could fall into the following sitiuation:
- You are working with a team that pushes the code regurally, And both of you could work on the same app which causing new migration files
- You created migration (002, 003) and the other team created (004, 005), Now Both of you pushed it to DEV env
- Be aware that 002 will depend on 001 and 004 depends on 003
- Now the other taem pushed migrations to the UAT or Prod, So they will face conflict because 004 depends on 003 which is not exist
- The other team will rename 004 to 002 because the UAT only have (001) because you didn't push you migrations yet
- When the other team renames 004 to 002 and 005 to 0023 and their dependencies as well, Then code will work
- Now when you deploy your code to UAT (002,003) you gonna get migration conflict because you depend on 001 just like the other team and this will cause conflict
- So to solve this you have to change dependencies in both of your migration files and the file names as well to 004 and 005

In the above situation the following happend:
- You manually editted the code and renamed the files
- The migration files will be different in DEV and UAT

So to solve the above issue just use **django_migralign**

When using it, It will change dependency on your behalf and will keep file names as it is, So you can align and make sure all migration names and inner code are the same across environments, The package will change dependecies only which will not affect anything in the code, It just matter of ordering.


Usage
============

You can use the following command:
.. code-block:: python
    python manage.py migralign
        ...

NOTE: You have to use it after **makemigrations** and before **migrate**, So it could align your migrations and making them ready for migrating.

Final Words!
===========

I have made this package because i personally fall into that conflict many times, I have tested it in different scienarios and projects, But maybe there are special cases that are not covered, So in this case please open an **ISSUE** in this repo to discuss it further and make it work under all circumstances.
