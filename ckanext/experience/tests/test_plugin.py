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

from ckan.lib.helpers import url_for
from nose import tools as nosetools
from nose import SkipTest

from ckan.plugins import toolkit as tk
import ckan.model as model
try:
    import ckan.tests.factories as factories
except ImportError:  # for ckan <= 2.3
    import ckan.new_tests.factories as factories

try:
    import ckan.tests.helpers as helpers
except ImportError:  # for ckan <= 2.3
    import ckan.new_tests.helpers as helpers

from ckanext.experience.model import ExperiencePackageAssociation
from ckanext.experience.tests import ExperienceFunctionalTestBase

import logging
log = logging.getLogger(__name__)

submit_and_follow = helpers.submit_and_follow


class TestExperienceIndex(ExperienceFunctionalTestBase):

    def test_experiences_redirects_to_experience(self):
        '''/experiences redirects to /experience.'''
        app = self._get_test_app()
        response = app.get('/experiences', status=302)
        nosetools.assert_equal(response.location, 'http://localhost/experience')

    def test_experiences_redirects_to_experience_for_item(self):
        '''/experiences/ redirects to /experience.'''
        app = self._get_test_app()

        factories.Dataset(type='experience', name='my-experience')

        response = app.get('/experiences/my-experience', status=302)
        nosetools.assert_equal(response.location, 'http://localhost/experience/my-experience')

    def test_experience_listed_on_index(self):
        '''
        An added Experience will appear on the Experience index page.
        '''
        app = self._get_test_app()

        factories.Dataset(type='experience', name='my-experience')

        response = app.get("/experience", status=200)
        response.mustcontain("1 experience found")
        response.mustcontain("my-experience")


class TestExperienceNewView(ExperienceFunctionalTestBase):

    def test_experience_create_form_renders(self):
        app = self._get_test_app()
        sysadmin = factories.Sysadmin()

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='ckanext.experience.controller:ExperienceController', action='new'),
            extra_environ=env,
        )
        nosetools.assert_true('dataset-edit' in response.forms)

    def test_experience_new_redirects_to_manage_datasets(self):
        '''Creating a new experience redirects to the manage datasets form.'''
        app = self._get_test_app()
        sysadmin = factories.Sysadmin()
        # need a dataset for the 'bulk_action.experience_add' button to show
        factories.Dataset()

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='ckanext.experience.controller:ExperienceController', action='new'),
            extra_environ=env,
        )

        # create experience
        form = response.forms['dataset-edit']
        form['name'] = u'my-experience'
        create_response = submit_and_follow(app, form, env, 'save')

        # Unique to manage_datasets page
        nosetools.assert_true('bulk_action.experience_add' in create_response)
        # Requested page is the manage_datasets url.
        nosetools.assert_equal(url_for(controller='ckanext.experience.controller:ExperienceController',
                                       action='manage_datasets', id='my-experience'), create_response.request.path)


class TestExperienceEditView(ExperienceFunctionalTestBase):

    def test_experience_edit_form_renders(self):
        '''
        Edit form renders in response for ExperienceController edit action.
        '''
        app = self._get_test_app()
        sysadmin = factories.Sysadmin()
        factories.Dataset(name='my-experience', type='experience')

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='ckanext.experience.controller:ExperienceController',
                        action='edit',
                        id='my-experience'),
            extra_environ=env,
        )
        nosetools.assert_true('dataset-edit' in response.forms)

    def test_experience_edit_redirects_to_experience_details(self):
        '''Editing a experience redirects to the experience details page.'''
        app = self._get_test_app()
        sysadmin = factories.Sysadmin()
        factories.Dataset(name='my-experience', type='experience')

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='ckanext.experience.controller:ExperienceController',
                        action='edit', id='my-experience'),
            extra_environ=env,
        )

        # edit experience
        form = response.forms['dataset-edit']
        form['name'] = u'my-changed-experience'
        edit_response = submit_and_follow(app, form, env, 'save')

        # Requested page is the experience read url.
        nosetools.assert_equal(url_for(controller='ckanext.experience.controller:ExperienceController',
                                       action='read', id='my-changed-experience'), edit_response.request.path)


class TestDatasetView(ExperienceFunctionalTestBase):

    '''Plugin adds a new experiences view for datasets.'''

    def test_dataset_read_has_experiences_tab(self):
        '''
        Dataset view page has a new Experiences tab linked to the correct place.
        '''
        app = self._get_test_app()
        dataset = factories.Dataset(name='my-dataset')

        response = app.get(
            url=url_for(controller='package', action='read', id=dataset['id'])
        )
        # response contains link to dataset's experience list
        nosetools.assert_true('/dataset/experiences/{0}'.format(dataset['name']) in response)

    def test_dataset_experience_page_lists_experiences_no_associations(self):
        '''
        No experiences are listed if dataset has no experience associations.
        '''

        app = self._get_test_app()
        dataset = factories.Dataset(name='my-dataset')

        response = app.get(
            url=url_for(controller='ckanext.experience.controller:ExperienceController',
                        action='dataset_experience_list', id=dataset['id'])
        )

        nosetools.assert_equal(len(response.html.select('ul.media-grid li.media-item')), 0)

    def test_dataset_experience_page_lists_experiences_two_associations(self):
        '''
        Two experiences are listed for dataset with two experience associations.
        '''

        app = self._get_test_app()
        sysadmin = factories.Sysadmin()
        dataset = factories.Dataset(name='my-dataset')
        experience_one = factories.Dataset(name='my-first-experience', type='experience')
        experience_two = factories.Dataset(name='my-second-experience', type='experience')
        factories.Dataset(name='my-third-experience', type='experience')

        context = {'user': sysadmin['name']}
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=dataset['id'],
                            experience_id=experience_one['id'])
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=dataset['id'],
                            experience_id=experience_two['id'])

        response = app.get(
            url=url_for(controller='ckanext.experience.controller:ExperienceController',
                        action='dataset_experience_list', id=dataset['id'])
        )

        nosetools.assert_equal(len(response.html.select('li.media-item')), 2)
        nosetools.assert_true('my-first-experience' in response)
        nosetools.assert_true('my-second-experience' in response)
        nosetools.assert_true('my-third-experience' not in response)

    def test_dataset_experience_page_add_to_experience_dropdown_list(self):
        '''
        Add to experience dropdown only lists experiences that aren't already
        associated with dataset.
        '''
        app = self._get_test_app()
        sysadmin = factories.Sysadmin()
        dataset = factories.Dataset(name='my-dataset')
        experience_one = factories.Dataset(name='my-first-experience', type='experience')
        experience_two = factories.Dataset(name='my-second-experience', type='experience')
        experience_three = factories.Dataset(name='my-third-experience', type='experience')

        context = {'user': sysadmin['name']}
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=dataset['id'],
                            experience_id=experience_one['id'])

        response = app.get(
            url=url_for(controller='ckanext.experience.controller:ExperienceController',
                        action='dataset_experience_list', id=dataset['id']),
            extra_environ={'REMOTE_USER': str(sysadmin['name'])}
        )

        experience_add_form = response.forms['experience-add']
        experience_added_options = [value for (value, _) in experience_add_form['experience_added'].options]
        nosetools.assert_true(experience_one['id'] not in experience_added_options)
        nosetools.assert_true(experience_two['id'] in experience_added_options)
        nosetools.assert_true(experience_three['id'] in experience_added_options)

    def test_dataset_experience_page_add_to_experience_dropdown_submit(self):
        '''
        Submitting 'Add to experience' form with selected experience value creates
        a sc/pkg association.
        '''
        app = self._get_test_app()
        sysadmin = factories.Sysadmin()
        dataset = factories.Dataset(name='my-dataset')
        experience_one = factories.Dataset(name='my-first-experience', type='experience')
        factories.Dataset(name='my-second-experience', type='experience')
        factories.Dataset(name='my-third-experience', type='experience')

        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 0)

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}

        response = app.get(
            url=url_for(controller='ckanext.experience.controller:ExperienceController',
                        action='dataset_experience_list', id=dataset['id']),
            extra_environ=env
        )

        form = response.forms['experience-add']
        form['experience_added'] = experience_one['id']
        experience_add_response = submit_and_follow(app, form, env)

        # returns to the correct page
        nosetools.assert_equal(experience_add_response.request.path, "/dataset/experiences/my-dataset")
        # an association is created
        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 1)

    def test_dataset_experience_page_remove_experience_button_submit(self):
        '''
        Submitting 'Remove' form with selected experience value deletes a sc/pkg
        association.
        '''
        app = self._get_test_app()
        sysadmin = factories.Sysadmin()
        dataset = factories.Dataset(name='my-dataset')
        experience_one = factories.Dataset(name='my-first-experience', type='experience')

        context = {'user': sysadmin['name']}
        helpers.call_action('ckanext_experience_package_association_create',
                            context=context, package_id=dataset['id'],
                            experience_id=experience_one['id'])

        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 1)

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='ckanext.experience.controller:ExperienceController',
                        action='dataset_experience_list', id=dataset['id']),
            extra_environ=env
        )

        # Submit the remove form.
        form = response.forms[1]
        nosetools.assert_equal(form['remove_experience_id'].value, experience_one['id'])
        experience_remove_response = submit_and_follow(app, form, env)

        # returns to the correct page
        nosetools.assert_equal(experience_remove_response.request.path, "/dataset/experiences/my-dataset")
        # the association is deleted
        nosetools.assert_equal(model.Session.query(ExperiencePackageAssociation).count(), 0)


class TestExperienceAdminManageView(ExperienceFunctionalTestBase):

    '''Plugin adds a experience admin management page to ckan-admin section.'''

    def test_ckan_admin_has_experience_config_tab(self):
        '''
        ckan-admin index page has a experience config tab.
        '''
        if not tk.check_ckan_version(min_version='2.4'):
            raise SkipTest('Experience config tab only available for CKAN 2.4+')

        app = self._get_test_app()
        sysadmin = factories.Sysadmin()

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='admin', action='index'),
            extra_environ=env
        )
        # response contains link to dataset's experience list
        nosetools.assert_true('/ckan-admin/experience_admins' in response)

    def test_experience_admin_manage_page_returns_correct_status(self):
        '''
        /ckan-admin/experience_admins can be successfully accessed.
        '''
        app = self._get_test_app()
        sysadmin = factories.Sysadmin()

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        app.get(url=url_for(controller='ckanext.experience.controller:ExperienceController',
                            action='manage_experience_admins'),
                status=200, extra_environ=env)

    def test_experience_admin_manage_page_lists_experience_admins(self):
        '''
        Experience admins are listed on the experience admin page.
        '''
        app = self._get_test_app()
        user_one = factories.User()
        user_two = factories.User()
        user_three = factories.User()

        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user_one['name'])
        helpers.call_action('ckanext_experience_admin_add', context={},
                            username=user_two['name'])

        sysadmin = factories.Sysadmin()

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        response = app.get(url=url_for(controller='ckanext.experience.controller:ExperienceController',
                                       action='manage_experience_admins'),
                           status=200, extra_environ=env)

        nosetools.assert_true('/user/{0}'.format(user_one['name']) in response)
        nosetools.assert_true('/user/{0}'.format(user_two['name']) in response)
        nosetools.assert_true('/user/{0}'.format(user_three['name']) not in response)

    def test_experience_admin_manage_page_no_admins_message(self):
        '''
        Experience admins page displays message if no experience admins present.
        '''
        app = self._get_test_app()

        sysadmin = factories.Sysadmin()

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        response = app.get(url=url_for(controller='ckanext.experience.controller:ExperienceController',
                                       action='manage_experience_admins'),
                           status=200, extra_environ=env)

        nosetools.assert_true('There are currently no Experience Admins' in response)


class TestSearch(helpers.FunctionalTestBase):

    def test_search_with_nonascii_filter_query(self):
        '''
        Searching with non-ASCII filter queries works.

        See https://github.com/ckan/ckanext-experience/issues/34.
        '''
        app = self._get_test_app()
        tag = u'\xe4\xf6\xfc'
        dataset = factories.Dataset(tags=[{'name': tag, 'state': 'active'}])
        result = helpers.call_action('package_search', fq='tags:' + tag)
        nosetools.assert_equals(result['count'], 1)

