# -*- coding: utf-8 -*-
##############################################################################
#
#    oerpfs module for OpenERP, Automatic mounts with fuse on the filesystem for simple operations (files access, data import, etc.)
#    Copyright (C) 2014 SYLEAM Info Services (<http://www.Syleam.fr/>)
#              Sylvain Garancher <sylvain.garancher@syleam.fr>
#
#    This file is a part of oerpfs
#
#    oerpfs is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    oerpfs is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm
from openerp.osv import fields


class OerpFsDirectory(orm.Model):
    _name = 'oerpfs.directory'
    _description = 'OerpFS Directory'

    _columns = {
        'name': fields.char('Name', size=64, required=True, help='Directory name'),
        'path': fields.char('Path', size=256, required=True, help='Path of this directory'),
        'type': fields.selection([('attachment', 'Attachment'), ('csv_import', 'CSV Import')], 'Type', required=True, help='Type of mount'),
    }

    _defaults = {
        'path': '/srv/openerp/fs/',
        'type': 'attachment',
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
