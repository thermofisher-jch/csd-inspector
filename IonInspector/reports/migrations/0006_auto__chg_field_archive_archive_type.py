# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Archive.archive_type'
        db.alter_column(u'reports_archive', 'archive_type', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Archive.archive_type'
        raise RuntimeError("Cannot reverse this migration. 'Archive.archive_type' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'Archive.archive_type'
        db.alter_column(u'reports_archive', 'archive_type', self.gf('django.db.models.fields.CharField')(max_length=255))

    models = {
        u'reports.archive': {
            'Meta': {'object_name': 'Archive'},
            'archive_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
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