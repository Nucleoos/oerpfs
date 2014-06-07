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


class OerpfsMount(orm.TransientModel):
    _name = 'wizard.oerpfs.mount'
    _description = 'Mount OerpFS'

    _columns = {
        'directory_id': fields.many2one('oerpfs.directory', 'Directory', required=True, help='Directory where the FS will be mounted'),
        'user_id': fields.many2one('res.users', 'User', required=True, help='User which mounts the filesystem'),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context=None: uid,
    }

    def mount(self, cr, uid, ids, context=None):
        """
        Mount a directory for the choosen user
        """
        directory_obj = self.pool.get('oerpfs.directory')
        for wizard in self.browse(cr, uid, ids, context=context):
            directory_obj.mount(cr, wizard.user_id.id, [wizard.directory_id.id], context=context)

        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
