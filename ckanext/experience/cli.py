# -*- coding: utf-8 -*-

import click

from ckan import model

import ckantoolkit as tk


@click.group()
def experience():
    '''experience commands
    '''
    pass


@experience.command()
@click.option('--allow-duplicates',
              default=False,
              help='Allow related items with duplicate titles to be migrated.'
                   'Duplicate experiences will be created as "duplicate_<related-name>_<related-id>".')
def migrate(allow_duplicates):
    """
        experience migrate [options]
    """
    related_items = tk.get_action('related_list')(data_dict={})

    # preflight:
    # related items must have unique titles before migration
    related_titles = [i['title'] for i in related_items]
    # make a list of duplicate titles
    duplicate_titles = _find_duplicates(related_titles)
    if duplicate_titles and allow_duplicates is False:
        print(
            """All Related Items must have unique titles before migration. The following
Related Item titles are used more than once and need to be corrected before
migration can continue. Please correct and try again:""")
        for i in duplicate_titles:
            print(i)
        return

    for related in related_items:
        existing_experience = tk.get_action('package_search')(data_dict={
            'fq':
                '+dataset_type:experience original_related_item_id:{0}'.format(
                    related['id'])
        })
        normalized_title = substitute_ascii_equivalents(related['title'])
        if existing_experience['count'] > 0:
            print('Experience for Related Item "{0}" already exists.'.format(
                normalized_title))
        else:
            experience_title = _gen_new_title(related.get('title'),
                                              related['id'])
            data_dict = {
                'original_related_item_id': related.get('id'),
                'title': experience_title,
                'name': munge_title_to_name(experience_title),
                'notes': related.get('description'),
                'image_url': related.get('image_url'),
                'url': related.get('url'),
                'tags': [{
                    "name": related.get('type').lower()
                }]
            }
            # make the experience
            try:
                new_experience = tk.get_action('ckanext_experience_create')(
                    data_dict=data_dict)
            except Exception as e:
                print('There was a problem migrating "{0}": {1}'.format(
                    normalized_title, e))
            else:
                print('Created Experience from the Related Item "{0}"'.format(
                    normalized_title))

                # make the experience_package_association, if needed
                try:
                    related_pkg_id = _get_related_dataset(related['id'])
                    if related_pkg_id:
                        tk.get_action(
                            'ckanext_experience_package_association_create')(
                            data_dict={
                                'experience_id': new_experience['id'],
                                'package_id': related_pkg_id
                            })
                except Exception as e:
                    print('There was a problem creating the '
                          'experience_package_association for "{0}": {1}'.format(normalized_title, e))


def _get_related_dataset(related_id):
    '''Get the id of a package from related_dataset, if one exists.'''
    related_dataset = model.Session.query(
        model.RelatedDataset).filter_by(related_id=related_id).first()
    if related_dataset:
        return related_dataset.dataset_id


def get_commands():
    return [experience]