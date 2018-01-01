# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services PVT. LTD.
#    (<http://www.serpentcs.com>)
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
# ---------------------------------------------------------------------------
import json
from datetime import datetime, timedelta

from babel.dates import format_datetime, format_date

from odoo import models, api, _, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools.misc import formatLang

class HotelDashboard(models.Model):
    _name = "hotel.dashboard"

    def _get_count(self):
        resevations_count = self.env['hotel.reservation'].search(
            [('sate', '=', 'confirm')])
        folios_count = self.env['hotel.folio'].search(
            [('sate', '=', 'sales_order')])
        next_arrivals_count = self.env['sale.order'].search(
            [('is_checkin', '=', True)])

        self.orders_count = len(orders_count)
        self.quotations_count = len(quotations_count)
        self.orders_done_count = len(orders_done_count)
    @api.one
    def _kanban_dashboard(self):
        if self.graph_type == 'bar':
            self.kanban_dashboard_graph = json.dumps(self.get_bar_graph_datas())
        elif self.graph_type == 'line':
            self.kanban_dashboard_graph = json.dumps(self.get_line_graph_datas())
        
    @api.one
    def _kanban_dashboard_graph(self):
        self.kanban_dashboard_graph = json.dumps(self.get_bar_graph_datas())
        #~ if (self.type in ['sale', 'purchase']):
            #~ self.kanban_dashboard_graph = json.dumps(self.get_bar_graph_datas())
        #~ elif (self.type in ['cash', 'bank']):
            #~ self.kanban_dashboard_graph = json.dumps(self.get_line_graph_datas())

    color = fields.Integer(string='Color Index')
    name = fields.Char(string="Name")
    type = fields.Char(default="sale")
    graph_type = fields.Selection([('line','Line'),('bar','Bar'),('none','None')])
    reservations_count = fields.Integer(compute = '_get_count')
    folios_count = fields.Integer(compute= '_get_count')
    next_arrivals_count = fields.Integer(compute= '_get_count')
    kanban_dashboard = fields.Text(compute='_kanban_dashboard')
    kanban_dashboard_graph = fields.Text(compute='_kanban_dashboard_graph')
    show_on_dashboard = fields.Boolean(string='Show journal on dashboard', help="Whether this journal should be displayed on the dashboard or not", default=True)
    
    @api.multi
    def get_bar_graph_datas(self):
        #~ data = []
        #~ today = datetime.strptime(fields.Date.context_today(self), DF)
        #~ data.append({'label': _('Past'), 'value':0.0, 'type': 'past'})
        #~ day_of_week = int(format_datetime(today, 'e', locale=self._context.get('lang') or 'en_US'))
        #~ first_day_of_week = today + timedelta(days=-day_of_week+1)
        #~ for i in range(-1,4):
            #~ if i==0:
                #~ label = _('This Week')
            #~ elif i==3:
                #~ label = _('Future')
            #~ else:
                #~ start_week = first_day_of_week + timedelta(days=i*7)
                #~ end_week = start_week + timedelta(days=6)
                #~ if start_week.month == end_week.month:
                    #~ label = str(start_week.day) + '-' +str(end_week.day)+ ' ' + format_date(end_week, 'MMM', locale=self._context.get('lang') or 'en_US')
                #~ else:
                    #~ label = format_date(start_week, 'd MMM', locale=self._context.get('lang') or 'en_US')+'-'+format_date(end_week, 'd MMM', locale=self._context.get('lang') or 'en_US')
            #~ data.append({'label':label,'value':0.0, 'type': 'past' if i<0 else 'future'})

        #~ # Build SQL query to find amount aggregated by week
        #~ select_sql_clause = """SELECT sum(residual_company_signed) as total, min(date) as aggr_date from account_invoice where journal_id = %(journal_id)s and state = 'open'"""
        #~ query = ''
        #~ start_date = (first_day_of_week + timedelta(days=-7))
        #~ for i in range(0,6):
            #~ if i == 0:
                #~ query += "("+select_sql_clause+" and date < '"+start_date.strftime(DF)+"')"
            #~ elif i == 5:
                #~ query += " UNION ALL ("+select_sql_clause+" and date >= '"+start_date.strftime(DF)+"')"
            #~ else:
                #~ next_date = start_date + timedelta(days=7)
                #~ query += " UNION ALL ("+select_sql_clause+" and date >= '"+start_date.strftime(DF)+"' and date < '"+next_date.strftime(DF)+"')"
                #~ start_date = next_dates

        #~ self.env.cr.execute(query, {'journal_id':self.id})
        #~ query_results = self.env.cr.dictfetchall()
        #~ for index in range(0, len(query_results)):
            #~ if query_results[index].get('aggr_date') != None:
                #~ data[index]['value'] = query_results[index].get('total')

        data = ({'label': 'Anteayer', 'value':0.0, 'type': 'past'},
                {'label': 'Ayer', 'value':9.0, 'type': 'past'},
                {'label': 'Hoy', 'value':2.0, 'type': 'future'},
                {'label': 'Mañana', 'value':7.0, 'type': 'future'},
                {'label': 'Pasado', 'value':4.0, 'type': 'future'},
                {'label': 'Sabado', 'value':18.0, 'type': 'future'},
                {'label': 'Domingo', 'value':12.0, 'type': 'future'})
        return [{'values': data}]

    @api.multi
    def get_journal_dashboard_datas(self):
        #~ currency = self.currency_id or self.company_id.currency_id
        #~ number_to_reconcile = last_balance = account_sum = 0
        #~ ac_bnk_stmt = []
        #~ title = ''
        #~ number_draft = number_waiting = number_late = 0
        #~ sum_draft = sum_waiting = sum_late = 0.0
        #~ if self.type in ['bank', 'cash']:
            #~ last_bank_stmt = self.env['account.bank.statement'].search([('journal_id', 'in', self.ids)], order="date desc, id desc", limit=1)
            #~ last_balance = last_bank_stmt and last_bank_stmt[0].balance_end or 0
            #~ #Get the number of items to reconcile for that bank journal
            #~ self.env.cr.execute("""SELECT COUNT(DISTINCT(statement_line_id)) 
                        #~ FROM account_move where statement_line_id 
                        #~ IN (SELECT line.id 
                            #~ FROM account_bank_statement_line AS line 
                            #~ LEFT JOIN account_bank_statement AS st 
                            #~ ON line.statement_id = st.id 
                            #~ WHERE st.journal_id IN %s and st.state = 'open')""", (tuple(self.ids),))
            #~ already_reconciled = self.env.cr.fetchone()[0]
            #~ self.env.cr.execute("""SELECT COUNT(line.id) 
                            #~ FROM account_bank_statement_line AS line 
                            #~ LEFT JOIN account_bank_statement AS st 
                            #~ ON line.statement_id = st.id 
                            #~ WHERE st.journal_id IN %s and st.state = 'open'""", (tuple(self.ids),))
            #~ all_lines = self.env.cr.fetchone()[0]
            #~ number_to_reconcile = all_lines - already_reconciled
            #~ # optimization to read sum of balance from account_move_line
            #~ account_ids = tuple(filter(None, [self.default_debit_account_id.id, self.default_credit_account_id.id]))
            #~ if account_ids:
                #~ amount_field = 'balance' if (not self.currency_id or self.currency_id == self.company_id.currency_id) else 'amount_currency'
                #~ query = """SELECT sum(%s) FROM account_move_line WHERE account_id in %%s AND date <= %%s;""" % (amount_field,)
                #~ self.env.cr.execute(query, (account_ids, fields.Date.today(),))
                #~ query_results = self.env.cr.dictfetchall()
                #~ if query_results and query_results[0].get('sum') != None:
                    #~ account_sum = query_results[0].get('sum')
        #~ #TODO need to check if all invoices are in the same currency than the journal!!!!
        #~ elif self.type in ['sale', 'purchase']:
            #~ title = _('Bills to pay') if self.type == 'purchase' else _('Invoices owed to you')
            #~ # optimization to find total and sum of invoice that are in draft, open state
            #~ query = """SELECT state, amount_total, currency_id AS currency, type FROM account_invoice WHERE journal_id = %s AND state NOT IN ('paid', 'cancel');"""
            #~ self.env.cr.execute(query, (self.id,))
            #~ query_results = self.env.cr.dictfetchall()
            #~ today = datetime.today()
            #~ query = """SELECT amount_total, currency_id AS currency, type FROM account_invoice WHERE journal_id = %s AND date < %s AND state = 'open';"""
            #~ self.env.cr.execute(query, (self.id, today))
            #~ late_query_results = self.env.cr.dictfetchall()
            #~ for result in query_results:
                #~ if result['type'] in ['in_refund', 'out_refund']:
                    #~ factor = -1
                #~ else:
                    #~ factor = 1
                #~ cur = self.env['res.currency'].browse(result.get('currency'))
                #~ if result.get('state') in ['draft', 'proforma', 'proforma2']:
                    #~ number_draft += 1
                    #~ sum_draft += cur.compute(result.get('amount_total'), currency) * factor
                #~ elif result.get('state') == 'open':
                    #~ number_waiting += 1
                    #~ sum_waiting += cur.compute(result.get('amount_total'), currency) * factor
            #~ for result in late_query_results:
                #~ if result['type'] in ['in_refund', 'out_refund']:
                    #~ factor = -1
                #~ else:
                    #~ factor = 1
                #~ cur = self.env['res.currency'].browse(result.get('currency'))
                #~ number_late += 1
                #~ sum_late += cur.compute(result.get('amount_total'), currency) * factor

        #~ difference = currency.round(last_balance-account_sum) + 0.0
        return {
            'graph': self.graph_type,
            'number_to_reconcile': 11,
            'account_balance': 4314,
            'last_balance': 252,
            'difference': 432,
            'number_draft': 32,
            'number_waiting': 44,
            'number_late': 23,
            'sum_draft': 2424245,
            'sum_waiting': 3124312,
            'sum_late': 23123,
            'currency_id': 1,
            'bank_statements_source': 'fonte',
            'title': 'titulo', 
        }
        
    @api.multi
    def get_line_graph_datas(self):
        #~ data = []
        #~ today = datetime.today()
        #~ last_month = today + timedelta(days=-30)
        #~ bank_stmt = []
        #~ # Query to optimize loading of data for bank statement graphs
        #~ # Return a list containing the latest bank statement balance per day for the
        #~ # last 30 days for current journal
        #~ query = """SELECT a.date, a.balance_end 
                        #~ FROM account_bank_statement AS a, 
                            #~ (SELECT c.date, max(c.id) AS stmt_id 
                                #~ FROM account_bank_statement AS c 
                                #~ WHERE c.journal_id = %s 
                                    #~ AND c.date > %s 
                                    #~ AND c.date <= %s 
                                    #~ GROUP BY date, id 
                                    #~ ORDER BY date, id) AS b 
                        #~ WHERE a.id = b.stmt_id;"""

        #~ self.env.cr.execute(query, (self.id, last_month, today))
        #~ bank_stmt = self.env.cr.dictfetchall()

        #~ last_bank_stmt = self.env['account.bank.statement'].search([('journal_id', 'in', self.ids),('date', '<=', last_month.strftime(DF))], order="date desc, id desc", limit=1)
        #~ start_balance = last_bank_stmt and last_bank_stmt[0].balance_end or 0

        #~ locale = self._context.get('lang') or 'en_US'
        #~ show_date = last_month
        #~ #get date in locale format
        #~ name = format_date(show_date, 'd LLLL Y', locale=locale)
        #~ short_name = format_date(show_date, 'd MMM', locale=locale)
        #~ data.append({'x':short_name,'y':start_balance, 'name':name})

        #~ for stmt in bank_stmt:
            #~ #fill the gap between last data and the new one
            #~ number_day_to_add = (datetime.strptime(stmt.get('date'), DF) - show_date).days
            #~ last_balance = data[len(data) - 1]['y']
            #~ for day in range(0,number_day_to_add + 1):
                #~ show_date = show_date + timedelta(days=1)
                #~ #get date in locale format
                #~ name = format_date(show_date, 'd LLLL Y', locale=locale)
                #~ short_name = format_date(show_date, 'd MMM', locale=locale)
                #~ data.append({'x': short_name, 'y':last_balance, 'name': name})
            #~ #add new stmt value
            #~ data[len(data) - 1]['y'] = stmt.get('balance_end')

        #~ #continue the graph if the last statement isn't today
        #~ if show_date != today:
            #~ number_day_to_add = (today - show_date).days
            #~ last_balance = data[len(data) - 1]['y']
            #~ for day in range(0,number_day_to_add):
                #~ show_date = show_date + timedelta(days=1)
                #~ #get date in locale format
                #~ name = format_date(show_date, 'd LLLL Y', locale=locale)
                #~ short_name = format_date(show_date, 'd MMM', locale=locale)
                #~ data.append({'x': short_name, 'y':last_balance, 'name': name})
        data = ({'name': '27 December 2017', 'x':'27', 'y': 8},
                {'name': '28 December 2017', 'x':'28', 'y': 4},
                {'name': '29 December 2017', 'x':'29', 'y': 6},
                {'name': '30 December 2017', 'x':'30', 'y': 12},
                {'name': '31 December 2017', 'x':'31', 'y': 20},
                {'name': '1 January 2017', 'x':'1', 'y': 35},
                {'name': '2 January 2017', 'x':'2', 'y': 20},
                {'name': '3 January 2017', 'x':'3', 'y': 44},
                {'name': '4 January 2017', 'x':'4', 'y': 13},
                {'name': '5 January 2017', 'x':'5', 'y': 43},
                {'name': '6 January 2017', 'x':'6', 'y': 34},
                {'name': '7 January 2017', 'x':'7', 'y': 13},
                {'name': '8 January 2017', 'x':'8', 'y': 24},
                {'name': '9 January 2017', 'x':'9', 'y': 9},
                {'name': '10 January 2017', 'x':'10', 'y': 34},
                {'name': '11 January 2017', 'x':'11', 'y': 20},
                {'name': '12 January 2017', 'x':'12', 'y': 44},
                {'name': '13 January 2017', 'x':'13', 'y': 4},
                {'name': '14 January 2017', 'x':'14', 'y': 12},
                {'name': '15 January 2017', 'x':'15', 'y': 4},
                {'name': '16 January 2017', 'x':'16', 'y': 4},
                {'name': '17 January 2017', 'x':'17', 'y': 10},
                {'name': '18 January 2017', 'x':'18', 'y': 13},
                {'name': '19 January 2017', 'x':'19', 'y': 16},
                {'name': '20 January 2017', 'x':'20', 'y': 14},
                {'name': '21 January 2017', 'x':'21', 'y': 5},
                {'name': '22 January 2017', 'x':'22', 'y': 16},
                {'name': '23 January 2017', 'x':'23', 'y': 14},
                {'name': '24 January 2017', 'x':'24', 'y': 13},
                {'name': '25 January 2017', 'x':'25', 'y': 13},
                {'name': '26 January 2017', 'x':'26', 'y': 34},
                {'name': '27 January 2017', 'x':'27', 'y': 30})
        return [{'values': data, 'area': True}]
        
    @api.multi
    def action_create_new(self):
        #~ ctx = self._context.copy()
        #~ model = 'account.invoice'
        #~ if self.type == 'sale':
            #~ ctx.update({'journal_type': self.type, 'default_type': 'out_invoice', 'type': 'out_invoice', 'default_journal_id': self.id})
            #~ if ctx.get('refund'):
                #~ ctx.update({'default_type':'out_refund', 'type':'out_refund'})
            #~ view_id = self.env.ref('account.invoice_form').id
        #~ elif self.type == 'purchase':
            #~ ctx.update({'journal_type': self.type, 'default_type': 'in_invoice', 'type': 'in_invoice', 'default_journal_id': self.id})
            #~ if ctx.get('refund'):
                #~ ctx.update({'default_type': 'in_refund', 'type': 'in_refund'})
            #~ view_id = self.env.ref('account.invoice_supplier_form').id
        #~ else:
            #~ ctx.update({'default_journal_id': self.id})
            #~ view_id = self.env.ref('account.view_move_form').id
            #~ model = 'account.move'
        model = "hotel.folio"
        view_id = self.env.ref('hotel.view_hotel_folio1_form').id
        ctx=''
        return {
            'name': _('Create invoice/bill'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': model,
            'view_id': view_id,
            'context': ctx,
        }
    
    @api.multi
    def open_action(self):
        """return action based on type for related journals"""
        #~ action_name = self._context.get('action_name', False)
        #~ if not action_name:
            #~ if self.type == 'bank':
                #~ action_name = 'action_bank_statement_tree'
            #~ elif self.type == 'cash':
                #~ action_name = 'action_view_bank_statement_tree'
            #~ elif self.type == 'sale':
                #~ action_name = 'action_invoice_tree1'
            #~ elif self.type == 'purchase':
                #~ action_name = 'action_invoice_tree2'
            #~ else:
                #~ action_name = 'action_move_journal_line'

        #~ _journal_invoice_type_map = {
            #~ ('sale', None): 'out_invoice',
            #~ ('purchase', None): 'in_invoice',
            #~ ('sale', 'refund'): 'out_refund',
            #~ ('purchase', 'refund'): 'in_refund',
            #~ ('bank', None): 'bank',
            #~ ('cash', None): 'cash',
            #~ ('general', None): 'general',
        #~ }
        #~ invoice_type = _journal_invoice_type_map[(self.type, self._context.get('invoice_type'))]

        #~ ctx = self._context.copy()
        #~ ctx.pop('group_by', None)
        #~ ctx.update({
            #~ 'journal_type': self.type,
            #~ 'default_journal_id': self.id,
            #~ 'search_default_journal_id': self.id,
            #~ 'default_type': invoice_type,
            #~ 'type': invoice_type
        #~ })

        #~ [action] = self.env.ref('account.%s' % action_name).read()
        #~ action['context'] = ctx
        #~ action['domain'] = self._context.get('use_domain', [])
        #~ if action_name in ['action_bank_statement_tree', 'action_view_bank_statement_tree']:
            #~ action['views'] = False
            #~ action['view_id'] = False
        return False
