# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from contextlib import contextmanager
from odoo import models, api, fields
from ...components.backend_adapter import WuBookLogin, WuBookServer


class ChannelBackend(models.Model):
    _inherit = 'channel.backend'

    @api.model
    def select_versions(self):
        """ Available versions in the backend.
        Can be inherited to add custom versions.  Using this method
        to add a version from an ``_inherit`` does not constrain
        to redefine the ``version`` field in the ``_inherit`` model.
        """
        super(ChannelBackend, self).select_versions()
        return [('1.2', '1.2+')]

    def _get_default_server(self):
        super(ChannelBackend, self)._get_default_server()
        return 'https://wired.wubook.net/xrws/'

    lcode = fields.Char('Channel Service lcode')
    pkey = fields.Char('Channel Service PKey')

    @contextmanager
    @api.multi
    def work_on(self, model_name, **kwargs):
        self.ensure_one()
        wubook_login = WuBookLogin(
            self.server,
            self.username,
            self.passwd,
            self.lcode,
            self.pkey)
        with WuBookServer(wubook_login) as channel_api:
            _super = super(ChannelBackend, self)
            with _super.work_on(model_name, channel_api=channel_api, **kwargs) as work:
                yield work
