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

import ckan.lib.helpers as h
from ckan.plugins import toolkit as tk


def facet_remove_field(key, value=None, replace=None):
    '''
    A custom remove field function to be used by the Experience search page to
    render the remove link for the tag pills.
    '''
    return h.remove_url_param(
        key, value=value, replace=replace,
        controller='ckanext.experience.controller:ExperienceController',
        action='search')


def get_site_statistics():
    '''
    Custom stats helper, so we can get the correct number of packages, and a
    count of experiences.
    '''

    stats = {}
    stats['experience_count'] = tk.get_action('package_search')(
        {}, {"rows": 1, 'fq': 'dataset_type:experience'})['count']
    stats['dataset_count'] = tk.get_action('package_search')(
        {}, {"rows": 1, 'fq': '!dataset_type:experience'})['count']
    stats['group_count'] = len(tk.get_action('group_list')({}, {}))
    stats['organization_count'] = len(
        tk.get_action('organization_list')({}, {}))

    return stats
