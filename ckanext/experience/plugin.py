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

from flask import Blueprint


import ckan.plugins as plugins
import ckan.lib.plugins as lib_plugins
import ckan.lib.helpers as h
from ckan.plugins import toolkit as tk
import ckan.logic as logic
import ckan.model as model
from ckanext.experience.views import experience
from ckanext.experience.views import admin_experience


_ = tk._
c = tk.c
request = tk.request
render = tk.render
abort = tk.abort
redirect = tk.redirect_to
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError
check_access = tk.check_access
get_action = tk.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
NotAuthorized = tk.NotAuthorized


try:
    from collections import OrderedDict  # from python 2.7
except ImportError:
    from sqlalchemy.util import OrderedDict


from ckan import model as ckan_model
from ckan.lib.plugins import DefaultTranslation

from routes.mapper import SubMapper

import ckanext.experience.logic.auth
import ckanext.experience.logic.action.create
import ckanext.experience.logic.action.delete
import ckanext.experience.logic.action.update
import ckanext.experience.logic.action.get
import ckanext.experience.logic.schema as experience_schema
import ckanext.experience.logic.helpers as experience_helpers
from ckanext.experience.model import setup as model_setup

c = tk.c
_ = tk._

log = logging.getLogger(__name__)

DATASET_TYPE_NAME = 'experience'

#def register_translator():
    # Register a translator in this thread so that
    # the _() functions in logic layer can work
#    from fanstatic.registry import Registry

#    from ckan.lib.cli import MockTranslator
#    global registry
#    registry = Registry()
#    registry.prepare()
#    global translator_obj
#    translator_obj = MockTranslator()
#    registry.register(translator_obj)


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

    # IConfigurer

    def update_config(self, config):
        #register_translator()

        ckan_templates_dir = config.get('ckan.base_templates_folder')
        ckan_public_dir = config.get('ckan.base_public_folder')
        extension_templates_dir = 'templates'
        extension_public_dir = 'public'

        if tk.check_ckan_version(min_version='2.7'):
            if ckan_templates_dir == 'templates-bs2':
                extension_templates_dir = 'templates-bs2'
                extension_public_dir = 'public-bs2'
        else:
            extension_templates_dir = 'templates-bs2'
            extension_public_dir = 'public-bs2'

        tk.add_template_directory(config, extension_templates_dir)
        tk.add_public_directory(config, extension_public_dir)
        tk.add_resource('fanstatic', 'experience')

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

    # IRoutes

    def get_blueprint(self):
        

        # These named routes are used for custom dataset forms which will use
        # the names below based on the dataset.type ('dataset' is the default
        # type)

        # Font Awesome was upgraded to v4 in CKAN 2.7
        is_fontawesome_v4 = tk.check_ckan_version(min_version='2.7')

        if is_fontawesome_v4:
            ckan_picture_icon = 'handshake-o'
        else:
            ckan_picture_icon = 'handshake'


        # blueprint = Blueprint('ckanext.experience.views:ExperienceController', self.__module__)
        # rules = [
        # 	('/experience', 'index search', index),
        # 	('/experience/new', 'new', new),
        # 	('/experience/delete/{id}', 'delete', delete),
        # 	('/experience/{id}', 'read', read),
        # 	('/experience/edit/{id}', 'edit', edit),
        # 	('/experience/manage_datasets/{id}', 'manga_datasets', manage_datasets),
        #     ('/dataset/experiences/{id}', 'dataset_experience_list', dataset_experience_list),
       	#     ('/ckan-admin/experience_admins', 'manage_experience_admins', manage_experience_admins),
       	#     ('/ckan-admin/experience_admin_remove', 'remove_experience_admin', remove_experience_admin),
        # ]
        # for rule in rules:
        #    	blueprint.add_url_rule("/experience") 
        
           #with SubMapper(map,'ckanext.experience.controller:ExperienceController') as m:
            #m.connect('ckanext_experience_index', '/experience', action='search',
            #          highlight_actions='index search')
           # m.connect('ckanext_experience_new', '/experience/new', action='new')
            #m.connect('ckanext_experience_delete', '/experience/delete/{id}',
             #         action='delete')
            #m.connect('ckanext_experience_read', '/experience/{id}', action='read',
            #          ckan_icon=ckan_picture_icon)
            #m.connect('ckanext_experience_edit', '/experience/edit/{id}',
            #          action='edit', ckan_icon='edit')
            #m.connect('ckanext_experience_manage_datasets',
            #          '/experience/manage_datasets/{id}',
            #          action="manage_datasets", ckan_icon="sitemap")
            #m.connect('dataset_experience_list', '/dataset/experiences/{id}',
            #          action='dataset_experience_list', ckan_icon=ckan_picture_icon)
            #m.connect('ckanext_experience_admins', '/ckan-admin/experience_admins',
            #          action='manage_experience_admins', ckan_icon=ckan_picture_icon),
            #m.connect('ckanext_experience_admin_remove',
            #          '/ckan-admin/experience_admin_remove',
            #          action='remove_experience_admin')
        redirect('/experiences', '/experience')
        redirect('/experiences/{url:.*}', '/experience/{url}')
        return [views, admin_views]

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
