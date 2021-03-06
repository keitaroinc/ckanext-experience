"""
Copyright (c) 2018 Keitaro AB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from nose import tools as nosetools

from ckan.model.package import Package
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


class TestCreateExperience(ExperienceFunctionalTestBase):

    def test_experience_create_no_args(self):
        '''
        Calling experience create without args raises ValidationError.
        '''
        sysadmin = factories.Sysadmin()
        context = {'user': sysadmin['name']}

        # no experiences exist.
        nosetools.assert_equal(model.Session.query(Package)
                               .filter(Package.type == 'experience').count(), 0)

        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_create',
                                context=context)

        # no experiences (dataset of type 'experience') created.
        nosetools.assert_equal(model.Session.query(Package)
                               .filter(Package.type == 'experience').count(), 0)

    def test_experience_create_with_name_arg(self):
        '''
        Calling experience create with a name arg creates a experience package.
        '''
        sysadmin = factories.Sysadmin()
        context = {'user': sysadmin['name']}

        # no experiences exist.
        nosetools.assert_equal(model.Session.query(Package)
                               .filter(Package.type == 'experience').count(), 0)

        helpers.call_action('ckanext_experience_create',
                            context=context, name='my-experience')

        # a experiences (dataset of type 'experience') created.
        nosetools.assert_equal(model.Session.query(Package)
                               .filter(Package.type == 'experience').count(), 1)

    def test_experience_create_with_existing_name(self):
        '''
        Calling experience create with an existing name raises ValidationError.
        '''
        sysadmin = factories.Sysadmin()
        context = {'user': sysadmin['name']}
        factories.Dataset(type='experience', name='my-experience')

        # a single experiences exist.
        nosetools.assert_equal(model.Session.query(Package)
                               .filter(Package.type == 'experience').count(), 1)

        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_create',
                                context=context, name='my-experience')

        # still only one experience exists.
        nosetools.assert_equal(model.Session.query(Package)
                               .filter(Package.type == 'experience').count(), 1)


class TestCreateExperiencePackageAssociation(ExperienceFunctionalTestBase):

    def test_association_create_no_args(self):
        '''
        Calling sc/pkg association create with no args raises
        ValidationError.
        '''
        sysadmin = factories.User(sysadmin=True)
        context = {'user': sysadmin['name']}
        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_package_association_create',
                                context=context)

        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 0)

    def test_association_create_missing_arg(self):
        '''
        Calling sc/pkg association create with a missing arg raises
        ValidationError.
        '''
        sysadmin = factories.User(sysadmin=True)
        package_id = factories.Dataset()['id']

        context = {'user': sysadmin['name']}
        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_package_association_create',
                                context=context, package_id=package_id)

        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 0)

    def test_association_create_by_id(self):
        '''
        Calling sc/pkg association create with correct args (package ids)
        creates an association.
        '''
        sysadmin = factories.User(sysadmin=True)
        package_id = factories.Dataset()['id']
        experience_id = factories.Dataset(type='experience')['id']

        context = {'user': sysadmin['name']}
        association_dict = helpers.call_action('ckanext_experience_package_association_create',
                                               context=context, package_id=package_id,
                                               experience_id=experience_id)

        # One association object created
        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 1)
        # Association properties are correct
        nosetools.assert_equal(association_dict.get('experience_id'), experience_id)
        nosetools.assert_equal(association_dict.get('package_id'), package_id)

    def test_association_create_by_name(self):
        '''
        Calling sc/pkg association create with correct args (package names)
        creates an association.
        '''
        sysadmin = factories.User(sysadmin=True)
        package = factories.Dataset()
        package_name = package['name']
        experience = factories.Dataset(type='experience')
        experience_name = experience['name']

        context = {'user': sysadmin['name']}
        association_dict = helpers.call_action('ckanext_experience_package_association_create',
                                               context=context, package_id=package_name,
                                               experience_id=experience_name)

        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 1)
        nosetools.assert_equal(association_dict.get('experience_id'), experience['id'])
        nosetools.assert_equal(association_dict.get('package_id'), package['id'])

    def test_association_create_existing(self):
        '''
        Attempt to create association with existing details returns Validation
        Error.
        '''
        sysadmin = factories.User(sysadmin=True)
        package_id = factories.Dataset()['id']
        experience_id = factories.Dataset(type='experience')['id']

        context = {'user': sysadmin['name']}
        # Create association
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=package_id,
                            experience_id=experience_id)
        # Attempted duplicate creation results in ValidationError
        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_package_association_create',
                                context=context, package_id=package_id,
                                experience_id=experience_id)


class TestCreateExperienceAdmin(ExperienceFunctionalTestBase):

    def test_experience_admin_add_creates_experience_admin_user(self):
        '''
        Calling ckanext_experience_admin_add adds user to experience admin list.
        '''
        user_to_add = factories.User()

        nosetools.assert_equal(model.Session.query(ExperienceAdmin).count(), 0)

        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user_to_add['name'])

        nosetools.assert_equal(model.Session.query(ExperienceAdmin).count(), 1)
        nosetools.assert_true(user_to_add['id'] in ExperienceAdmin.get_experience_admin_ids())

    def test_experience_admin_add_multiple_users(self):
        '''
        Calling ckanext_experience_admin_add for multiple users correctly adds
        them to experience admin list.
        '''
        user_to_add = factories.User()
        second_user_to_add = factories.User()

        nosetools.assert_equal(model.Session.query(ExperienceAdmin).count(), 0)

        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user_to_add['name'])

        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=second_user_to_add['name'])

        nosetools.assert_equal(model.Session.query(ExperienceAdmin).count(), 2)
        nosetools.assert_true(user_to_add['id'] in ExperienceAdmin.get_experience_admin_ids())
        nosetools.assert_true(second_user_to_add['id'] in ExperienceAdmin.get_experience_admin_ids())

    def test_experience_admin_add_existing_user(self):
        '''
        Calling ckanext_experience_admin_add twice for same user raises a
        ValidationError.
        '''
        user_to_add = factories.User()

        # Add once
        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user_to_add['name'])

        nosetools.assert_equal(model.Session.query(ExperienceAdmin).count(), 1)

        # Attempt second add
        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_admin_add', context={},
                                username=user_to_add['name'])

        # Still only one ExperienceAdmin object.
        nosetools.assert_equal(model.Session.query(ExperienceAdmin).count(), 1)

    def test_experience_admin_add_username_doesnot_exist(self):
        '''
        Calling ckanext_experience_admin_add with non-existent username raises
        ValidationError and no ExperienceAdmin object is created.
        '''
        nosetools.assert_raises(toolkit.ObjectNotFound, helpers.call_action,
                                'ckanext_experience_admin_add', context={},
                                username='missing')

        nosetools.assert_equal(model.Session.query(ExperienceAdmin).count(), 0)
        nosetools.assert_equal(ExperienceAdmin.get_experience_admin_ids(), [])

    def test_experience_admin_add_no_args(self):
        '''
        Calling ckanext_experience_admin_add with no args raises ValidationError
        and no ExperienceAdmin object is created.
        '''
        nosetools.assert_raises(toolkit.ValidationError, helpers.call_action,
                                'ckanext_experience_admin_add', context={})

        nosetools.assert_equal(model.Session.query(ExperienceAdmin).count(), 0)
        nosetools.assert_equal(ExperienceAdmin.get_experience_admin_ids(), [])
