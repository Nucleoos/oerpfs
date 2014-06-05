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

import csv
import stat
import fuse
import base64
from errno import ENOENT
from StringIO import StringIO
from openerp import pooler
from openerp.osv import orm
from openerp.osv import fields

fuse.fuse_python_api = (0, 2)


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

class OerpFSModel(fuse.Fuse):
    """
    Fuse filesystem for simple OpenERP filestore access
    """
    def __init__(self, uid, dbname, *args, **kwargs):
        super(OerpFSModel, self).__init__(*args, **kwargs)

        # Initialize OpenERP specific variables
        self.uid = uid
        self.dbname = dbname

    def getattr(self, path):
        """
        Return attributes for the specified path :
            - Search for the model as first part
            - Search for an existing record as second part
            - Search for an existing attachment as third part
            - There cannot be more than 3 parts in the path
        """
        db, pool = pooler.get_db_and_pool(self.dbname)
        cr = db.cursor()
        fakeStat = fuse.Stat()
        fakeStat.st_mode = stat.S_IFDIR | 0400
        fakeStat.st_nlink = 0

        if path == '/':
            cr.close()
            return fakeStat

        paths = path.split('/')[1:]
        if len(paths) > 3:
            cr.close()
            return -ENOENT

        # Check for model existence
        model_obj = pool.get('ir.model')
        model_ids = model_obj.search(cr, self.uid, [('model', '=', paths[0])])
        if not model_ids:
            cr.close()
            return -ENOENT
        elif len(paths) == 1:
            cr.close()
            return fakeStat

        # Check for record existence
        element_obj = pool.get(paths[0])
        element_ids = element_obj.search(cr, self.uid, [('id', '=', int(paths[1]))])
        if not element_ids:
            cr.close()
            return -ENOENT
        elif len(paths) == 2:
            cr.close()
            return fakeStat

        # Chech for attachement existence
        attachment_obj = pool.get('ir.attachment')
        attachment_ids = attachment_obj.search(cr, self.uid, [('res_model', '=', paths[0]), ('res_id', '=', int(paths[1])), ('id', '=', self.id_from_label(paths[2]))])
        if not attachment_ids:
            cr.close()
            return -ENOENT

        # Common stats
        fakeStat.st_mode = stat.S_IFREG | 0400
        fakeStat.st_nlink = 2

        # Read the file
        attachment_obj = pool.get('ir.attachment')
        attachment_ids = attachment_obj.search(cr, self.uid, [('res_model', '=', paths[0]), ('res_id', '=', int(paths[1])), ('id', '=', self.id_from_label(paths[2]))])
        attachment_data = attachment_obj.read(cr, self.uid, attachment_ids, ['datas'])
        fakeStat.st_size = len(base64.b64decode(attachment_data[0]['datas']))
        cr.close()
        return fakeStat

    def readdir(self, path, offset):
        """
        Return content of a directory :
            - List models for root path
            - List records for a model
            - List attachments for a record
        We don't have to check for the path, because getattr already returns -ENOENT if the model/record/attachment doesn't exist
        """
        db, pool = pooler.get_db_and_pool(self.dbname)
        cr = db.cursor()
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')

        paths = path.split('/')[1:]
        # List models
        if path == '/':
            model_obj = pool.get('ir.model')
            model_ids = model_obj.search(cr, self.uid, [])
            for model_data in model_obj.read(cr, self.uid, model_ids, ['model']):
                yield fuse.Direntry(str(model_data['model']))
        # List records
        elif len(paths) == 1:
            element_obj = pool.get(paths[0])
            element_ids = element_obj.search(cr, self.uid, [])
            for element_data in element_obj.read(cr, self.uid, element_ids, ['id']):
                yield fuse.Direntry(str(element_data['id']))
        # List attachments
        else:
            attachment_obj = pool.get('ir.attachment')
            attachment_ids = attachment_obj.search(cr, self.uid, [('res_model', '=', paths[0]), ('res_id', '=', int(paths[1]))])
            for attachment_data in attachment_obj.read(cr, self.uid, attachment_ids, ['name']):
                yield fuse.Direntry(str('%d-%s' % (attachment_data['id'], attachment_data['name'])))

        cr.close()

    def read(self, path, size, offset):
        """
        Return the specified slide of a file
        Note : Only the beginning of the name is required (the ID of the attachment), we can put anything after the first '-', it will be ignored
        """
        db, pool = pooler.get_db_and_pool(self.dbname)
        cr = db.cursor()
        paths = path.split('/')[1:]
        # Read files by slides
        attachment_obj = pool.get('ir.attachment')
        attachment_ids = attachment_obj.search(cr, self.uid, [('res_model', '=', paths[0]), ('res_id', '=', int(paths[1])), ('id', '=', self.id_from_label(paths[2]))])
        attachment_data = attachment_obj.read(cr, self.uid, attachment_ids, ['datas'])
        cr.close()
        return base64.b64decode(attachment_data[0]['datas'])[offset:offset + size]

    def id_from_label(self, label):
        """
        Return the attachment ID from a file name : only the part before the first '-'
        """
        return int(label.split('-')[0])


class OerpFSCsvImport(fuse.Fuse):
    """
    Automatic CSV import to OpenERP on file copy
    """
    def __init__(self, uid, dbname, *args, **kwargs):
        super(OerpFSCsvImport, self).__init__(*args, **kwargs)

        # Dict used to store files contents
        self.files = {}

        # Initialize OpenERP specific variables
        self.uid = uid
        self.dbname = dbname

    def getattr(self, path):
        """
        Only the root path exists, where we copy the CSV files to be imported
        """
        fakeStat = fuse.Stat()
        fakeStat.st_mode = stat.S_IFDIR | 0200
        fakeStat.st_nlink = 0

        if path == '/':
            return fakeStat

        if path in self.files:
            fakeStat.st_mode = stat.S_IFREG | 0200
            fakeStat.st_nlink = 1
            return fakeStat

        return -ENOENT

    def readdir(self, path, offset):
        """
        As only the root path exists, we only have to return the default entries
        """
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')

        for path in self.files:
            yield(fuse.Direntry(path))

    def open(self, path, flags):
        return 0

    def create(self, path, mode, fi=None):
        self.files[path] = StringIO()
        return 0

    def write(self, path, buf, offset):
        """
        Write the contents of a CSV file : store it in a variable
        """
        if not path in self.files:
            return -ENOENT
        self.files[path].write(buf)
        return len(buf)

    def flush(self, path):
        return 0

    def truncate(self, path, length):
        return 0

    def chmod(self, path):
        return 0

    def chown(self, path):
        return 0

    def utime(self, path, times=None):
        return 0

    def release(self, path, fh):
        """
        Writing of the file is finished, import the contents into OpenERP
        """
        db, pool = pooler.get_db_and_pool(self.dbname)
        cr = db.cursor()
        # FIXME : Don't know why it doesn't work without rebuilding the StringIO object...
        value = StringIO(self.files[path].getvalue())

        # Parse the CSV file contents
        csvFile = csv.reader(value)
        lines = list(csvFile)

        # Import data into OpenERP
        model = path.replace('.csv', '')[1:]
        oerpObject = pool.get(model)
        oerpObject.import_data(cr, self.uid, lines[0], lines[1:], 'init', '', False, {'import': True})

        # Close StringIO and free memory
        self.files[path].close()
        del self.files[path]
        value.close()
        del value
        cr.commit()
        cr.close()
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
