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

import multiprocessing
from openerp.osv import orm
from openerp.osv import fields
from openerp.addons.oerpfs.oerpfs import OerpFSModel, OerpFSCsvImport


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
        for wizard in self.browse(cr, uid, ids, context=context):
            fuseClass = None
            if wizard.directory_id.type == 'attachment':
                fuseClass = OerpFSModel
            elif wizard.directory_id.type == 'csv_import':
                fuseClass = OerpFSCsvImport

            # Mount options
            mount_options = [
                '-o', 'fsname=oerpfs',
                '-o', 'subtype=openerp.' + str(wizard.directory_id.name),
            ]

            # Mount the directory using fuse
            mount_point = fuseClass(wizard.user_id.id, cr.dbname)
            mount_point.fuse_args.mountpoint = str(wizard.directory_id.path)
            mount_point.multithreaded = True
            mount_point.parse(mount_options)
            mount_process = multiprocessing.Process(target=mount_point.main)
            mount_process.start()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
