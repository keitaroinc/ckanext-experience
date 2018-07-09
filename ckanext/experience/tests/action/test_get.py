from nose import tools as nosetools
from nose import SkipTest

import ckan.plugins.toolkit as toolkit
try:
    import ckan.tests.factories as factories
except ImportError:  # for ckan <= 2.3
    import ckan.new_tests.factories as factories

try:
    import ckan.tests.helpers as helpers
except ImportError:  # for ckan <= 2.3
    import ckan.new_tests.helpers as helpers

from ckanext.experience.tests import ExperienceFunctionalTestBase


class TestExperienceShow(ExperienceFunctionalTestBase):

    def test_experience_show_no_args(self):
        '''
        Calling experience show with no args raises a ValidationError.
        '''
        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_show')

    def test_experience_show_with_id(self):
        '''
        Calling experience show with id arg returns experience dict.
        '''
        my_experience = factories.Dataset(type='experience', name='my-experience')

        experience_shown = helpers.call_action('ckanext_experience_show', id=my_experience['id'])

        nosetools.assert_equal(my_experience['name'], experience_shown['name'])

    def test_experience_show_with_name(self):
        '''
        Calling experience show with name arg returns experience dict.
        '''
        my_experience = factories.Dataset(type='experience', name='my-experience')

        experience_shown = helpers.call_action('ckanext_experience_show', id=my_experience['name'])

        nosetools.assert_equal(my_experience['id'], experience_shown['id'])

    def test_experience_show_with_nonexisting_name(self):
        '''
        Calling experience show with bad name arg returns ObjectNotFound.
        '''
        factories.Dataset(type='experience', name='my-experience')

        nosetools.assert_raises(toolkit.ObjectNotFound, helpers.call_action,
                                'ckanext_experience_show', id='my-bad-name')

    def test_experience_show_num_datasets_added(self):
        '''
        num_datasets property returned with experience dict.
        '''
        my_experience = factories.Dataset(type='experience', name='my-experience')

        experience_shown = helpers.call_action('ckanext_experience_show', id=my_experience['name'])

        nosetools.assert_true('num_datasets' in experience_shown)
        nosetools.assert_equal(experience_shown['num_datasets'], 0)

    def test_experience_show_num_datasets_correct_value(self):
        '''
        num_datasets property has correct value.
        '''

        sysadmin = factories.User(sysadmin=True)

        my_experience = factories.Dataset(type='experience', name='my-experience')
        package_one = factories.Dataset()
        package_two = factories.Dataset()

        context = {'user': sysadmin['name']}
        # create an association
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package_one['id'],
                            experience_id=my_experience['id'])
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package_two['id'],
                            experience_id=my_experience['id'])

        experience_shown = helpers.call_action('ckanext_experience_show', id=my_experience['name'])

        nosetools.assert_equal(experience_shown['num_datasets'], 2)

    def test_experience_show_num_datasets_correct_only_count_active_datasets(self):
        '''
        num_datasets property has correct value when some previously
        associated datasets have been datasets.
        '''
        sysadmin = factories.User(sysadmin=True)

        my_experience = factories.Dataset(type='experience', name='my-experience')
        package_one = factories.Dataset()
        package_two = factories.Dataset()
        package_three = factories.Dataset()

        context = {'user': sysadmin['name']}
        # create the associations
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package_one['id'],
                            experience_id=my_experience['id'])
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package_two['id'],
                            experience_id=my_experience['id'])
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package_three['id'],
                            experience_id=my_experience['id'])

        # delete the first package
        helpers.call_action('package_delete', context=context, id=package_one['id'])

        experience_shown = helpers.call_action('ckanext_experience_show', id=my_experience['name'])

        # the num_datasets should only include active datasets
        nosetools.assert_equal(experience_shown['num_datasets'], 2)

    def test_experience_anon_user_can_see_package_list_when_experience_association_was_deleted(self):
        '''
        When a experience is deleted, the remaining associations with formerly associated
        packages or experiences can still be displayed.
        '''
        app = self._get_test_app()

        sysadmin = factories.User(sysadmin=True)

        experience_one = factories.Dataset(type='experience', name='experience-one')
        experience_two = factories.Dataset(type='experience', name='experience-two')
        package_one = factories.Dataset()
        package_two = factories.Dataset()

        admin_context = {'user': sysadmin['name']}

        # create the associations
        helpers.call_action('ckanext_experience_package_association_create',
                            context=admin_context, package_id=package_one['id'],
                            experience_id=experience_one['id'])
        helpers.call_action('ckanext_experience_package_association_create',
                            context=admin_context, package_id=package_one['id'],
                            experience_id=experience_two['id'])
        helpers.call_action('ckanext_experience_package_association_create',
                            context=admin_context, package_id=package_two['id'],
                            experience_id=experience_one['id'])
        helpers.call_action('ckanext_experience_package_association_create',
                            context=admin_context, package_id=package_two['id'],
                            experience_id=experience_two['id'])

        # delete one of the associated experiences
        helpers.call_action('package_delete', context=admin_context,
                            id=experience_two['id'])

        # the anon user can still see the associated packages of remaining experience
        associated_packages = helpers.call_action(
            'ckanext_experience_package_list',
            experience_id=experience_one['id'])

        nosetools.assert_equal(len(associated_packages), 2)

        # overview of packages can still be seen
        app.get("/dataset", status=200)


class TestExperienceList(ExperienceFunctionalTestBase):

    def test_experience_list(self):
        '''Experience list action returns names of experiences in site.'''

        experience_one = factories.Dataset(type='experience')
        experience_two = factories.Dataset(type='experience')
        experience_three = factories.Dataset(type='experience')

        experience_list = helpers.call_action('ckanext_experience_list')

        experience_list_name_id = [(sc['name'], sc['id']) for sc in experience_list]

        nosetools.assert_equal(len(experience_list), 3)
        nosetools.assert_true(sorted(experience_list_name_id) ==
                              sorted([(experience['name'], experience['id'])
                                     for experience in [experience_one,
                                                      experience_two,
                                                      experience_three]]))

    def test_experience_list_no_datasets(self):
        '''
        Experience list action doesn't return normal datasets (of type
        'dataset').
        '''
        experience_one = factories.Dataset(type='experience')
        dataset_one = factories.Dataset()
        dataset_two = factories.Dataset()

        experience_list = helpers.call_action('ckanext_experience_list')

        experience_list_name_id = [(sc['name'], sc['id']) for sc in experience_list]

        nosetools.assert_equal(len(experience_list), 1)
        nosetools.assert_true((experience_one['name'], experience_one['id']) in experience_list_name_id)
        nosetools.assert_true((dataset_one['name'], dataset_one['id']) not in experience_list_name_id)
        nosetools.assert_true((dataset_two['name'], dataset_two['id']) not in experience_list_name_id)


class TestExperiencePackageList(ExperienceFunctionalTestBase):

    '''Tests for ckanext_experience_package_list'''

    def test_experience_package_list_no_packages(self):
        '''
        Calling ckanext_experience_package_list with a experience that has no
        packages returns an empty list.
        '''
        experience_id = factories.Dataset(type='experience')['id']

        pkg_list = helpers.call_action('ckanext_experience_package_list',
                                       experience_id=experience_id)

        nosetools.assert_equal(pkg_list, [])

    def test_experience_package_list_works_with_name(self):
        '''
        Calling ckanext_experience_package_list with a experience name doesn't
        raise a ValidationError.
        '''
        experience_name = factories.Dataset(type='experience')['name']

        pkg_list = helpers.call_action('ckanext_experience_package_list',
                                       experience_id=experience_name)

        nosetools.assert_equal(pkg_list, [])

    def test_experience_package_list_wrong_experience_id(self):
        '''
        Calling ckanext_experience_package_list with a bad experience id raises a
        ValidationError.
        '''
        factories.Dataset(type='experience')['id']

        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_package_list',
                                experience_id='a-bad-id')

    def test_experience_package_list_experience_has_package(self):
        '''
        Calling ckanext_experience_package_list with a experience that has a
        package should return that package.
        '''
        sysadmin = factories.User(sysadmin=True)

        package = factories.Dataset()
        experience_id = factories.Dataset(type='experience')['id']
        context = {'user': sysadmin['name']}
        # create an association
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package['id'],
                            experience_id=experience_id)

        pkg_list = helpers.call_action('ckanext_experience_package_list',
                                       experience_id=experience_id)

        # We've got an item in the pkg_list
        nosetools.assert_equal(len(pkg_list), 1)
        # The list item should have the correct name property
        nosetools.assert_equal(pkg_list[0]['name'], package['name'])

    def test_experience_package_list_experience_has_two_packages(self):
        '''
        Calling ckanext_experience_package_list with a experience that has two
        packages should return the packages.
        '''
        sysadmin = factories.User(sysadmin=True)

        package_one = factories.Dataset()
        package_two = factories.Dataset()
        experience_id = factories.Dataset(type='experience')['id']
        context = {'user': sysadmin['name']}
        # create first association
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package_one['id'],
                            experience_id=experience_id)
        # create second association
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package_two['id'],
                            experience_id=experience_id)

        pkg_list = helpers.call_action('ckanext_experience_package_list',
                                       experience_id=experience_id)

        # We've got two items in the pkg_list
        nosetools.assert_equal(len(pkg_list), 2)

    def test_experience_package_list_experience_only_contains_active_datasets(self):
        '''
        Calling ckanext_experience_package_list will only return active datasets
        (not deleted ones).
        '''
        sysadmin = factories.User(sysadmin=True)

        package_one = factories.Dataset()
        package_two = factories.Dataset()
        package_three = factories.Dataset()
        experience_id = factories.Dataset(type='experience')['id']
        context = {'user': sysadmin['name']}
        # create first association
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package_one['id'],
                            experience_id=experience_id)
        # create second association
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package_two['id'],
                            experience_id=experience_id)
        # create third association
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package_three['id'],
                            experience_id=experience_id)

        # delete the first package
        helpers.call_action('package_delete', context=context, id=package_one['id'])

        pkg_list = helpers.call_action('ckanext_experience_package_list',
                                       experience_id=experience_id)

        # We've got two items in the pkg_list
        nosetools.assert_equal(len(pkg_list), 2)

        pkg_list_ids = [pkg['id'] for pkg in pkg_list]
        nosetools.assert_true(package_two['id'] in pkg_list_ids)
        nosetools.assert_true(package_three['id'] in pkg_list_ids)
        nosetools.assert_false(package_one['id'] in pkg_list_ids)

    def test_experience_package_list_package_isnot_a_experience(self):
        '''
        Calling ckanext_experience_package_list with a package id should raise a
        ValidationError.

        Since Experiences are Packages under the hood, make sure we treat them
        differently.
        '''
        sysadmin = factories.User(sysadmin=True)

        package = factories.Dataset()
        experience_id = factories.Dataset(type='experience')['id']
        context = {'user': sysadmin['name']}
        # create an association
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package['id'],
                            experience_id=experience_id)

        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_package_list',
                                experience_id=package['id'])


class TestPackageExperienceList(ExperienceFunctionalTestBase):

    '''Tests for ckanext_package_experience_list'''

    def test_package_experience_list_no_experiences(self):
        '''
        Calling ckanext_package_experience_list with a package that has no
        experiences returns an empty list.
        '''
        package_id = factories.Dataset()['id']

        experience_list = helpers.call_action('ckanext_package_experience_list',
                                            package_id=package_id)

        nosetools.assert_equal(experience_list, [])

    def test_package_experience_list_works_with_name(self):
        '''
        Calling ckanext_package_experience_list with a package name doesn't
        raise a ValidationError.
        '''
        package_name = factories.Dataset()['name']

        experience_list = helpers.call_action('ckanext_package_experience_list',
                                            package_id=package_name)

        nosetools.assert_equal(experience_list, [])

    def test_package_experience_list_wrong_experience_id(self):
        '''
        Calling ckanext_package_experience_list with a bad package id raises a
        ValidationError.
        '''
        factories.Dataset()['id']

        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_package_experience_list',
                                experience_id='a-bad-id')

    def test_package_experience_list_experience_has_package(self):
        '''
        Calling ckanext_package_experience_list with a package that has a
        experience should return that experience.
        '''
        sysadmin = factories.User(sysadmin=True)

        package = factories.Dataset()
        experience = factories.Dataset(type='experience')
        context = {'user': sysadmin['name']}
        # create an association
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package['id'],
                            experience_id=experience['id'])

        experience_list = helpers.call_action('ckanext_package_experience_list',
                                            package_id=package['id'])

        # We've got an item in the experience_list
        nosetools.assert_equal(len(experience_list), 1)
        # The list item should have the correct name property
        nosetools.assert_equal(experience_list[0]['name'], experience['name'])

    def test_package_experience_list_experience_has_two_packages(self):
        '''
        Calling ckanext_package_experience_list with a package that has two
        experiences should return the experiences.
        '''
        sysadmin = factories.User(sysadmin=True)

        package = factories.Dataset()
        experience_one = factories.Dataset(type='experience')
        experience_two = factories.Dataset(type='experience')
        context = {'user': sysadmin['name']}
        # create first association
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package['id'],
                            experience_id=experience_one['id'])
        # create second association
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package['id'],
                            experience_id=experience_two['id'])

        experience_list = helpers.call_action('ckanext_package_experience_list',
                                            package_id=package['id'])

        # We've got two items in the experience_list
        nosetools.assert_equal(len(experience_list), 2)

    def test_package_experience_list_package_isnot_a_experience(self):
        '''
        Calling ckanext_package_experience_list with a experience id should raise a
        ValidationError.

        Since Experiences are Packages under the hood, make sure we treat them
        differently.
        '''
        sysadmin = factories.User(sysadmin=True)

        package = factories.Dataset()
        experience = factories.Dataset(type='experience')
        context = {'user': sysadmin['name']}
        # create an association
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package['id'],
                            experience_id=experience['id'])

        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_package_experience_list',
                                package_id=experience['id'])


class TestExperienceAdminList(ExperienceFunctionalTestBase):

    '''Tests for ckanext_experience_admin_list'''

    def test_experience_admin_list_no_experience_admins(self):
        '''
        Calling ckanext_experience_admin_list on a site that has no experiences
        admins returns an empty list.
        '''

        experience_admin_list = helpers.call_action('ckanext_experience_admin_list')

        nosetools.assert_equal(experience_admin_list, [])

    def test_experience_admin_list_users(self):
        '''
        Calling ckanext_experience_admin_list will return users who are experience
        admins.
        '''
        user_one = factories.User()
        user_two = factories.User()
        user_three = factories.User()

        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user_one['name'])
        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user_two['name'])
        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user_three['name'])

        experience_admin_list = helpers.call_action('ckanext_experience_admin_list', context={})

        nosetools.assert_equal(len(experience_admin_list), 3)
        for user in [user_one, user_two, user_three]:
            nosetools.assert_true({'name': user['name'], 'id': user['id']} in experience_admin_list)

    def test_experience_admin_only_lists_admin_users(self):
        '''
        Calling ckanext_experience_admin_list will only return users who are
        experience admins.
        '''
        user_one = factories.User()
        user_two = factories.User()
        user_three = factories.User()

        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user_one['name'])
        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user_two['name'])

        experience_admin_list = helpers.call_action('ckanext_experience_admin_list', context={})

        nosetools.assert_equal(len(experience_admin_list), 2)
        # user three isn't in list
        nosetools.assert_true({'name': user_three['name'], 'id': user_three['id']} not in experience_admin_list)


class TestPackageSearchBeforeSearch(ExperienceFunctionalTestBase):

    '''
    Extension uses the `before_search` method to alter search parameters.
    '''

    def test_package_search_no_additional_filters(self):
        '''
        Perform package_search with no additional filters should not include
        experiences.
        '''
        factories.Dataset()
        factories.Dataset()
        factories.Dataset(type='experience')
        factories.Dataset(type='custom')

        search_results = helpers.call_action('package_search', context={})['results']

        types = [result['type'] for result in search_results]

        nosetools.assert_equal(len(search_results), 3)
        nosetools.assert_true('experience' not in types)
        nosetools.assert_true('custom' in types)

    def test_package_search_filter_include_experience(self):
        '''
        package_search filtered to include datasets of type experience should
        only include experiences.
        '''
        factories.Dataset()
        factories.Dataset()
        factories.Dataset(type='experience')
        factories.Dataset(type='custom')

        search_results = helpers.call_action('package_search', context={},
                                             fq='dataset_type:experience')['results']

        types = [result['type'] for result in search_results]

        nosetools.assert_equal(len(search_results), 1)
        nosetools.assert_true('experience' in types)
        nosetools.assert_true('custom' not in types)
        nosetools.assert_true('dataset' not in types)


class TestUserShowBeforeSearch(ExperienceFunctionalTestBase):

    '''
    Extension uses the `before_search` method to alter results of user_show
    (via package_search).
    '''

    def test_user_show_no_additional_filters(self):
        '''
        Perform package_search with no additional filters should not include
        experiences.
        '''
        if not toolkit.check_ckan_version(min_version='2.4'):
            raise SkipTest('Filtering out experiences requires CKAN 2.4+ (ckan/ckan/issues/2380)')

        user = factories.User()
        factories.Dataset(user=user)
        factories.Dataset(user=user)
        factories.Dataset(user=user, type='experience')
        factories.Dataset(user=user, type='custom')

        search_results = helpers.call_action('user_show', context={},
                                             include_datasets=True,
                                             id=user['name'])['datasets']

        types = [result['type'] for result in search_results]

        nosetools.assert_equal(len(search_results), 3)
        nosetools.assert_true('experience' not in types)
        nosetools.assert_true('custom' in types)
