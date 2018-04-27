# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'Archive', fields ['site']
        db.create_index(u'reports_archive', ['site'])

        # Adding index on 'Archive', fields ['submitter_name']
        db.create_index(u'reports_archive', ['submitter_name'])


    def backwards(self, orm):
        # Removing index on 'Archive', fields ['submitter_name']
        db.delete_index(u'reports_archive', ['submitter_name'])

        # Removing index on 'Archive', fields ['site']
        db.delete_index(u'reports_archive', ['site'])


    models = {
        u'reports.archive': {
            'Meta': {'object_name': 'Archive'},
            'archive_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'doc_file': ('django.db.models.fields.files.FileField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'site': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'submitter_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'summary': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255'}),
            'taser_ticket_number': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'reports.diagnostic': {
            'Meta': {'ordering': "['name']", 'object_name': 'Diagnostic'},
            'archive': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'diagnostics'", 'to': u"orm['reports.Archive']"}),
            'details': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '2048'}),
            'error': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '2048'}),
            'html': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'start_execute': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'Unexecuted'", 'max_length': '255'})
        },
        u'reports.tag': {
            'Meta': {'object_name': 'Tag'},
            'archive': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tags'", 'to': u"orm['reports.Archive']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['reports']