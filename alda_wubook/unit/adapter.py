# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.addons.connector.unit.backend_adapter import CRUDAdapter
from openerp.addons.connector.exception import (NetworkRetryableError,
                                                RetryableJobError)


class WuBookCRUDAdapter(CRUDAdapter):
    def __init__(self, connector_env):
        """
        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(WuBookCRUDAdapter, self).__init__(connector_env)
        backend = self.backend_record
        magento = MagentoLocation(
            backend.location,
            backend.username,
            backend.password,
            use_custom_api_path=backend.use_custom_api_path)
        if backend.use_auth_basic:
            magento.use_auth_basic = True
            magento.auth_basic_username = backend.auth_basic_username
            magento.auth_basic_password = backend.auth_basic_password
        self.magento = magento

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        raise NotImplementedError

    def create(self, data):
        """ Create a record on the external system """
        raise NotImplementedError

    def write(self, id, data):
        """ Update records on the external system """
        raise NotImplementedError

    def delete(self, id):
        """ Delete a record on the external system """
        raise NotImplementedError
    