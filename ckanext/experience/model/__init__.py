from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import types

from ckan.model.domain_object import DomainObject
from ckan.model.meta import metadata, mapper, Session
from ckan import model

import logging
log = logging.getLogger(__name__)


experience_package_assocation_table = None
experience_admin_table = None


def setup():
    # setup experience_package_assocation_table
    if experience_package_assocation_table is None:
        define_experience_package_association_table()
        log.debug('ExperiencePackageAssociation table defined in memory')

    if model.package_table.exists():
        if not experience_package_assocation_table.exists():
            experience_package_assocation_table.create()
            log.debug('ExperiencePackageAssociation table create')
        else:
            log.debug('ExperiencePackageAssociation table already exists')
    else:
        log.debug('ExperiencePackageAssociation table creation deferred')

    # setup experience_admin_table
    if experience_admin_table is None:
        define_experience_admin_table()
        log.debug('ExperienceAdmin table defined in memory')

    if model.user_table.exists():
        if not experience_admin_table.exists():
            experience_admin_table.create()
            log.debug('ExperienceAdmin table create')
        else:
            log.debug('ExperienceAdmin table already exists')
    else:
        log.debug('ExperienceAdmin table creation deferred')


class ExperienceBaseModel(DomainObject):
    @classmethod
    def filter(cls, **kwargs):
        return Session.query(cls).filter_by(**kwargs)

    @classmethod
    def exists(cls, **kwargs):
        if cls.filter(**kwargs).first():
            return True
        else:
            return False

    @classmethod
    def get(cls, **kwargs):
        instance = cls.filter(**kwargs).first()
        return instance

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        Session.add(instance)
        Session.commit()
        return instance.as_dict()


class ExperiencePackageAssociation(ExperienceBaseModel):

    @classmethod
    def get_package_ids_for_experience(cls, experience_id):
        '''
        Return a list of package ids associated with the passed experience_id.
        '''
        experience_package_association_list = \
            Session.query(cls.package_id).filter_by(
                experience_id=experience_id).all()
        return experience_package_association_list

    @classmethod
    def get_experience_ids_for_package(cls, package_id):
        '''
        Return a list of experience ids associated with the passed package_id.
        '''
        experience_package_association_list = \
            Session.query(cls.experience_id).filter_by(
                package_id=package_id).all()
        return experience_package_association_list


def define_experience_package_association_table():
    global experience_package_assocation_table

    experience_package_assocation_table = Table(
        'experience_package_association', metadata,
        Column('package_id', types.UnicodeText,
               ForeignKey('package.id',
                          ondelete='CASCADE',
                          onupdate='CASCADE'),
               primary_key=True, nullable=False),
        Column('experience_id', types.UnicodeText,
               ForeignKey('package.id',
                          ondelete='CASCADE',
                          onupdate='CASCADE'),
               primary_key=True, nullable=False)
    )

    mapper(ExperiencePackageAssociation, experience_package_assocation_table)


class ExperienceAdmin(ExperienceBaseModel):

    @classmethod
    def get_experience_admin_ids(cls):
        '''
        Return a list of experience admin user ids.
        '''
        id_list = [i for (i, ) in Session.query(cls.user_id).all()]
        return id_list

    @classmethod
    def is_user_experience_admin(cls, user):
        '''
        Determine whether passed user is in the experience admin list.
        '''
        return (user.id in cls.get_experience_admin_ids())


def define_experience_admin_table():
    global experience_admin_table

    experience_admin_table = Table('experience_admin', metadata,
                                 Column('user_id', types.UnicodeText,
                                        ForeignKey('user.id',
                                                   ondelete='CASCADE',
                                                   onupdate='CASCADE'),
                                        primary_key=True, nullable=False))

    mapper(ExperienceAdmin, experience_admin_table)
