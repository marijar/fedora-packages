from moksha.connector import IConnector, ICall, IQuery, ParamFilter
from moksha.connector.utils import DateTimeDisplay
from pylons import config
import koji
import re

class KojiConnector(IConnector, ICall, IQuery):
    def __init__(self, environ=None, request=None):
        super(KojiConnector, self).__init__(environ, request)
        self._koji_client = koji.ClientSession(self._base_url)

    # IConnector
    @classmethod
    def register(cls):
        cls._base_url = config.get('fedoracommunity.connector.kojihub.baseurl',
                                   'http://koji.fedoraproject.org/kojihub')

        cls.register_query_builds()
        cls.register_query_packages()
        cls.register_query_changelogs()

    def request_data(self, resource_path, params, _cookies):
        return self._koji_client.callMethod(resource_path, **params)

    def introspect(self):
        # FIXME: return introspection data
        return None

    #ICall
    def call(self, resource_path, params, _cookies=None):
        # koji client only returns structured data so we can pass
        # this off to request_data
        return self.request_data(resource_path, params, _cookies)

    #IQuery
    @classmethod
    def register_query_changelogs(cls):
        path = cls.register_path(
                      'query_changelogs',
                      cls.query_changelogs,
                      primary_key_col = 'id',
                      default_sort_col = 'date',
                      default_sort_order = -1,
                      can_paginate = True)

        path.register_column('id',
                        default_visible = True,
                        can_sort = True,
                        can_filter_wildcards = False)

        path.register_column('date',
                        default_visible = True,
                        can_sort = True,
                        can_filter_wildcards = False)

        path.register_column('author',
                        default_visible = True,
                        can_sort = True,
                        can_filter_wildcards = False)

        path.register_column('text',
                        default_visible = True,
                        can_sort = True,
                        can_filter_wildcards = False)

        f = ParamFilter()
        f.add_filter('package',[], allow_none = False)
        cls._query_changelogs_filter = f

        cls._changelog_version_extract_re = re.compile('(.*)\W*(<.*>)\W*-?\W*(.*)')

    def query_changelogs(self, start_row=None,
                           rows_per_page=10,
                           order=-1,
                           sort_col=None,
                           filters = {},
                           **params):

        filters = self._query_changelogs_filter.filter(filters, conn=self)

        package = filters.get('package', '')

        if order < 0:
            order = '-' + sort_col
        else:
            order = sort_col

        pkg_id = None
        if package:
            pkg_id = self._koji_client.getPackageID(package)

        if not pkg_id:
            return (0, [])

        queryOpts = None

        qo = {}
        if not (start_row == None):
          qo['offset'] = int(start_row)

        if not (rows_per_page == None):
            qo['limit'] = int(rows_per_page)

        if order:
            qo['order'] = order

        if qo:
            queryOpts = qo

        countQueryOpts = {'countOnly': True}

        self._koji_client.multicall = False

        # FIXME: Figure out how to deal with different builds
        #tags = self._koji_client.listTags(package=pkg_id,
        #                                  queryOpts={})

        # ask pkgdb for the collections table
        # pkgdb = get_connector('pkgdb', self._request)
        # collections_table = pkgdb.get_collection_table()

        # get latest version and use that to get the changelog
        builds = self._koji_client.listBuilds(packageID=pkg_id,
                                              queryOpts={'limit': 1,
                                                         'offset': 0,
                                                         'order': '-nvr'})

        build_id = builds[0].get('build_id');
        if not build_id:
            return (0, [])

        self._koji_client.multicall = True
        self._koji_client.getChangelogEntries(buildID=build_id,
                                                queryOpts=countQueryOpts)

        self._koji_client.getChangelogEntries(buildID=build_id,
                                              queryOpts=queryOpts)

        results = self._koji_client.multiCall()

        changelog_list = results[1][0]

        for entry in changelog_list:
            # try to extract a version and e-mail from the authors field
            m = self._changelog_version_extract_re.match(entry['author'])

            entry['author'] = m.group(1)
            entry['email'] = m.group(2)
            entry['version'] = m.group(3)

            # convert the date to a nicer format
            dtd = DateTimeDisplay(entry['date'])
            entry['display_date'] = dtd.when(0)['date'];

        total_count = results[0][0]

        self._koji_client.multicall = False

        return (total_count, changelog_list)

    @classmethod
    def register_query_packages(cls):
        path = cls.register_path(
                      'query_packages',
                      cls.query_packages,
                      primary_key_col = 'id',
                      default_sort_col = 'name',
                      default_sort_order = 1,
                      can_paginate = True)

        path.register_column('id',
                        default_visible = True,
                        can_sort = True,
                        can_filter_wildcards = False)

        path.register_column('name',
                        default_visible = True,
                        can_sort = True,
                        can_filter_wildcards = False)

        f = ParamFilter()
        f.add_filter('prefix',[], allow_none = False)
        cls._query_packages_filter = f

    def query_packages(self, start_row=None,
                           rows_per_page=10,
                           order=1,
                           sort_col=None,
                           filters = {},
                           **params):

        filters = self._query_packages_filter.filter(filters, conn=self)
        prefix = filters.get('prefix')
        terms = '%'
        if prefix:
            terms = prefix + '%'

        countQueryOpts = {'countOnly': True}

        if order < 0:
            order = '-' + sort_col
        else:
            order = sort_col

        if start_row == None:
            start_row = 0

        queryOpts = None

        qo = {}
        if not (start_row == None):
          qo['offset'] = int(start_row)

        if not (rows_per_page == None):
            qo['limit'] = int(rows_per_page)

        if order:
            qo['order'] = order

        if qo:
            queryOpts = qo


        countQueryOpts = {'countOnly': True}

        self._koji_client.multicall = True
        self._koji_client.search(terms=terms,
                                 type='package',
                                 matchType='glob',
                                 queryOpts=countQueryOpts)

        self._koji_client.search(terms=terms,
                                type='package',
                                matchType='glob',
                                queryOpts=queryOpts)

        results = self._koji_client.multiCall()
        pkgs = results[1][0]
        total_count = results[0][0]

        return (total_count, pkgs)

    @classmethod
    def register_query_builds(cls):
        path = cls.register_path(
                      'query_builds',
                      cls.query_builds,
                      primary_key_col = 'build_id',
                      default_sort_col = 'build_id',
                      default_sort_order = -1,
                      can_paginate = True)

        path.register_column('build_id',
                        default_visible = True,
                        can_sort = True,
                        can_filter_wildcards = False)
        path.register_column('nvr',
                        default_visible = True,
                        can_sort = True,
                        can_filter_wildcards = False)
        path.register_column('owner_name',
                        default_visible = True,
                        can_sort = True,
                        can_filter_wildcards = False)
        path.register_column('state',
                        default_visible = True,
                        can_sort = True,
                        can_filter_wildcards = False)

        def _profile_user(conn, filter_dict, key, value, allow_none):
            d = filter_dict

            if value:
                user = None

                ident = conn._environ.get('repoze.who.identity')
                if ident:
                    user = ident.get('repoze.who.userid')

                if user or allow_none:
                    d['user'] = user

        f = ParamFilter()
        f.add_filter('user',['u', 'username', 'name'], allow_none = False)
        f.add_filter('profile',[], allow_none=False,
                     filter_func=_profile_user,
                     cast=bool)
        f.add_filter('package',['p'], allow_none = True)
        f.add_filter('state',['s'], allow_none = True)
        cls._query_builds_filter = f

    def query_builds(self, start_row=None,
                           rows_per_page=10,
                           order=-1,
                           sort_col=None,
                           filters = {},
                           **params):

        filters = self._query_builds_filter.filter(filters, conn=self)

        user = filters.get('user', '')
        package = filters.get('package', '')
        state = filters.get('state')

        complete_before = None
        complete_after = None

        # need a better way to specify this
        # completed_filter = filters.get('completed')
        # if completed_filter:
        #    if completed_filter['op'] in ('>', 'after'):
        #        complete_after = completed_filter['value']
        #    elif completed_filter['op'] in ('<', 'before'):
        #        complete_before = completed_filter['value']

        if order < 0:
            order = '-' + sort_col
        else:
            order = sort_col

        user = self._koji_client.getUser(user)

        id = None
        if user:
            id = user['id']

        pkg_id = None
        if package:
            pkg_id = self._koji_client.getPackageID(package)

        queryOpts = None

        if state:
            state = int(state)

        qo = {}
        if not (start_row == None):
          qo['offset'] = int(start_row)

        if not (rows_per_page == None):
            qo['limit'] = int(rows_per_page)

        if order:
            qo['order'] = order

        if qo:
            queryOpts = qo

        countQueryOpts = {'countOnly': True}

        self._koji_client.multicall = True
        self._koji_client.listBuilds(packageID=pkg_id,
                      userID=id,
                      state=state,
                      completeBefore = complete_before,
                      completeAfter = complete_after,
                      queryOpts=countQueryOpts)

        self._koji_client.listBuilds(packageID=pkg_id,
                      userID=id,
                      state=state,
                      completeBefore = complete_before,
                      completeAfter = complete_after,
                      queryOpts=queryOpts)

        results = self._koji_client.multiCall()
        builds_list = results[1][0]
        total_count = results[0][0]
        for b in builds_list:
            start = b['creation_time']
            complete = b['completion_time']
            completion_display = None
            if not complete:
                dtd = DateTimeDisplay(start)
                completion_display = {'when': 'In progress...',
                                    'should_display_time': False,
                                    'time': ''}
                elapsed = dtd.time_elapsed(0)
                completion_display['elapsed'] = elapsed['display']
            else:
                dtd = DateTimeDisplay(start, complete)
                completion_display = dtd.when(1)
                elapsed = dtd.time_elapsed(0,1)
                completion_display['elapsed'] = elapsed['display']

            b['completion_time_display'] = completion_display

        self._koji_client.multicall = False

        return (total_count, builds_list)
