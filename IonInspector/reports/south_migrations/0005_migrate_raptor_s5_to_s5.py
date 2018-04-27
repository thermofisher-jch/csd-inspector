# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models


class Migration(DataMigration):

    def forwards(self, orm):
        """Write your forwards methods here."""
        # Note: Don't use "from appname.models import ModelName". 
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.
        for archive in orm['reports.Archive'].objects.all():
            if 'RAPTOR_S5' == archive.archive_type.upper():
                archive.archive_type = 'S5'
                archive.save()

    def backwards(self, orm):
        """Write your backwards methods here."""
        for archive in orm['reports.Archive'].objects.all():
            if archive.archive_type == 'S5':
                archive.archive_type = 'Raptor_S5'
                archive.save()

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
    symmetrical = True
