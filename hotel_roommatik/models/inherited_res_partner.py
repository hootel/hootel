# Copyright 2018 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from odoo import _, api, fields, models


class ResPartner(models.Model):

    _inherit = 'res.partner'

    @api.model
    def rm_add_customer(self, customer):
        partner_res = self.env['res.partner'].search(
            [('name', '=', customer['FirstName'])])
        # Need a smart search function here (Check name, document, mail) return unique or null customer.

        json_response = dict()
        if any(partner_res):
            json_response = {
                "Id": partner_res.id,
                "FirstName": partner_res.name,
                "LastName1": "Null",
                "LastName2": "Null",
                "Birthday": "Null",
                "Sex": "Null",
                "Address": [{
                    "Nationality": "Null",
                    "Country": partner_res.country_id.name,
                    "ZipCode": partner_res.zip,
                    "City": partner_res.city,
                    "Street": partner_res.street,
                    "House": "Null",
                    "Flat": "Null",
                    "Number": "Null",
                    "Province": "Null",
                }],
                "IdentityDocument": [{
                    "Number": "Null",
                    "Type": "Null",
                    "ExpiryDate": "dateTime",
                    "ExpeditionDate": "dateTime",
                    "Street": "Null",
                    "House": "Null",
                    "Flat": "Null",
                    "Number": "Null",
                    "Province": "Null",
                }],
                "Contact": [{
                    "Telephone": partner_res.phone,
                    "Fax": "Null",
                    "Mobile": partner_res.mobile,
                    "Email": partner_res.email,
                }]
            }
        else:
            # Create new customer
            json_response = {'Id': 0}
        # Debug Stop -------------------
        #import wdb; wdb.set_trace()
        # Debug Stop -------


        # Id: será 0 en la solicitud y será diferente de 0 si el cliente se ha creado
        # correctamente en el PMS.
        # FirstName: nombre.
        # LastName1: primer apellido.
        # LastName2: segundo apellido.
        # Birthday: fecha de nacimiento.
        # Sex: sexo. Puede ser “M” para masculino o “F” para femenino.
        # IdentityDocument: documento de identidad, formado por los siguientes
        # valores:
        # o Number: número de documento.
        # o Type: tipo de documento. Puede ser:
        # ▪ C: permiso de conducir.
        # ▪ X: permiso de residencia europeo.
        # ▪ D: DNI.
        # ▪ I: documento de identidad.
        # ▪ P: pasaporte.
        # ▪ N: permiso de residencia español.
        # o Expedition: fecha de expedición.
        # o Expiration: fecha de caducidad.
        # Address: dirección, formada por los siguientes valores:
        # o City: ciudad.
        # o Country: país (código ISO 3).
        # o Flat: piso.
        # o Nationality: nacionalidad (código ISO 3).
        # o Number: número.
        # o StateOrProvince: estado o provincia.
        # o Street: calle.
        # o ZipCode: código postal.

        json_response = json.dumps(json_response)

        return json_response
