# This file is part of Fedora Community.
# Copyright (C) 2008-2010  Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
import logging

from paste.deploy.converters import asbool
from tg import config
from fedora.client import ProxyClient
from datetime import datetime, timedelta
from webhelpers.date import distance_of_time_in_words
from webhelpers.html import HTML

from fedoracommunity.connectors.api import get_connector
from fedoracommunity.connectors.api import IConnector, ICall, IQuery, ParamFilter
from moksha.common.lib.dates import DateTimeDisplay

from fedoracommunity.lib.utils import parse_build

log = logging.getLogger(__name__)

class BodhiConnector(IConnector, ICall, IQuery):
    _method_paths = {}
    _query_paths = {}

    def __init__(self, environ, request):
        super(BodhiConnector, self).__init__(environ, request)
        self._prod_url = config.get('fedoracommunity.connector.bodhi.produrl', 'https://admin.fedoraproject.org/updates')
        self._bodhi_client = ProxyClient(self._base_url,
                                         session_as_cookie=False,
                                         insecure = self._insecure)

    # IConnector
    @classmethod
    def register(cls):
        cls._base_url = config.get('fedoracommunity.connector.bodhi.baseurl',
                                   'https://admin.fedoraproject.org/updates')

        check_certs = asbool(config.get('fedora.clients.check_certs', True))
        cls._insecure = not check_certs

        cls.register_query_updates()
        cls.register_query_active_releases()

    def request_data(self, resource_path, params, _cookies):
        auth_params={}

        fas_info = self._environ.get('FAS_LOGIN_INFO')
        if fas_info:
            session_id = fas_info[0]
            auth_params={'session_id': session_id}

        return self._bodhi_client.send_request(resource_path,
                                               req_params=params,
                                               auth_params=auth_params)

    def introspect(self):
        # FIXME: return introspection data
        return None

    #ICall
    def call(self, resource_path, params, _cookies=None):
        log.debug('BodhiConnector.call(%s)' % locals())
        # proxy client only returns structured data so we can pass
        # this off to request_data but we should fix that in ProxyClient
        return self.request_data(resource_path, params, _cookies)

    #IQuery
    @classmethod
    def register_query_updates(cls):
        path = cls.register_query(
                      'query_updates',
                      cls.query_updates,
                      primary_key_col = 'request_id',
                      default_sort_col = 'request_id',
                      default_sort_order = -1,
                      can_paginate = True)

        path.register_column('request_id',
                        default_visible = False,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('updateid',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('nvr',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('submitter',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('status',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('request',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('karma',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('nagged',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('type',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('approved',
                        default_visible = True,
                        can_sort = False,
                     can_filter_wildcards = False)
        path.register_column('date_submitted',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('date_pushed',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('date_modified',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('comments',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('bugs',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('builds',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('releases',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('release',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)
        path.register_column('karma_level',
                        default_visible = True,
                        can_sort = False,
                        can_filter_wildcards = False)

        def _profile_user(conn, filter_dict, key, value, allow_none):
            if value:
                user = None
                ident = conn._environ.get('repoze.who.identity')
                if ident:
                    user = ident.get('repoze.who.userid')
                if user or allow_none:
                    filter_dict['username'] = user

        f = ParamFilter()
        f.add_filter('package', ['nvr'], allow_none=False)
        f.add_filter('user',['u', 'username', 'name'], allow_none = False)
        f.add_filter('profile',[], allow_none=False,
                     filter_func=_profile_user,
                     cast=bool)
        f.add_filter('status',['status'], allow_none = True)
        f.add_filter('group_updates', allow_none=True, cast=bool)
        f.add_filter('granularity', allow_none=True)
        f.add_filter('release', allow_none=False)
        cls._query_updates_filter = f

    def query_updates(self, start_row=None,
                            rows_per_page=None,
                            order=-1,
                            sort_col=None,
                            filters=None,
                            **params):
        if not filters:
            filters = {}

        filters = self._query_updates_filter.filter(filters, conn=self)
        group_updates = filters.get('group_updates', True)

        params.update(filters)
        params['tg_paginate_no'] = int(start_row/rows_per_page) + 1

        # If we're grouping updates, ask for twice as much.  This is so we can
        # handle the case where there are two updates for each package, one for
        # each release.  Yes, worst case we get twice as much data as we ask
        # for, but this allows us to do *much* more efficient database calls on
        # the server.
        if group_updates:
            params['tg_paginate_limit'] = rows_per_page * 2
        else:
            params['tg_paginate_limit'] = rows_per_page

        results = self._bodhi_client.send_request('list', req_params=params)

        total_count = results[1]['num_items']

        if group_updates:
            updates_list = self._group_updates(results[1]['updates'],
                                               num_packages=rows_per_page)
        else:
            updates_list = results[1]['updates']

        for up in updates_list:
            versions = []
            releases = []

            if group_updates:
                up['title'] = up['dist_updates'][0]['title']

                for dist_update in up['dist_updates']:
                    versions.append(dist_update['version'])
                    releases.append(dist_update['release_name'])

                up['name'] = up['package_name']

                up['versions'] = versions
                up['releases'] = releases
                up['status'] = up['dist_updates'][0]['status']
                up['nvr'] = up['dist_updates'][0]['title']
                up['request_id'] = up['package_name'] + dist_update['version'].replace('.', '')
            else:
                chunks = up['title'].split('-')
                up['name'] = '-'.join(chunks[:-2])
                up['version'] = '-'.join(chunks[-2:])
                up['versions'] = chunks[-2]
                up['releases'] = up['release']['long_name']
                up['nvr'] = up['title']
                up['request_id'] = up.get('updateid') or \
                        up['nvr'].replace('.', '').replace(',', '')

            up['id'] = up['nvr'].split(',')[0]

            # A unique id that we can use in HTML class fields.
            #up['request_id'] = up.get('updateid') or \
            #        up['nvr'].replace('.', '').replace(',', '')

            actions = []

            # Right now we're making the assumption that if you're logged
            # in, we query by your username, thus you should be able to
            # modify these updates.  This way, we avoid the pkgdb calls.
            # Ideally, we should get the real ACLs from the pkgdb connector's
            # cache.
            if filters.get('username'):
                # If we have multiple updates that are all in the same state,
                # then create a single set of action buttons to control all
                # of them.  If not,then supply separate ones.
                if 'dist_updates' in up and len(up['dist_updates']) > 1:
                    if up['dist_updates'][0]['status'] != \
                       up['dist_updates'][1]['status']:
                        for update in up['dist_updates']:
                            for action in self._get_update_actions(update):
                                actions.append(action)
                    else:
                        for update in up['dist_updates']:
                            for action in self._get_update_actions(update):
                                actions.append(action)
                else:
                    # Create a single set of action buttons
                    if 'dist_updates' in up:
                        update = up['dist_updates'][0]
                    else:
                        update = up
                    for action in self._get_update_actions(update):
                        actions.append(action)

            up['actions'] = ''
            for action in actions:
                reqs = ''
                if group_updates:
                    for u in up['dist_updates']:
                        reqs += "update_action('%s', '%s');" % (u['title'],
                                                                action[0])
                    title = up['dist_updates'][0]['title']
                else:
                    reqs += "update_action('%s', '%s');" % (up['title'],
                                                            action[0])
                    title = up['title']

                # FIXME: Don't embed HTML
                up['actions'] += """
                    <button id="%s_%s" onclick="%s return false;">%s</button><br/>
                    """ % (title.replace('.', ''), action[0], reqs, action[1])

            # Dates
            if group_updates:
                date_submitted = up['dist_updates'][0]['date_submitted']
                date_pushed = up['dist_updates'][0]['date_pushed']
            else:
                date_submitted = up['date_submitted']
                date_pushed = up['date_pushed']

            granularity = filters.get('granularity', 'day')
            ds = DateTimeDisplay(date_submitted)
            up['date_submitted_display'] = ds.age(granularity=granularity,
                                                  general=True) + ' ago'

            if date_pushed:
                dp = DateTimeDisplay(date_pushed)
                up['date_pushed'] = dp.datetime.strftime('%d %b %Y')
                up['date_pushed_display'] = dp.age(granularity=granularity,
                                                   general=True) + ' ago'

            # karma
            # FIXME: take into account karma from both updates
            if group_updates:
                k = up['dist_updates'][0]['karma']
            else:
                k = up['karma']
            if k:
                up['karma_str'] = "%+d"%k
            else:
                up['karma_str'] = " %d"%k
            up['karma_level'] = 'meh'
            if k > 0:
                up['karma_level'] = 'good'
            if k < 0:
                up['karma_level'] = 'bad'

            up['details'] = self._get_update_details(up)

        return (total_count, updates_list)

    def _get_update_details(self, update):
        details = ''
        if update['status'] == 'stable':
            if update.get('updateid'):
                details += HTML.tag('a', c=update['updateid'], href='%s/%s' % (
                                    self._prod_url, update['updateid']))
            if update.get('date_pushed'):
                details += HTML.tag('br') + update['date_pushed']
            else:
                details += 'In process...'
        elif update['status'] == 'pending' and update.get('request'):
            details += 'Pending push to %s' % update['request']
            details += HTML.tag('br')
            details += HTML.tag('a', c="View update details >",
                                href="%s/%s" % (self._prod_url,
                                                update['title']))
        elif update['status'] == 'obsolete':
            for comment in update['comments']:
                if comment['author'] == 'bodhi':
                    if comment['text'].startswith('This update has been obsoleted by '):
                        details += 'Obsoleted by %s' % HTML.tag('a',
                                href='%s/%s' % (self._prod_url,update['title']),
                                c=comment['text'].split()[-1])
        return details

    def _get_update_actions(self, update):
        actions = []
        if update['request']:
            actions.append(('revoke', 'Cancel push'))
        else:
            if update['status'] == 'testing':
                actions.append(('unpush', 'Unpush'))
                actions.append(('stable', 'Push to stable'))
            if update['status'] == 'pending':
                actions.append(('testing', 'Push to testing'))
                actions.append(('stable', 'Push to stable'))
        return actions

    def _group_updates(self, updates, num_packages=None):
        """
        Group a list of updates by release.
        This method allows allows you to limit the number of packages,
        for when we want to display 1 package per row, regardless of how
        many updates there are for it.
        """
        packages = {}
        done = False
        i = 0

        if not updates:
            return []

        for update in updates:
            for build in update['builds']:
                pkg = build['package']['name']
                if pkg not in packages:
                    if num_packages and i >= num_packages:
                        done = True
                        break
                    packages[pkg] = {
                            'package_name' : pkg,
                            'dist_updates': []
                            }
                    i += 1
                else:
                    skip = False
                    for up in packages[pkg]['dist_updates']:
                        if up['release_name'] == update['release']['long_name']:
                            skip = True
                            break
                    if skip:
                        break
                packages[pkg]['dist_updates'].append({
                        'release_name': update['release']['long_name'],
                        'version': '-'.join(build['nvr'].split('-')[-2:])
                        })
                packages[pkg]['dist_updates'][-1].update(update)
            if done:
                break

        result = [packages[pkg] for pkg in packages]

        sort_col = 'date_submitted'
        if result[0]['dist_updates'][0]['status'] == 'stable':
            sort_col = 'date_pushed'

        result = sorted(result, reverse=True, cmp=lambda x, y:
                     cmp(x['dist_updates'][0][sort_col],
                         y['dist_updates'][0][sort_col]))

        return result

    def get_dashboard_stats(self, username=None):
        bodhi_cache = self._request.environ['beaker.cache'].get_cache('bodhi')
        return bodhi_cache.get_value(key='dashboard_%s' % username,
                createfunc=lambda: self._get_dashboard_stats(username),
                expiretime=300)

    def _get_dashboard_stats(self, username):
        options = {}
        results = {}

        if username:
            options['username'] = username

        for status in ('pending', 'testing'):
            options['status'] = status
            results[status] = self.query_updates_count(**options)['count']

        now = datetime.utcnow()
        options['status'] = 'stable'
        options['after'] = week_start = now - timedelta(weeks=1)
        results['stable'] = self.query_updates_count(**options)['count']

        return results

    def query_updates_count(self, status, username=None,
                            before=None, after=None):
        bodhi_cache = self._request.environ['beaker.cache'].get_cache('bodhi')
        return bodhi_cache.get_value(key='count_%s_%s_%s_%s' % (
                status, username, str(before).split('.')[0],
                str(after).split('.')[0]), expiretime=300,
                createfunc=lambda: self._query_updates_count(status, username,
                                                             before, after))

    def _query_updates_count(self, status, username, before, after):
        params = {'count_only': True}
        label = status + ' updates pushed'

        if username:
            params['username'] = username
        if status:
            params['status'] = status
        if before:
            before = str(before)
            params['end_date'] = before.split('.')[0]
        if after:
            after = str(after)
            params['start_date'] = after.split('.')[0]

        count = self.call('list', params)[1]['num_items']

        return {'count': count, 'label': label, 'state': status}

    def add_updates_to_builds(self, builds):
        """Update a list of koji builds with the corresponding bodhi updates.

        This method makes a single query to bodhi, asking if it knows about
        any updates for a given list of koji builds.  For builds with existing
        updates, the `update` will be added to it's dictionary.

        Currently it also adds `update_details`, which is HTML for rendering
        the builds update options.  Ideally, this should be done client-side
        in the template (builds/templates/table_widget.mak).

        """
        start = datetime.now()
        updates = self.call('get_updates_from_builds', {
            'builds': ' '.join([b['nvr'] for b in builds])})
        if updates:
            # FIXME: Lets stop changing the upstream APIs by putting the
            # session id as the first element, and the results in the second.
            updates = updates[1]

        for build in builds:
            if build['nvr'] in updates:
                build['update'] = updates[build['nvr']]
                status = build['update']['status']
                details = ''
                # FIXME: ideally, we should just return the update JSON and do
                # this logic client-side in the template when the grid data
                # comes in.
                if status == 'stable':
                    details = 'Pushed to updates'
                elif status == 'testing':
                    details = 'Pushed to updates-testing'
                elif status == 'pending':
                    details = 'Pending push to %s' % build['update']['request']

                details += HTML.tag('br')
                details += HTML.tag('a', c="View update details >",
                                    href="%s/%s" % (self._prod_url,
                                                    build['update']['title']))
            else:
                details = HTML.tag('a', c='Push to updates >',
                                   href='%s/new?builds.text=%s' % (
                                       self._prod_url, build['nvr']))

            build['update_details'] = details

        log.debug("Queried bodhi for builds in: %s" %  (datetime.now() - start))

    @classmethod
    def register_query_active_releases(cls):
        path = cls.register_query('query_active_releases',
                                  cls.query_active_releases,
                                  primary_key_col='release',
                                  default_sort_col='release',
                                  default_sort_order=-1,
                                  can_paginate=True)
        path.register_column('release',
                             default_visible=True,
                             can_sort=False,
                             can_filter_wildcards=False)
        path.register_column('stable_version',
                             default_visible=True,
                             can_sort=False,
                             can_filter_wildcards=False)
        path.register_column('testing_version',
                             default_visible=True,
                             can_sort=False,
                             can_filter_wildcards=False)

        f = ParamFilter()
        f.add_filter('package', ['nvr'], allow_none=False)
        cls._query_active_releases = f

    def query_active_releases(self, filters=None, **params):
        releases = []
        queries = []
        release_tag = {} # Mapping of tag -> release
        testing_builds = [] # List of testing builds to query bodhi for
        testing_builds_row = {} # nvr -> release lookup table
        if not filters: filters = {}
        filters = self._query_updates_filter.filter(filters, conn=self)
        package = filters.get('package')
        pkgdb = get_connector('pkgdb')
        koji = get_connector('koji')._koji_client
        koji.multicall = True

        for release in pkgdb.get_fedora_releases():
            tag = release[0]
            name = release[1]
            r = {'release': name, 'stable_version': 'None',
                 'testing_version': 'None'}
            if tag == 'rawhide':
                koji.listTagged(tag, package=package, latest=True, inherit=True)
                queries.append(tag)
                release_tag[tag] = r
            else:
                if tag.endswith('epel'):
                    stable_tag = tag
                    testing_tag = tag + '-testing'
                else:
                    stable_tag = tag + '-updates'
                    testing_tag = stable_tag + '-testing'
                koji.listTagged(stable_tag, package=package,
                                latest=True, inherit=True)
                queries.append(stable_tag)
                release_tag[stable_tag] = r
                koji.listTagged(testing_tag, package=package, latest=True)
                queries.append(testing_tag)
                release_tag[testing_tag] = r
            releases.append(r)

        results = koji.multiCall()

        for i, result in enumerate(results):
            if isinstance(result, dict):
                if 'faultString' in result:
                    log.error("FAULT: %s" % result['faultString'])
                else:
                    log.error("Can't find fault string in result: %s" % result)
            else:
                query = queries[i]
                row = release_tag[query]
                release = result[0]

                if query == 'dist-rawhide':
                    if release:
                        nvr = parse_build(release[0]['nvr'])
                        row['stable_version'] = '%(version)s-%(release)s' % nvr
                    else:
                        row['stable_version'] = 'No builds tagged with %s' % tag
                    row['testing_version'] = HTML.tag('i', c='Not Applicable')
                    continue
                if release:
                    release = release[0]
                    if query.endswith('-testing'):
                        nvr = parse_build(release['nvr'])
                        row['testing_version'] = HTML.tag('a',
                                c='%(version)s-%(release)s' % nvr,
                                href='%s/%s' % (self._prod_url, nvr['nvr']))
                        testing_builds.append(release['nvr'])
                        testing_builds_row[release['nvr']] = row
                    else: # stable
                        nvr = parse_build(release['nvr'])
                        if release['tag_name'].endswith('-updates'):
                            row['stable_version'] = HTML.tag('a',
                                    c='%(version)s-%(release)s' % nvr,
                                    href='%s/%s' % (self._prod_url, nvr['nvr']))
                        else:
                            row['stable_version'] = '%(version)s-%(release)s' % nvr

        # If there are updates in testing, then query bodhi with a single call
        if testing_builds:
            updates = self.call('get_updates_from_builds', {
                'builds': ' '.join(testing_builds)
                })
            if updates[1]:
                for build in updates[1]:
                    if build == 'tg_flash':
                        continue
                    up = updates[1][build]
                    if up.karma > 1:
                        up.karma_icon = 'good'
                    elif up.karma < 0:
                        up.karma_icon = 'bad'
                    else:
                        up.karma_icon = 'meh'
                    karma_icon_url = self._request.environ['SCRIPT_NAME'] + \
				'/images/16_karma-%s.png' % up.karma_icon
                    row = testing_builds_row[build]
                    row['testing_version'] += HTML.tag('div',
                            c=HTML.tag('a', href="%s/%s" % (
                                self._prod_url, up.title),
                                c=HTML.tag('img',
                                    src=karma_icon_url) +
                                HTML.tag('span', c='%s karma' %
                                    up.karma)),
                                **{'class': 'karma'})

        return (len(releases), releases)

    def get_metrics(self):
        bodhi_cache = self._request.environ['beaker.cache'].get_cache('bodhi')
        return bodhi_cache.get_value(key='bodhi_metrics',
                createfunc=self._get_metrics,
                expiretime=300)

    def _get_metrics(self):
        return self._bodhi_client.send_request('metrics')[1]
