from nose import tools as nosetools
from nose import SkipTest

from ckan.plugins import toolkit as tk
try:
    import ckan.tests.factories as factories
except ImportError:  # for ckan <= 2.3
    import ckan.new_tests.factories as factories

try:
    import ckan.tests.helpers as helpers
except ImportError:  # for ckan <= 2.3
    import ckan.new_tests.helpers as helpers

import ckanext.experience.logic.helpers as experience_helpers
from ckanext.experience.tests import ExperienceFunctionalTestBase


class TestGetSiteStatistics(ExperienceFunctionalTestBase):

    def test_dataset_count_no_datasets(self):
        '''
        Dataset and experience count is 0 when no datasets, and no experiences.
        '''
        if not tk.check_ckan_version(min_version='2.5'):
            raise SkipTest('get_site_statistics without user broken in CKAN 2.4')
        stats = experience_helpers.get_site_statistics()
        nosetools.assert_equal(stats['dataset_count'], 0)
        nosetools.assert_equal(stats['experience_count'], 0)

    def test_dataset_count_no_datasets_some_experiences(self):
        '''
        Dataset and experience count is 0 when no datasets, but some experiences.
        '''
        if not tk.check_ckan_version(min_version='2.5'):
            raise SkipTest('get_site_statistics without user broken in CKAN 2.4')
        for i in xrange(0, 10):
            factories.Dataset(type='experience')

        stats = experience_helpers.get_site_statistics()
        nosetools.assert_equal(stats['dataset_count'], 0)
        nosetools.assert_equal(stats['experience_count'], 10)

    def test_dataset_count_some_datasets_no_experiences(self):
        '''
        Dataset and experience count is correct when there are datasets, but no
        experiences.
        '''
        if not tk.check_ckan_version(min_version='2.5'):
            raise SkipTest('get_site_statistics without user broken in CKAN 2.4')
        for i in xrange(0, 10):
            factories.Dataset()

        stats = experience_helpers.get_site_statistics()
        nosetools.assert_equal(stats['dataset_count'], 10)
        nosetools.assert_equal(stats['experience_count'], 0)

    def test_dataset_count_some_datasets_some_experiences(self):
        '''
        Dataset and experience count is correct when there are datasets and some
        experiences.
        '''
        if not tk.check_ckan_version(min_version='2.5'):
            raise SkipTest('get_site_statistics without user broken in CKAN 2.4')
        for i in xrange(0, 10):
            factories.Dataset()

        for i in xrange(0, 5):
            factories.Dataset(type='experience')

        stats = experience_helpers.get_site_statistics()
        nosetools.assert_equal(stats['dataset_count'], 10)
        nosetools.assert_equal(stats['experience_count'], 5)
