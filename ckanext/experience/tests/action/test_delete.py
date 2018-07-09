from nose import tools as nosetools

import ckan.model as model
import ckan.plugins.toolkit as toolkit
try:
    import ckan.tests.factories as factories
except ImportError:  # for ckan <= 2.3
    import ckan.new_tests.factories as factories

try:
    import ckan.tests.helpers as helpers
except ImportError:  # for ckan <= 2.3
    import ckan.new_tests.helpers as helpers

from ckanext.experience.model import ExperiencePackageAssociation, ExperienceAdmin
from ckanext.experience.tests import ExperienceFunctionalTestBase
from ckan.model.package import Package


class TestDeleteExperience(ExperienceFunctionalTestBase):

    def test_experience_delete_no_args(self):
        '''
        Calling experience delete with no args raises a ValidationError.
        '''
        sysadmin = factories.Sysadmin()
        context = {'user': sysadmin['name']}
        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_delete', context=context)

    def test_experience_delete_incorrect_args(self):
        '''
        Calling experience delete with incorrect args raises ObjectNotFound.
        '''
        sysadmin = factories.Sysadmin()
        context = {'user': sysadmin['name']}
        factories.Dataset(type='experience')
        nosetools.assert_raises(toolkit.ObjectNotFound, helpers.call_action,
                                'ckanext_experience_delete', context=context,
                                id='blah-blah')

    def test_experience_delete_by_id(self):
        '''
        Calling experience delete with experience id.
        '''
        sysadmin = factories.Sysadmin()
        context = {'user': sysadmin['name']}
        experience = factories.Dataset(type='experience')

        # One experience object created
        nosetools.assert_equal(model.Session.query(Package)
                               .filter(Package.type == 'experience').count(), 1)

        helpers.call_action('ckanext_experience_delete',
                            context=context, id=experience['id'])

        nosetools.assert_equal(model.Session.query(Package)
                               .filter(Package.type == 'experience').count(), 0)

    def test_experience_delete_by_name(self):
        '''
        Calling experience delete with experience name.
        '''
        sysadmin = factories.Sysadmin()
        context = {'user': sysadmin['name']}
        experience = factories.Dataset(type='experience')

        # One experience object created
        nosetools.assert_equal(model.Session.query(Package)
                               .filter(Package.type == 'experience').count(), 1)

        helpers.call_action('ckanext_experience_delete',
                            context=context, id=experience['name'])

        nosetools.assert_equal(model.Session.query(Package)
                               .filter(Package.type == 'experience').count(), 0)

    def test_experience_delete_removes_associations(self):
        '''
        Deleting a experience also deletes associated ExperiencePackageAssociation
        objects.
        '''
        sysadmin = factories.Sysadmin()
        context = {'user': sysadmin['name']}
        experience = factories.Dataset(type='experience', name='my-experience')
        dataset_one = factories.Dataset(name='dataset-one')
        dataset_two = factories.Dataset(name='dataset-two')

        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=dataset_one['id'],
                            experience_id=experience['id'])
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=dataset_two['id'],
                            experience_id=experience['id'])

        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 2)

        helpers.call_action('ckanext_experience_delete',
                            context=context, id=experience['id'])

        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 0)


class TestDeletePackage(ExperienceFunctionalTestBase):

    def test_package_delete_retains_associations(self):
        '''
        Deleting a package (setting its status to 'delete') retains associated
        ExperiencePackageAssociation objects.
        '''
        sysadmin = factories.Sysadmin()
        context = {'user': sysadmin['name']}
        experience = factories.Dataset(type='experience', name='my-experience')
        dataset_one = factories.Dataset(name='dataset-one')
        dataset_two = factories.Dataset(name='dataset-two')

        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=dataset_one['id'],
                            experience_id=experience['id'])
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=dataset_two['id'],
                            experience_id=experience['id'])

        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 2)

        # delete the first package, should also delete the
        # ExperiencePackageAssociation associated with it.
        helpers.call_action('package_delete',
                            context=context, id=dataset_one['id'])

        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 2)

    def test_package_purge_deletes_associations(self):
        '''
        Purging a package (actually deleting it from the database) deletes
        associated ExperiencePackageAssociation objects.
        '''
        sysadmin = factories.Sysadmin()
        context = {'user': sysadmin['name']}
        experience = factories.Dataset(type='experience', name='my-experience')
        dataset_one = factories.Dataset(name='dataset-one')
        dataset_two = factories.Dataset(name='dataset-two')

        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=dataset_one['id'],
                            experience_id=experience['id'])
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=dataset_two['id'],
                            experience_id=experience['id'])

        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 2)

        # purge the first package, should also delete the
        # ExperiencePackageAssociation associated with it.
        pkg = model.Session.query(model.Package).get(dataset_one['id'])
        pkg.purge()
        model.repo.commit_and_remove()

        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 1)


class TestDeleteExperiencePackageAssociation(ExperienceFunctionalTestBase):

    def test_association_delete_no_args(self):
        '''
        Calling sc/pkg association delete with no args raises ValidationError.
        '''
        sysadmin = factories.User(sysadmin=True)
        context = {'user': sysadmin['name']}
        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_package_association_delete',
                                context=context)

    def test_association_delete_missing_arg(self):
        '''
        Calling sc/pkg association delete with a missing arg raises
        ValidationError.
        '''
        sysadmin = factories.User(sysadmin=True)
        package_id = factories.Dataset()['id']

        context = {'user': sysadmin['name']}
        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_package_association_delete',
                                context=context, package_id=package_id)

    def test_association_delete_by_id(self):
        '''
        Calling sc/pkg association delete with correct args (package ids)
        correctly deletes an association.
        '''
        sysadmin = factories.User(sysadmin=True)
        package_id = factories.Dataset()['id']
        experience_id = factories.Dataset(type='experience')['id']

        context = {'user': sysadmin['name']}
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package_id,
                            experience_id=experience_id)

        # One association object created
        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 1)

        helpers.call_action('ckanext_experience_package_association_delete',
                            context=context, package_id=package_id,
                            experience_id=experience_id)

    def test_association_delete_attempt_with_non_existent_association(self):
        '''
        Attempting to delete a non-existent association (package ids exist,
        but aren't associated with each other), will cause a NotFound error.
        '''
        sysadmin = factories.User(sysadmin=True)
        package_id = factories.Dataset()['id']
        experience_id = factories.Dataset(type='experience')['id']

        # No existing associations
        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 0)

        context = {'user': sysadmin['name']}
        nosetools.assert_raises(toolkit.ObjectNotFound, helpers.call_action,
                                'ckanext_experience_package_association_delete',
                                context=context, package_id=package_id,
                                experience_id=experience_id)

    def test_association_delete_attempt_with_bad_package_ids(self):
        '''
        Attempting to delete an association by passing non-existent package
        ids will cause a ValidationError.
        '''
        sysadmin = factories.User(sysadmin=True)

        # No existing associations
        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 0)

        context = {'user': sysadmin['name']}
        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_package_association_delete',
                                context=context, package_id="my-bad-package-id",
                                experience_id="my-bad-experience-id")

    def test_association_delete_retains_packages(self):
        '''
        Deleting a sc/pkg association doesn't delete the associated packages.
        '''
        sysadmin = factories.User(sysadmin=True)
        package_id = factories.Dataset()['id']
        experience_id = factories.Dataset(type='experience')['id']

        context = {'user': sysadmin['name']}
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package_id,
                            experience_id=experience_id)

        helpers.call_action('ckanext_experience_package_association_delete',
                            context=context, package_id=package_id,
                            experience_id=experience_id)

        # package still exist
        nosetools.assert_equal(model.Session.query(Package)
                               .filter(Package.type == 'dataset').count(), 1)

        # experience still exist
        nosetools.assert_equal(model.Session.query(Package)
                               .filter(Package.type == 'experience').count(), 1)


class TestRemoveExperienceAdmin(ExperienceFunctionalTestBase):

    def test_experience_admin_remove_deletes_experience_admin_user(self):
        '''
        Calling ckanext_experience_admin_remove deletes ExperienceAdmin object.
        '''
        user = factories.User()

        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user['name'])

        # There's an ExperienceAdmin obj
        nosetools.assert_equal(model.Session.query(ExperienceAdmin).count(), 1)

        helpers.call_action('ckanext_experience_admin_remove', context={},
                            username=user['name'])

        # There's no ExperienceAdmin obj
        nosetools.assert_equal(model.Session.query(ExperienceAdmin).count(), 0)
        nosetools.assert_equal(ExperienceAdmin.get_experience_admin_ids(), [])

    def test_experience_admin_delete_user_removes_experience_admin_object(self):
        '''
        Deleting a user also deletes the corresponding ExperienceAdmin object.
        '''
        user = factories.User()

        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user['name'])

        # There's an ExperienceAdmin object
        nosetools.assert_equal(model.Session.query(ExperienceAdmin).count(), 1)
        nosetools.assert_true(user['id'] in ExperienceAdmin.get_experience_admin_ids())

        # purge the user, should also delete the ExperienceAdmin object
        # associated with it.
        user_obj = model.Session.query(model.User).get(user['id'])
        user_obj.purge()
        model.repo.commit_and_remove()

        # The ExperienceAdmin has also been removed
        nosetools.assert_equal(model.Session.query(ExperienceAdmin).count(), 0)
        nosetools.assert_equal(ExperienceAdmin.get_experience_admin_ids(), [])

    def test_experience_admin_remove_retains_user(self):
        '''
        Deleting an ExperienceAdmin object doesn't delete the corresponding user.
        '''

        user = factories.User()

        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user['name'])

        # We have a user
        user_obj = model.Session.query(model.User).get(user['id'])
        nosetools.assert_true(user_obj is not None)

        helpers.call_action('ckanext_experience_admin_remove', context={},
                            username=user['name'])

        # We still have a user
        user_obj = model.Session.query(model.User).get(user['id'])
        nosetools.assert_true(user_obj is not None)

    def test_experience_admin_remove_with_bad_username(self):
        '''
        Calling experience admin remove with a non-existent user raises
        ValidationError.
        '''

        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_admin_remove', context={},
                                username='no-one-here')

    def test_experience_admin_remove_with_no_args(self):
        '''
        Calling experience admin remove with no arg raises ValidationError.
        '''

        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_admin_remove', context={})
