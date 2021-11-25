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

import os
import sys
import logging

from collections import OrderedDict

import ckan.plugins as plugins
import ckan.lib.plugins as lib_plugins
import ckan.lib.helpers as h
from ckan.plugins import toolkit as tk
from ckan import model as ckan_model
from ckan.lib.plugins import DefaultTranslation

import ckanext.experience.logic.auth
import ckanext.experience.logic.action.create
import ckanext.experience.logic.action.delete
import ckanext.experience.logic.action.update
import ckanext.experience.logic.action.get
import ckanext.experience.logic.schema as experience_schema
import ckanext.experience.logic.helpers as experience_helpers
from ckanext.experience.model import setup as model_setup
import ckanext.experience.views as views
import ckanext.experience.cli as cli

c = tk.c
_ = tk._

log = logging.getLogger(__name__)

DATASET_TYPE_NAME = views.DATASET_TYPE_NAME


class ExperiencePlugin(plugins.SingletonPlugin, lib_plugins.DefaultDatasetForm,
                       DefaultTranslation):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IClick)

    # IConfigurer

    def update_config(self, config):

        tk.add_template_directory(config, 'templates')
        tk.add_public_directory(config, 'public')
        tk.add_resource('fanstatic', 'experience')

        tk.add_ckan_admin_tab(config, 'experience_blueprint.admins',
                              'Experience Config')

    # IConfigurable

    def configure(self, config):
        model_setup()

    # IDatasetForm

    def package_types(self):
        return [DATASET_TYPE_NAME]

    def is_fallback(self):
        return False

    def search_template(self):
        return 'experience/search.html'

    def new_template(self):
        return 'experience/new.html'

    def read_template(self):
        return 'experience/read.html'

    def edit_template(self):
        return 'experience/edit.html'

    def package_form(self):
        return 'experience/new_package_form.html'

    def create_package_schema(self):
        return experience_schema.experience_create_schema()

    def update_package_schema(self):
        return experience_schema.experience_update_schema()

    def show_package_schema(self):
        return experience_schema.experience_show_schema()

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'facet_remove_field': experience_helpers.facet_remove_field,
            'get_site_statistics': experience_helpers.get_site_statistics,
            'check_ckan_version': tk.check_ckan_version
        }

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        '''Only show tags for Experience search list.'''
        if package_type != DATASET_TYPE_NAME:
            return facets_dict
        return OrderedDict({'tags': _('Tags')})

    # IAuthFunctions

    def get_auth_functions(self):
        return {
            'ckanext_experience_create': ckanext.experience.logic.auth.create,
            'ckanext_experience_update': ckanext.experience.logic.auth.update,
            'ckanext_experience_delete': ckanext.experience.logic.auth.delete,
            'ckanext_experience_show': ckanext.experience.logic.auth.show,
            'ckanext_experience_list': ckanext.experience.logic.auth.list,
            'ckanext_experience_package_association_create':
                ckanext.experience.logic.auth.package_association_create,
            'ckanext_experience_package_association_delete':
                ckanext.experience.logic.auth.package_association_delete,
            'ckanext_experience_package_list':
                ckanext.experience.logic.auth.experience_package_list,
            'ckanext_package_experience_list':
                ckanext.experience.logic.auth.package_experience_list,
            'ckanext_experience_admin_add':
                ckanext.experience.logic.auth.add_experience_admin,
            'ckanext_experience_admin_remove':
                ckanext.experience.logic.auth.remove_experience_admin,
            'ckanext_experience_admin_list':
                ckanext.experience.logic.auth.experience_admin_list
        }

    # IBlueprint

    def get_blueprint(self):
        return views.get_blueprints()

    # IActions

    def get_actions(self):
        action_functions = {
            'ckanext_experience_create':
                ckanext.experience.logic.action.create.experience_create,
            'ckanext_experience_update':
                ckanext.experience.logic.action.update.experience_update,
            'ckanext_experience_delete':
                ckanext.experience.logic.action.delete.experience_delete,
            'ckanext_experience_show':
                ckanext.experience.logic.action.get.experience_show,
            'ckanext_experience_list':
                ckanext.experience.logic.action.get.experience_list,
            'ckanext_experience_package_association_create':
                ckanext.experience.logic.action.create.experience_package_association_create,
            'ckanext_experience_package_association_delete':
                ckanext.experience.logic.action.delete.experience_package_association_delete,
            'ckanext_experience_package_list':
                ckanext.experience.logic.action.get.experience_package_list,
            'ckanext_package_experience_list':
                ckanext.experience.logic.action.get.package_experience_list,
            'ckanext_experience_admin_add':
                ckanext.experience.logic.action.create.experience_admin_add,
            'ckanext_experience_admin_remove':
                ckanext.experience.logic.action.delete.experience_admin_remove,
            'ckanext_experience_admin_list':
                ckanext.experience.logic.action.get.experience_admin_list,
        }
        return action_functions

    # IPackageController

    def _add_to_pkg_dict(self, context, pkg_dict):
        '''
        Add key/values to pkg_dict and return it.
        '''

        if pkg_dict['type'] != 'experience':
            return pkg_dict

        # Add a display url for the Experience image to the pkg dict so template
        # has access to it.
        image_url = pkg_dict.get('image_url')
        pkg_dict[u'image_display_url'] = image_url
        if image_url and not image_url.startswith('http'):
            pkg_dict[u'image_url'] = image_url
            pkg_dict[u'image_display_url'] = \
                h.url_for_static('uploads/{0}/{1}'
                                 .format(DATASET_TYPE_NAME,
                                         pkg_dict.get('image_url')),
                                 qualified=True)

        # Add dataset count
        pkg_dict[u'num_datasets'] = len(
            tk.get_action('ckanext_experience_package_list')(
                context, {'experience_id': pkg_dict['id']}))

        # Rendered notes
        pkg_dict[u'experience_notes_formatted'] = \
            h.render_markdown(pkg_dict['notes'])
        return pkg_dict

    def after_show(self, context, pkg_dict):
        '''
        Modify package_show pkg_dict.
        '''
        pkg_dict = self._add_to_pkg_dict(context, pkg_dict)

    def before_view(self, pkg_dict):
        '''
        Modify pkg_dict that is sent to templates.
        '''

        context = {'model': ckan_model, 'session': ckan_model.Session,
                   'user': c.user or c.author}

        return self._add_to_pkg_dict(context, pkg_dict)

    def before_search(self, search_params):
        '''
        Unless the query is already being filtered by this dataset_type
        (either positively, or negatively), exclude datasets of type
        `experience`.
        '''
        fq = search_params.get('fq', '')
        filter = 'dataset_type:{0}'.format(DATASET_TYPE_NAME)
        if filter not in fq:
            search_params.update({'fq': fq + " -" + filter})
        return search_params

    # IClick

    def get_commands(self):
        return cli.get_commands()
