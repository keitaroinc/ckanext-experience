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

import json
from nose import tools as nosetools

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


class TestExperienceAuthIndex(ExperienceFunctionalTestBase):

    def test_auth_anon_user_can_view_experience_index(self):
        '''An anon (not logged in) user can view the Experiences index.'''
        app = self._get_test_app()

        app.get("/experience", status=200)

    def test_auth_logged_in_user_can_view_experience_index(self):
        '''
        A logged in user can view the Experience index.
        '''
        app = self._get_test_app()

        user = factories.User()

        app.get("/experience", status=200,
                extra_environ={'REMOTE_USER': str(user["name"])})

    def test_auth_anon_user_cant_see_add_experience_button(self):
        '''
        An anon (not logged in) user can't see the Add Experience button on the
        experience index page.
        '''
        app = self._get_test_app()

        response = app.get("/experience", status=200)

        # test for new experience link in response
        response.mustcontain(no="/experience/new")

    def test_auth_logged_in_user_cant_see_add_experience_button(self):
        '''
        A logged in user can't see the Add Experience button on the experience
        index page.
        '''
        app = self._get_test_app()
        user = factories.User()

        response = app.get("/experience", status=200,
                           extra_environ={'REMOTE_USER': str(user['name'])})

        # test for new experience link in response
        response.mustcontain(no="/experience/new")

    def test_auth_sysadmin_can_see_add_experience_button(self):
        '''
        A sysadmin can see the Add Experience button on the experience index
        page.
        '''
        app = self._get_test_app()
        user = factories.Sysadmin()

        response = app.get("/experience", status=200,
                           extra_environ={'REMOTE_USER': str(user['name'])})

        # test for new experience link in response
        response.mustcontain("/experience/new")


class TestExperienceAuthDetails(ExperienceFunctionalTestBase):
    def test_auth_anon_user_can_view_experience_details(self):
        '''
        An anon (not logged in) user can view an individual Experience details page.
        '''
        app = self._get_test_app()

        factories.Dataset(type='experience', name='my-experience')

        app.get('/experience/my-experience', status=200)

    def test_auth_logged_in_user_can_view_experience_details(self):
        '''
        A logged in user can view an individual Experience details page.
        '''
        app = self._get_test_app()
        user = factories.User()

        factories.Dataset(type='experience', name='my-experience')

        app.get('/experience/my-experience', status=200,
                extra_environ={'REMOTE_USER': str(user['name'])})

    def test_auth_anon_user_cant_see_manage_button(self):
        '''
        An anon (not logged in) user can't see the Manage button on an individual
        experience details page.
        '''
        app = self._get_test_app()

        factories.Dataset(type='experience', name='my-experience')

        response = app.get('/experience/my-experience', status=200)

        # test for url to edit page
        response.mustcontain(no="/experience/edit/my-experience")

    def test_auth_logged_in_user_can_see_manage_button(self):
        '''
        A logged in user can't see the Manage button on an individual experience
        details page.
        '''
        app = self._get_test_app()
        user = factories.User()

        factories.Dataset(type='experience', name='my-experience')

        response = app.get('/experience/my-experience', status=200,
                           extra_environ={'REMOTE_USER': str(user['name'])})

        # test for url to edit page
        response.mustcontain(no="/experience/edit/my-experience")

    def test_auth_sysadmin_can_see_manage_button(self):
        '''
        A sysadmin can see the Manage button on an individual experience details
        page.
        '''
        app = self._get_test_app()
        user = factories.Sysadmin()

        factories.Dataset(type='experience', name='my-experience')

        response = app.get('/experience/my-experience', status=200,
                           extra_environ={'REMOTE_USER': str(user['name'])})

        # test for url to edit page
        response.mustcontain("/experience/edit/my-experience")

    def test_auth_experience_show_anon_can_access(self):
        '''
        Anon user can request experience show.
        '''
        app = self._get_test_app()

        factories.Dataset(type='experience', name='my-experience')

        response = app.get('/api/3/action/ckanext_experience_show?id=my-experience',
                           status=200)

        json_response = json.loads(response.body)

        nosetools.assert_true(json_response['success'])

    def test_auth_experience_show_normal_user_can_access(self):
        '''
        Normal logged in user can request experience show.
        '''
        user = factories.User()
        app = self._get_test_app()

        factories.Dataset(type='experience', name='my-experience')

        response = app.get('/api/3/action/ckanext_experience_show?id=my-experience',
                           status=200, extra_environ={'REMOTE_USER': str(user['name'])})

        json_response = json.loads(response.body)

        nosetools.assert_true(json_response['success'])

    def test_auth_experience_show_sysadmin_can_access(self):
        '''
        Normal logged in user can request experience show.
        '''
        user = factories.Sysadmin()
        app = self._get_test_app()

        factories.Dataset(type='experience', name='my-experience')

        response = app.get('/api/3/action/ckanext_experience_show?id=my-experience',
                           status=200, extra_environ={'REMOTE_USER': str(user['name'])})

        json_response = json.loads(response.body)

        nosetools.assert_true(json_response['success'])


class TestExperienceAuthCreate(ExperienceFunctionalTestBase):

    def test_auth_anon_user_cant_view_create_experience(self):
        '''
        An anon (not logged in) user can't access the create experience page.
        '''
        app = self._get_test_app()
        app.get("/experience/new", status=302)

    def test_auth_logged_in_user_cant_view_create_experience_page(self):
        '''
        A logged in user can't access the create experience page.
        '''
        app = self._get_test_app()
        user = factories.User()
        app.get("/experience/new", status=401,
                extra_environ={'REMOTE_USER': str(user['name'])})

    def test_auth_sysadmin_can_view_create_experience_page(self):
        '''
        A sysadmin can access the create experience page.
        '''
        app = self._get_test_app()
        user = factories.Sysadmin()
        app.get("/experience/new", status=200,
                extra_environ={'REMOTE_USER': str(user['name'])})


class TestExperienceAuthList(ExperienceFunctionalTestBase):

    def test_auth_experience_list_anon_can_access(self):
        '''
        Anon user can request experience list.
        '''
        app = self._get_test_app()

        factories.Dataset(type='experience', name='my-experience')

        response = app.get('/api/3/action/ckanext_experience_list',
                           status=200)

        json_response = json.loads(response.body)

        nosetools.assert_true(json_response['success'])

    def test_auth_experience_list_normal_user_can_access(self):
        '''
        Normal logged in user can request experience list.
        '''
        user = factories.User()
        app = self._get_test_app()

        factories.Dataset(type='experience', name='my-experience')

        response = app.get('/api/3/action/ckanext_experience_list',
                           status=200, extra_environ={'REMOTE_USER': str(user['name'])})

        json_response = json.loads(response.body)

        nosetools.assert_true(json_response['success'])

    def test_auth_experience_list_sysadmin_can_access(self):
        '''
        Normal logged in user can request experience list.
        '''
        user = factories.Sysadmin()
        app = self._get_test_app()

        factories.Dataset(type='experience', name='my-experience')

        response = app.get('/api/3/action/ckanext_experience_list',
                           status=200, extra_environ={'REMOTE_USER': str(user['name'])})

        json_response = json.loads(response.body)

        nosetools.assert_true(json_response['success'])


class TestExperienceAuthEdit(ExperienceFunctionalTestBase):

    def test_auth_anon_user_cant_view_edit_experience_page(self):
        '''
        An anon (not logged in) user can't access the experience edit page.
        '''
        app = self._get_test_app()

        factories.Dataset(type='experience', name='my-experience')

        app.get('/experience/edit/my-experience', status=302)

    def test_auth_logged_in_user_cant_view_edit_experience_page(self):
        '''
        A logged in user can't access the experience edit page.
        '''
        app = self._get_test_app()
        user = factories.User()

        factories.Dataset(type='experience', name='my-experience')

        app.get('/experience/edit/my-experience', status=401,
                extra_environ={'REMOTE_USER': str(user['name'])})

    def test_auth_sysadmin_can_view_edit_experience_page(self):
        '''
        A sysadmin can access the experience edit page.
        '''
        app = self._get_test_app()
        user = factories.Sysadmin()

        factories.Dataset(type='experience', name='my-experience')

        app.get('/experience/edit/my-experience', status=200,
                extra_environ={'REMOTE_USER': str(user['name'])})

    def test_auth_experience_admin_can_view_edit_experience_page(self):
        '''
        A experience admin can access the experience edit page.
        '''
        app = self._get_test_app()
        user = factories.User()

        # Make user a experience admin
        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user['name'])

        factories.Dataset(type='experience', name='my-experience')

        app.get('/experience/edit/my-experience', status=200,
                extra_environ={'REMOTE_USER': str(user['name'])})

    def test_auth_anon_user_cant_view_manage_datasets(self):
        '''
        An anon (not logged in) user can't access the experience manage datasets page.
        '''
        app = self._get_test_app()

        factories.Dataset(type='experience', name='my-experience')

        app.get('/experience/manage_datasets/my-experience', status=302)

    def test_auth_logged_in_user_cant_view_manage_datasets(self):
        '''
        A logged in user (not sysadmin) can't access the experience manage datasets page.
        '''
        app = self._get_test_app()
        user = factories.User()

        factories.Dataset(type='experience', name='my-experience')

        app.get('/experience/manage_datasets/my-experience', status=401,
                extra_environ={'REMOTE_USER': str(user['name'])})

    def test_auth_sysadmin_can_view_manage_datasets(self):
        '''
        A sysadmin can access the experience manage datasets page.
        '''
        app = self._get_test_app()
        user = factories.Sysadmin()

        factories.Dataset(type='experience', name='my-experience')

        app.get('/experience/manage_datasets/my-experience', status=200,
                extra_environ={'REMOTE_USER': str(user['name'])})

    def test_auth_experience_admin_can_view_manage_datasets(self):
        '''
        A experience admin can access the experience manage datasets page.
        '''
        app = self._get_test_app()
        user = factories.User()

        # Make user a experience admin
        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user['name'])

        factories.Dataset(type='experience', name='my-experience')

        app.get('/experience/manage_datasets/my-experience', status=200,
                extra_environ={'REMOTE_USER': str(user['name'])})

    def test_auth_anon_user_cant_view_delete_experience_page(self):
        '''
        An anon (not logged in) user can't access the experience delete page.
        '''
        app = self._get_test_app()

        factories.Dataset(type='experience', name='my-experience')

        app.get('/experience/delete/my-experience', status=302)

    def test_auth_logged_in_user_cant_view_delete_experience_page(self):
        '''
        A logged in user can't access the experience delete page.
        '''
        app = self._get_test_app()
        user = factories.User()

        factories.Dataset(type='experience', name='my-experience')

        app.get('/experience/delete/my-experience', status=401,
                extra_environ={'REMOTE_USER': str(user['name'])})

    def test_auth_sysadmin_can_view_delete_experience_page(self):
        '''
        A sysadmin can access the experience delete page.
        '''
        app = self._get_test_app()
        user = factories.Sysadmin()

        factories.Dataset(type='experience', name='my-experience')

        app.get('/experience/delete/my-experience', status=200,
                extra_environ={'REMOTE_USER': str(user['name'])})

    def test_auth_experience_admin_can_view_delete_experience_page(self):
        '''
        A experience admin can access the experience delete page.
        '''
        app = self._get_test_app()
        user = factories.User()

        # Make user a experience admin
        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user['name'])

        factories.Dataset(type='experience', name='my-experience')

        app.get('/experience/delete/my-experience', status=200,
                extra_environ={'REMOTE_USER': str(user['name'])})

    def test_auth_anon_user_cant_view_addtoexperience_dropdown_dataset_experience_list(self):
        '''
        An anonymous user can't view the 'Add to experience' dropdown selector
        from a datasets experience list page.
        '''
        app = self._get_test_app()

        factories.Dataset(name='my-experience', type='experience')
        factories.Dataset(name='my-dataset')

        experience_list_response = app.get('/dataset/experiences/my-dataset', status=200)

        nosetools.assert_false('experience-add' in experience_list_response.forms)

    def test_auth_normal_user_cant_view_addtoexperience_dropdown_dataset_experience_list(self):
        '''
        A normal (logged in) user can't view the 'Add to experience' dropdown
        selector from a datasets experience list page.
        '''
        user = factories.User()
        app = self._get_test_app()

        factories.Dataset(name='my-experience', type='experience')
        factories.Dataset(name='my-dataset')

        experience_list_response = app.get('/dataset/experiences/my-dataset', status=200,
                                         extra_environ={'REMOTE_USER': str(user['name'])})

        nosetools.assert_false('experience-add' in experience_list_response.forms)

    def test_auth_sysadmin_can_view_addtoexperience_dropdown_dataset_experience_list(self):
        '''
        A sysadmin can view the 'Add to experience' dropdown selector from a
        datasets experience list page.
        '''
        user = factories.Sysadmin()
        app = self._get_test_app()

        factories.Dataset(name='my-experience', type='experience')
        factories.Dataset(name='my-dataset')

        experience_list_response = app.get('/dataset/experiences/my-dataset', status=200,
                                         extra_environ={'REMOTE_USER': str(user['name'])})

        nosetools.assert_true('experience-add' in experience_list_response.forms)

    def test_auth_experience_admin_can_view_addtoexperience_dropdown_dataset_experience_list(self):
        '''
        A experience admin can view the 'Add to experience' dropdown selector from
        a datasets experience list page.
        '''
        app = self._get_test_app()
        user = factories.User()

        # Make user a experience admin
        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user['name'])

        factories.Dataset(name='my-experience', type='experience')
        factories.Dataset(name='my-dataset')

        experience_list_response = app.get('/dataset/experiences/my-dataset', status=200,
                                         extra_environ={'REMOTE_USER': str(user['name'])})

        nosetools.assert_true('experience-add' in experience_list_response.forms)


class TestExperiencePackageAssociationCreate(ExperienceFunctionalTestBase):

    def test_experience_package_association_create_no_user(self):
        '''
        Calling experience package association create with no user raises
        NotAuthorized.
        '''

        context = {'user': None, 'model': None}
        nosetools.assert_raises(toolkit.NotAuthorized, helpers.call_auth,
                                'ckanext_experience_package_association_create',
                                context=context)

    def test_experience_package_association_create_sysadmin(self):
        '''
        Calling experience package association create by a sysadmin doesn't
        raise NotAuthorized.
        '''
        a_sysadmin = factories.Sysadmin()
        context = {'user': a_sysadmin['name'], 'model': None}
        helpers.call_auth('ckanext_experience_package_association_create',
                          context=context)

    def test_experience_package_association_create_experience_admin(self):
        '''
        Calling experience package association create by a experience admin
        doesn't raise NotAuthorized.
        '''
        experience_admin = factories.User()

        # Make user a experience admin
        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=experience_admin['name'])

        context = {'user': experience_admin['name'], 'model': None}
        helpers.call_auth('ckanext_experience_package_association_create',
                          context=context)

    def test_experience_package_association_create_unauthorized_creds(self):
        '''
        Calling experience package association create with unauthorized user
        raises NotAuthorized.
        '''
        not_a_sysadmin = factories.User()
        context = {'user': not_a_sysadmin['name'], 'model': None}
        nosetools.assert_raises(toolkit.NotAuthorized, helpers.call_auth,
                                'ckanext_experience_package_association_create',
                                context=context)


class TestExperiencePackageAssociationDelete(ExperienceFunctionalTestBase):

    def test_experience_package_association_delete_no_user(self):
        '''
        Calling experience package association create with no user raises
        NotAuthorized.
        '''

        context = {'user': None, 'model': None}
        nosetools.assert_raises(toolkit.NotAuthorized, helpers.call_auth,
                                'ckanext_experience_package_association_delete',
                                context=context)

    def test_experience_package_association_delete_sysadmin(self):
        '''
        Calling experience package association create by a sysadmin doesn't
        raise NotAuthorized.
        '''
        a_sysadmin = factories.Sysadmin()
        context = {'user': a_sysadmin['name'], 'model': None}
        helpers.call_auth('ckanext_experience_package_association_delete',
                          context=context)

    def test_experience_package_association_delete_experience_admin(self):
        '''
        Calling experience package association create by a experience admin
        doesn't raise NotAuthorized.
        '''
        experience_admin = factories.User()

        # Make user a experience admin
        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=experience_admin['name'])

        context = {'user': experience_admin['name'], 'model': None}
        helpers.call_auth('ckanext_experience_package_association_delete',
                          context=context)

    def test_experience_package_association_delete_unauthorized_creds(self):
        '''
        Calling experience package association create with unauthorized user
        raises NotAuthorized.
        '''
        not_a_sysadmin = factories.User()
        context = {'user': not_a_sysadmin['name'], 'model': None}
        nosetools.assert_raises(toolkit.NotAuthorized, helpers.call_auth,
                                'ckanext_experience_package_association_delete',
                                context=context)


class TestExperienceAdminAddAuth(ExperienceFunctionalTestBase):

    def test_experience_admin_add_no_user(self):
        '''
        Calling experience admin add with no user raises NotAuthorized.
        '''

        context = {'user': None, 'model': None}
        nosetools.assert_raises(toolkit.NotAuthorized, helpers.call_auth,
                                'ckanext_experience_admin_add', context=context)

    def test_experience_admin_add_correct_creds(self):
        '''
        Calling experience admin add by a sysadmin doesn't raise
        NotAuthorized.
        '''
        a_sysadmin = factories.Sysadmin()
        context = {'user': a_sysadmin['name'], 'model': None}
        helpers.call_auth('ckanext_experience_admin_add', context=context)

    def test_experience_admin_add_unauthorized_creds(self):
        '''
        Calling experience admin add with unauthorized user raises
        NotAuthorized.
        '''
        not_a_sysadmin = factories.User()
        context = {'user': not_a_sysadmin['name'], 'model': None}
        nosetools.assert_raises(toolkit.NotAuthorized, helpers.call_auth,
                                'ckanext_experience_admin_add', context=context)


class TestExperienceAdminRemoveAuth(ExperienceFunctionalTestBase):

    def test_experience_admin_remove_no_user(self):
        '''
        Calling experience admin remove with no user raises NotAuthorized.
        '''

        context = {'user': None, 'model': None}
        nosetools.assert_raises(toolkit.NotAuthorized, helpers.call_auth,
                                'ckanext_experience_admin_remove', context=context)

    def test_experience_admin_remove_correct_creds(self):
        '''
        Calling experience admin remove by a sysadmin doesn't raise
        NotAuthorized.
        '''
        a_sysadmin = factories.Sysadmin()
        context = {'user': a_sysadmin['name'], 'model': None}
        helpers.call_auth('ckanext_experience_admin_remove', context=context)

    def test_experience_admin_remove_unauthorized_creds(self):
        '''
        Calling experience admin remove with unauthorized user raises
        NotAuthorized.
        '''
        not_a_sysadmin = factories.User()
        context = {'user': not_a_sysadmin['name'], 'model': None}
        nosetools.assert_raises(toolkit.NotAuthorized, helpers.call_auth,
                                'ckanext_experience_admin_remove', context=context)


class TestExperienceAdminListAuth(ExperienceFunctionalTestBase):

    def test_experience_admin_list_no_user(self):
        '''
        Calling experience admin list with no user raises NotAuthorized.
        '''

        context = {'user': None, 'model': None}
        nosetools.assert_raises(toolkit.NotAuthorized, helpers.call_auth,
                                'ckanext_experience_admin_list', context=context)

    def test_experience_admin_list_correct_creds(self):
        '''
        Calling experience admin list by a sysadmin doesn't raise
        NotAuthorized.
        '''
        a_sysadmin = factories.Sysadmin()
        context = {'user': a_sysadmin['name'], 'model': None}
        helpers.call_auth('ckanext_experience_admin_list', context=context)

    def test_experience_admin_list_unauthorized_creds(self):
        '''
        Calling experience admin list with unauthorized user raises
        NotAuthorized.
        '''
        not_a_sysadmin = factories.User()
        context = {'user': not_a_sysadmin['name'], 'model': None}
        nosetools.assert_raises(toolkit.NotAuthorized, helpers.call_auth,
                                'ckanext_experience_admin_list', context=context)


class TestExperienceAuthManageExperienceAdmins(ExperienceFunctionalTestBase):

    def test_auth_anon_user_cant_view_experience_admin_manage_page(self):
        '''
        An anon (not logged in) user can't access the manage experience admin
        page.
        '''
        app = self._get_test_app()
        app.get("/experience/new", status=302)

    def test_auth_logged_in_user_cant_view_experience_admin_manage_page(self):
        '''
        A logged in user can't access the manage experience admin page.
        '''
        app = self._get_test_app()
        user = factories.User()
        app.get("/experience/new", status=401,
                extra_environ={'REMOTE_USER': str(user['name'])})

    def test_auth_sysadmin_can_view_experience_admin_manage_page(self):
        '''
        A sysadmin can access the manage experience admin page.
        '''
        app = self._get_test_app()
        user = factories.Sysadmin()
        app.get("/experience/new", status=200,
                extra_environ={'REMOTE_USER': str(user['name'])})
