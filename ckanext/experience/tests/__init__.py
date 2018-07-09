from ckanext.experience.model import setup as experience_setup


try:
    import ckan.tests.helpers as helpers
except ImportError:  # for ckan <= 2.3
    import ckan.new_tests.helpers as helpers


class ExperienceFunctionalTestBase(helpers.FunctionalTestBase):

    def setup(self):
        '''Reset the database and clear the search indexes.'''
        super(ExperienceFunctionalTestBase, self).setup()
        # set up experience tables
        experience_setup()
