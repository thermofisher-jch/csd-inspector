# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Archive'
        db.create_table(u'reports_archive', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identifier', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('site', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
            ('submitter_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('archive_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('summary', self.gf('django.db.models.fields.CharField')(default=u'', max_length=255)),
            ('doc_file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal(u'reports', ['Archive'])

        # Adding model 'Diagnostic'
        db.create_table(u'reports_diagnostic', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='', max_length=255)),
            ('status', self.gf('django.db.models.fields.CharField')(default='Unexecuted', max_length=255)),
            ('details', self.gf('django.db.models.fields.CharField')(default='', max_length=2048)),
            ('error', self.gf('django.db.models.fields.CharField')(default='', max_length=2048)),
            ('html', self.gf('django.db.models.fields.CharField')(default='', max_length=255)),
            ('priority', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('start_execute', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('archive', self.gf('django.db.models.fields.related.ForeignKey')(related_name='diagnostics', to=orm['reports.Archive'])),
        ))
        db.send_create_signal(u'reports', ['Diagnostic'])

        # Adding model 'Tag'
        db.create_table(u'reports_tag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('archive', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tags', to=orm['reports.Archive'])),
        ))
        db.send_create_signal(u'reports', ['Tag'])


    def backwards(self, orm):
        # Deleting model 'Archive'
        db.delete_table(u'reports_archive')

        # Deleting model 'Diagnostic'
        db.delete_table(u'reports_diagnostic')

        # Deleting model 'Tag'
        db.delete_table(u'reports_tag')


    models = {
        u'reports.archive': {
            'Meta': {'object_name': 'Archive'},
            'archive_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'doc_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'site': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'submitter_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'summary': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'reports.diagnostic': {
            'Meta': {'object_name': 'Diagnostic'},
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