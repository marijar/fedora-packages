from tg import expose, tmpl_context

from moksha.lib.base import Controller
from moksha.lib.helpers import Category, MokshaApp
from helpers import PackagesDashboardContainer

class UpdatesDashboard(PackagesDashboardContainer):
    template = 'mako:fedoracommunity.mokshaapps.packages.templates.single_col_dashboard'
    layout = [Category('content-col-apps',
                       MokshaApp('Updates', 'fedoracommunity.updates/table',
                                 params={'filters':{'package':''}}))]

updates_dashboard = UpdatesDashboard('updates_dashboard')

class UpdatesController(Controller):
    @expose('mako:moksha.templates.widget')
    def index(self, package):
        tmpl_context.widget = updates_dashboard
        return {'options':{'package': package}}
