# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 Alexandre Díaz <dev@redneboa.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from io import BytesIO
import datetime
import pytz
import xlsxwriter
import base64
from odoo import api, fields, models, _
from openerp.exceptions import UserError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class CashDailyReportWizard(models.TransientModel):
    FILENAME = 'cash_daily_report.xls'
    _name = 'cash.daily.report.wizard'

    @api.model
    def automatic_period_lock_date(self):
        # The secong month day close the mont previous
        days = 2
        closeday = datetime.date.today().replace(day=days)
        if datetime.date.today() >= closeday:
            companies = self.env['res.company'].search([])
            for record in companies:
                lastday = datetime.date.today().replace(day=1) + \
                    datetime.timedelta(days=-1)
                lastday_str = lastday.strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
                if record.period_lock_date != lastday:
                    record.write({
                      'period_lock_date': lastday_str
                    })

    @api.model
    def _get_default_date_start(self):
        return datetime.datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

    @api.model
    def _get_default_date_end(self):
        return datetime.datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

    date_start = fields.Date("Start Date", default=_get_default_date_start)
    date_end = fields.Date("End Date", default=_get_default_date_end)
    xls_filename = fields.Char()
    xls_binary = fields.Binary()

    @api.model
    def _export(self):
        user = self.env['res.users'].browse(self.env.uid)
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data, {
            'strings_to_numbers': True,
            'default_date_format': 'dd/mm/yyyy'
        })
        cell_format = workbook.add_format({'bold': True, 'font_color': 'red'})
        validated_format = workbook.add_format({
            'bold': True,
            'bg_color': '#00FF00',
            'num_format': '#,##0.00'})
        company_id = self.env.user.company_id
        workbook.set_properties({
            'title': 'Exported data from ' + company_id.name,
            'subject': 'Payments Data from Odoo of ' + company_id.name,
            'author': 'Odoo',
            'manager': u'Alexandre Díaz Cuadrado',
            'company': company_id.name,
            'category': 'Hoja de Calculo',
            'keywords': 'payments, odoo, data, ' + company_id.name,
            'comments': 'Created with Python in Odoo and XlsxWriter'})
        workbook.use_zip64()

        xls_cell_format_date = workbook.add_format({
            'num_format': 'dd/mm/yyyy'
        })
        xls_cell_format_money = workbook.add_format({
            'num_format': '#,##0.00'
        })
        xls_cell_format_header = workbook.add_format({
            'bg_color': '#CCCCCC'
        })

        worksheet = workbook.add_worksheet(_('Cash Daily Report'))

        worksheet.write('A1', _('Name'), xls_cell_format_header)
        worksheet.write('B1', _('Reference'), xls_cell_format_header)
        worksheet.write('C1', _('Client/Supplier'), xls_cell_format_header)
        worksheet.write('D1', _('Date'), xls_cell_format_header)
        worksheet.write('E1', _('Journal'), xls_cell_format_header)
        worksheet.write('F1', _('Amount'), xls_cell_format_header)
        worksheet.write('G1', _('Tipo'), xls_cell_format_header)

        worksheet.set_column('C:C', 30)
        worksheet.set_column('D:D', 11)
        worksheet.set_column('E:E', 10)
        worksheet.set_column('F:F', 12)

        account_payments_obj = self.env['account.payment']
        account_payments = account_payments_obj.search([
            ('payment_date', '>=', self.date_start),
            ('payment_date', '<=', self.date_end),
        ])
        offset = 1
        total_account_payment_amount = 0.0
        total_account_payment = 0.0
        total_account_expenses = 0.0
        payment_journals = {}
        expense_journals = {}
        count_payment_journals = {}
        count_expense_journals = {}
        total_dates = {}
        for k_payment, v_payment in enumerate(account_payments):
            where = v_payment.partner_id.name
            amount = v_payment.amount if v_payment.payment_type in ('inbound') \
                else -v_payment.amount
            if v_payment.payment_type == 'transfer':
                ingresos = 'Ingresos ' + v_payment.destination_journal_id.name
                gastos = 'Gastos ' + v_payment.destination_journal_id.name
                where = v_payment.destination_journal_id.name
                total_account_payment += -amount
                if v_payment.destination_journal_id.name not in payment_journals:
                    payment_journals.update({v_payment.destination_journal_id.name: -amount})
                    count_payment_journals.update({v_payment.destination_journal_id.name: 1})
                else:
                    payment_journals[v_payment.destination_journal_id.name] += -amount
                    count_payment_journals[v_payment.destination_journal_id.name] += 1
                if v_payment.payment_date not in total_dates:
                    total_dates.update({v_payment.payment_date: {v_payment.destination_journal_id.name: -amount}})
                    total_dates[v_payment.payment_date].update({ingresos: -amount})
                    total_dates[v_payment.payment_date].update({gastos: 0})
                else:
                    if v_payment.destination_journal_id.name not in total_dates[v_payment.payment_date]:
                        total_dates[v_payment.payment_date].update({ingresos: -amount})
                        total_dates[v_payment.payment_date].update({gastos: 0})
                        total_dates[v_payment.payment_date].update({v_payment.destination_journal_id.name: -amount})
                    else:
                        total_dates[v_payment.payment_date][ingresos] += -amount
                        total_dates[v_payment.payment_date][v_payment.destination_journal_id.name] += -amount
            if amount < 0:
                ingresos = 'Ingresos ' + v_payment.journal_id.name
                gastos = 'Gastos ' + v_payment.journal_id.name
                total_account_expenses += -amount
                if v_payment.journal_id.name not in expense_journals:
                    expense_journals.update({v_payment.journal_id.name: amount})
                    count_expense_journals.update({v_payment.journal_id.name: 1})
                else:
                    expense_journals[v_payment.journal_id.name] += amount
                    count_expense_journals[v_payment.journal_id.name] += 1
                if v_payment.payment_date not in total_dates:
                    total_dates.update({v_payment.payment_date: {v_payment.journal_id.name: amount}})
                    total_dates[v_payment.payment_date].update({gastos: -amount})
                    total_dates[v_payment.payment_date].update({ingresos: 0})
                else:
                    if v_payment.journal_id.name not in total_dates[v_payment.payment_date]:
                        total_dates[v_payment.payment_date].update({v_payment.journal_id.name: amount})
                        total_dates[v_payment.payment_date].update({gastos: -amount})
                        total_dates[v_payment.payment_date].update({ingresos: 0})
                    else:
                        total_dates[v_payment.payment_date][gastos] += -amount
                        total_dates[v_payment.payment_date][v_payment.journal_id.name] += amount
            else:
                ingresos = 'Ingresos ' + v_payment.journal_id.name
                gastos = 'Gastos ' + v_payment.journal_id.name
                total_account_payment += amount
                if v_payment.journal_id.name not in payment_journals:
                    payment_journals.update({v_payment.journal_id.name: amount})
                    count_payment_journals.update({v_payment.journal_id.name: 1})
                else:
                    payment_journals[v_payment.journal_id.name] += amount
                    count_payment_journals[v_payment.journal_id.name] += 1
                if v_payment.payment_date not in total_dates:
                    total_dates.update({v_payment.payment_date: {v_payment.journal_id.name: amount}})
                    total_dates[v_payment.payment_date].update({ingresos: amount})
                    total_dates[v_payment.payment_date].update({gastos: 0})
                else:
                    if v_payment.journal_id.name not in total_dates[v_payment.payment_date]:
                        total_dates[v_payment.payment_date].update({v_payment.journal_id.name: amount})
                        total_dates[v_payment.payment_date].update({ingresos: amount})
                        total_dates[v_payment.payment_date].update({gastos: 0})
                    else:
                        total_dates[v_payment.payment_date][v_payment.journal_id.name] += amount
                        total_dates[v_payment.payment_date][ingresos] += amount

            worksheet.write(k_payment+offset, 0, v_payment.create_uid.login)
            worksheet.write(k_payment+offset, 1, v_payment.communication)
            worksheet.write(k_payment+offset, 2, where)
            worksheet.write(k_payment+offset, 3, v_payment.payment_date,
                            xls_cell_format_date)
            worksheet.write(k_payment+offset, 4, v_payment.journal_id.name)
            if v_payment.validated:
                worksheet.write(k_payment+offset, 5, amount,
                                validated_format)
            else:
                worksheet.write(k_payment+offset, 5, amount,
                                xls_cell_format_money)
            if v_payment.partner_type == 'customer':
                tipo_operacion = "Cliente"
            elif v_payment.partner_type == 'supplier':
                tipo_operacion = "Proveedor"
            else:
                tipo_operacion = "Interna"
            worksheet.write(k_payment+offset, 6, tipo_operacion)
            total_account_payment_amount += amount

        payment_returns_obj = self.env['payment.return']
        payment_returns = payment_returns_obj.search([
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
        ])
        offset += len(account_payments)
        total_payment_returns_amount = k_line = 0.0
        return_journals = {}
        count_return_journals = {}
        for k_payment, v_payment in enumerate(payment_returns):
            for k_line, v_line in enumerate(v_payment.line_ids):
                ingresos = 'Ingresos ' + v_payment.journal_id.name
                gastos = 'Gastos ' + v_payment.journal_id.name
                if v_payment.journal_id.name not in return_journals:
                    return_journals.update({v_payment.journal_id.name: -v_line.amount})
                    count_return_journals.update({v_payment.journal_id.name : 1})
                else:
                    return_journals[v_payment.journal_id.name] += -v_line.amount
                    count_return_journals[v_payment.journal_id.name] += 1
                if v_payment.date not in total_dates:
                    total_dates.update({v_payment.date: {v_payment.journal_id.name: -v_line.amount}})
                    total_dates[v_payment.date].update({gastos: -v_line.amount})
                    total_dates[v_payment.date].update({ingresos: 0})
                else:
                    if v_payment.journal_id.name not in total_dates[v_payment.date]:
                        total_dates[v_payment.date].update({v_payment.journal_id.name: -v_line.amount})
                        total_dates[v_payment.date].update({gastos: -v_line.amount})
                        total_dates[v_payment.date].update({ingresos: 0})
                    else:
                        total_dates[v_payment.date][v_payment.journal_id.name] += -v_line.amount
                        total_dates[v_payment.date][gastos] += -v_line.amount

                worksheet.write(k_line+offset, 0, v_payment.create_uid.login)
                worksheet.write(k_line+offset, 1, v_line.reference)
                worksheet.write(k_line+offset, 2, v_line.partner_id.name)
                worksheet.write(k_line+offset, 3, v_payment.date,
                                xls_cell_format_date)
                worksheet.write(k_line+offset, 4, v_payment.journal_id.name)
                if v_payment.validated:
                    worksheet.write(k_line+offset, 5, -v_line.amount,
                                    validated_format)
                else:
                    worksheet.write(k_line+offset, 5, -v_line.amount,
                                    xls_cell_format_money)
                worksheet.write(k_line+offset, 6, "Devolucion")
                total_payment_returns_amount += -v_line.amount
            offset += len(v_payment.line_ids)
        line = offset
        if k_line:
            line = k_line + offset

        worksheet.write(line + 1, 1, "Fecha/Hora:", cell_format)
        timezone = pytz.timezone(self._context.get('tz') or 'UTC')
        event_date = datetime.datetime.now()
        event_date = pytz.UTC.localize(event_date)

        event_date = event_date.astimezone(timezone)
        event_date = event_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        worksheet.write(line + 2, 1, event_date, cell_format)

        account_cash_ids = self.env['account.journal'].search([('type','=','cash')])
        for account in account_cash_ids:
            result_cash = account.get_journal_dashboard_datas().get('account_balance')
            worksheet.write(line + 3, 1, account.name, cell_format)
            worksheet.write(line + 4, 1, result_cash, cell_format)

        result_journals = {}
        # NORMAL PAYMENTS
        if total_account_payment != 0:
            line += 1
            worksheet.write(line, 3, _('COBROS'), xls_cell_format_header)
            worksheet.write(line, 4, _('UDS'), xls_cell_format_header)
            worksheet.write(line, 5, total_account_payment,
                            xls_cell_format_header)
        for journal in payment_journals:
            line += 1
            worksheet.write(line, 3, _(journal))
            worksheet.write(line, 4, count_payment_journals[journal],
                            xls_cell_format_money)
            worksheet.write(line, 5, payment_journals[journal],
                            xls_cell_format_money)
            if journal not in result_journals:
                result_journals.update({journal: payment_journals[journal]})
            else:
                result_journals[journal] += payment_journals[journal]

        # RETURNS
        if total_payment_returns_amount != 0:
            line += 1
            worksheet.write(line, 3, _('DEVOLUCIONES'), xls_cell_format_header)
            worksheet.write(line, 4, _('UDS'), xls_cell_format_header)
            worksheet.write(line, 5, total_payment_returns_amount,
                            xls_cell_format_header)
        for journal in return_journals:
            line += 1
            worksheet.write(line, 3, _(journal))
            worksheet.write(line, 4, count_return_journals[journal],
                            xls_cell_format_money)
            worksheet.write(line, 5, return_journals[journal],
                            xls_cell_format_money)
            if journal not in result_journals:
                result_journals.update({journal: return_journals[journal]})
            else:
                result_journals[journal] += return_journals[journal]

        # EXPENSES
        if total_account_expenses != 0:
            line += 1
            worksheet.write(line, 3, _('GASTOS'), xls_cell_format_header)
            worksheet.write(line, 4, _('UDS'), xls_cell_format_header)
            worksheet.write(line, 5, -total_account_expenses,
                            xls_cell_format_header)
        for journal in expense_journals:
            line += 1
            worksheet.write(line, 3, _(journal))
            worksheet.write(line, 4, count_expense_journals[journal],
                            xls_cell_format_money)
            worksheet.write(line, 5, -expense_journals[journal],
                            xls_cell_format_money)
            if journal not in result_journals:
                result_journals.update({journal: expense_journals[journal]})
            else:
                result_journals[journal] += expense_journals[journal]

        #TOTALS
        line += 1
        worksheet.write(line, 3, _('TOTAL'), xls_cell_format_header)
        worksheet.write(
            line,
            5,
            total_account_payment + total_payment_returns_amount - total_account_expenses,
            xls_cell_format_header)
        for journal in result_journals:
            line += 1
            worksheet.write(line, 3, _(journal))
            worksheet.write(line, 5, result_journals[journal],
                            xls_cell_format_money)

        line += 1
        worksheet.write(line, 1, _('FECHA:'))
        line += 1
        worksheet.write(line, 1, _('NOMBRE Y FIRMA TURNO SALIENTE:'))
        worksheet.write(line, 3, _('NOMBRE Y FIRMA TURNO ENTRANTE:'))
        worksheet.set_landscape()
        if not user.has_group('hotel.group_hotel_manager'):
            worksheet.protect()
        worksheet_day = workbook.add_worksheet(_('Por dia'))
        worksheet_day.write('A2', _('Date'), xls_cell_format_header)
        worksheet_day.write('B2', _('Validar'), xls_cell_format_header)
        columns_balance = {4: 'E:E', 7: 'H:H', 10: 'K:K', 13: 'N:N', 16: 'Q:Q', 19: 'T:T'}
        i = 1
        column_journal = {}
        for journal in result_journals:
            ingresos = 'Ingresos ' + journal
            gastos = 'Gastos ' + journal
            i += 1
            worksheet_day.write(0, i+2, _(journal), xls_cell_format_header)
            worksheet_day.write(1, i, _('Ingresos'), xls_cell_format_header)
            column_journal.update({ingresos: i})
            i += 1
            worksheet_day.write(1, i, _('Gastos'), xls_cell_format_header)
            column_journal.update({gastos: i})
            i += 1
            worksheet_day.write(1, i, _('Resultado'))
            column_journal.update({journal: i})
            if columns_balance.get(i):
                worksheet_day.set_column(columns_balance.get(i), 8, cell_format)

        worksheet_day.set_column('A:A', 11)

        offset = 2
        total_dates = sorted(total_dates.items(), key=lambda x: x[0])
        for k_day, v_day in enumerate(total_dates):
            worksheet_day.write(k_day+offset, 0, v_day[0])
            for journal in v_day[1]:
                worksheet_day.write(k_day+offset, column_journal[journal], v_day[1][journal])
        worksheet_day.set_landscape()
        if not user.has_group('hotel.group_hotel_manager'):
            worksheet_day.protect()
        workbook.close()
        file_data.seek(0)
        tnow = fields.Datetime.now().replace(' ', '_')
        return {
            'xls_filename': 'cash_daily_report_%s.xlsx' % tnow,
            'xls_binary': base64.encodestring(file_data.read()),
        }

    @api.multi
    def export(self):
        self.write(self._export())
        return {
            "type": "ir.actions.do_nothing",
        }
