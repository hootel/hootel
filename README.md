# ALDA PROJECT MODULES [![Build Status](https://travis-ci.org/eiqui-dev/alda.svg?branch=10.0)](https://travis-ci.org/eiqui-dev/alda) [![codecov](https://codecov.io/gh/eiqui-dev/alda/branch/10.0/graph/badge.svg)](https://codecov.io/gh/eiqui-dev/alda)


UNDER DEVELOPMENT: **NOT USE IN PRODUCTION**


**IMPORTANT:**
  - Set time zone of users that use the calendar

**MODULES:**
  - [x] hotel: Base module (a fork of SerpentCS Hotel Module)
  - [x] hotel_calendar: Adds calendar for manage hotel reservations and rooms configuration
  - [x] hotel_calendar_wubook: Unify 'hotel_wubook_prototype' and 'hotel_calendar' modules
  - [x] hotel_l10n_es: Procedures for check-in process in Spain
  - [ ] hotel_wubook: NOTHING... the idea is use Odoo Connector
  - [x] hotel_wubook_prototype: Current implementation of Wubook Connector... sync data with wubook.net account.
  - [ ] hotel_node_slave: Configure a node as a slave to serve and get information from a master one
  - [ ] hotel_node_master: Configure a node as a master
  - [ ] glasof_exporter: Export Odoo data to Glasof xls format
  - [x] hotel_revenue: Export Odoo data for Revenue in xls format

**HOW WORKS?**
  - The idea is... the hotel sell 'virtual rooms' and the customer is assigned to one 'normal room'.
  - The folio have all reservation lines, used services...
