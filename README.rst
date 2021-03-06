.. You should enable this project on travis-ci.org and coveralls.io to make
   these badges work. The necessary Travis and Coverage config files have been
   generated for you.

.. image:: https://travis-ci.org/ckan/ckanext-experience.svg?branch=master
    :target: https://travis-ci.org/ckan/ckanext-experience

.. image:: https://coveralls.io/repos/ckan/ckanext-experience/badge.svg
  :target: https://coveralls.io/r/ckan/ckanext-experience

================
ckanext-experience
================

Experience and link to datasets in use. Datasets used in an app, website or
visualization, or featured in an article, report or blog post can be showcased
within the CKAN website. Experiences can include an image, description, tags and
external link. Experiences may contain several datasets, helping users discover
related datasets being used together. Experiences can be discovered by searching
and filtered by tag.

Site sysadmins can promote selected users to become 'Experience Admins' to help
create, populate and maintain experiences.

ckanext-experience is intended to be a more powerful replacement for the
'Related Item' feature.


------------
Requirements
------------


Compatible with CKAN 2.3+.

N.B. The ``migrate`` command, detailed below, requires the Related Item models
and actions, which have been removed in CKAN 2.6. If you wish to migrate your
Related Items, please first upgrade CKAN to 2.5, do the migration, then
continue upgrading to CKAN 2.6+.


------------
Installation
------------

.. Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

To install ckanext-experience:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-experience Python package into your virtual environment::

     pip install ckanext-experience

3. Add ``experience`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


------------------------
Development Installation
------------------------

To install ckanext-experience for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/ckan/ckanext-experience.git
    cd ckanext-experience
    python setup.py develop
    pip install -r dev-requirements.txt


---
API
---

All actions in the Experience extension are available in the CKAN Action API.

Experience actions::

    - create a new experience (sysadmins and experience admins only)
    curl -X POST http://127.0.0.1:5000/api/3/action/ckanext_showcase_create -H "Authorization:{YOUR-API-KEY}" -d '{"name": "my-new-experience"}'

    - delete a experience (sysadmins and experience admins only)
    curl -X POST http://127.0.0.1:5000/api/3/action/ckanext_showcase_delete -H "Authorization:{YOUR-API-KEY}" -d '{"name": "my-new-experience"}'

    - show a experience
    curl -X POST http://127.0.0.1:5000/api/3/action/ckanext_showcase_show -d '{"id": "my-new-experience"}'

    - list experiences
    curl -X POST http://127.0.0.1:5000/api/3/action/ckanext_showcase_list -d ''


Dataset actions::

    - add a dataset to a experience (sysadmins and experience admins only)
    curl -X POST http://127.0.0.1:5000/api/3/action/ckanext_showcase_package_association_create -H "Authorization:{YOUR-API-KEY}" -d '{"showcase_id": "my-experience", "package_id": "my-package"}'

    - remove a dataset from a experience (sysadmins and experience admins only)
    curl -X POST http://127.0.0.1:5000/api/3/action/ckanext_showcase_package_association_delete -H "Authorization:{YOUR-API-KEY}" -d '{"showcase_id": "my-experience", "package_id": "my-package"}'

    - list datasets in a experience
    curl -X POST http://127.0.0.1:5000/api/3/action/ckanext_showcase_package_list -d '{"showcase_id": "my-experience"}'

    - list experiences featuring a given dataset
    curl -X POST http://127.0.0.1:5000/api/3/action/ckanext_package_showcase_list -d '{"package_id": "my-package"}'


Experience admin actions::

    - add experience admin (sysadmins only)
    curl -X POST http://127.0.0.1:5000/api/3/action/ckanext_showcase_admin_add -H "Authorization:{YOUR-API-KEY}" -d '{"username": "bert"}'

    - remove experience admin (sysadmins only)
    curl -X POST http://127.0.0.1:5000/api/3/action/ckanext_showcase_admin_remove -H "Authorization:{YOUR-API-KEY}" -d '{"username": "bert"}'

    - list experience admins (sysadmins only)
    curl -X POST http://127.0.0.1:5000/api/3/action/ckanext_showcase_admin_list -H "Authorization:{YOUR-API-KEY}" -d ''


----------------------------
Migrating from Related Items
----------------------------

If you already have Related Items in your database, you can use the ``experience
migrate`` command to create Experiences from Related Items.

From the ``ckanext-experience`` directory::

    paster experience migrate -c {path to production.ini}

Note that each Related Item must have a unique title before migration can
proceed. If you prefer resolving duplicates as experiences, you can use the --allow-duplicates
option to migrate them anyways. Duplicate Relations will be created as
'duplicate_' + original_related_title + '_' + related_id

    paster experience migrate -c {path to production.ini} --allow-duplicates

The Related Item property ``type`` will become an Experience tag. The Related Item
properties ``created``, ``owner_id``, ``view_count``, and ``featured`` have no
equivalent in Experiences and will not be migrated.

Related Item data is not removed from the database by this command.

-----------------
Running the Tests
-----------------

To run the tests, do::

    nosetests --ckan --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run::

    nosetests --ckan --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.experience --cover-inclusive --cover-erase --cover-tests


------------------------------------
Registering ckanext-experience on PyPI
------------------------------------

ckanext-experience should be availabe on PyPI as
https://pypi.python.org/pypi/ckanext-experience. If that link doesn't work, then
you can register the project on PyPI for the first time by following these
steps:

1. Create a source distribution of the project::

     python setup.py sdist

2. Register the project::

     python setup.py register

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the first release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.1 then do::

       git tag 0.0.1
       git push --tags


-------------------------------------------
Releasing a New Version of ckanext-experience
-------------------------------------------

ckanext-experience is availabe on PyPI as https://pypi.python.org/pypi/ckanext-experience.
To publish a new version to PyPI follow these steps:

1. Update the version number in the ``setup.py`` file.
   See `PEP 440 <http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers>`_
   for how to choose version numbers.

2. Create a source distribution of the new version::

     python setup.py sdist

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the new release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.2 then do::

       git tag 0.0.2
       git push --tags


-------------------------------------------
i18n
-------------------------------------------

See: "Internationalizing strings in extensions" : http://docs.ckan.org/en/latest/extensions/translating-extensions.html

1. Install babel

       pip install Babel

2. Init Catalog for your language

       python setup.py init_catalog -l es

3. Compile your language catalog ( You can force pybabel compile to compile messages marked as fuzzy with the -f)

       python setup.py compile_catalog -f -l es
