# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Archive'
        db.create_table(u'IonInspector_archive', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('site', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('submitter_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('archive_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('summary', self.gf('django.db.models.fields.CharField')(default=u'', max_length=255)),
        ))
        db.send_create_signal(u'IonInspector', ['Archive'])

        # Adding model 'Diagnostic'
        db.create_table(u'IonInspector_diagnostic', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('priority', self.gf('django.db.models.fields.IntegerField')()),
            ('details', self.gf('django.db.models.fields.CharField')(max_length=2048)),
            ('html', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('archive', self.gf('django.db.models.fields.related.ForeignKey')(related_name='diagnostics', to=orm['IonInspector.Archive'])),
        ))
        db.send_create_signal(u'IonInspector', ['Diagnostic'])

        # Adding model 'Tag'
        db.create_table(u'IonInspector_tag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('archive', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tags', to=orm['IonInspector.Archive'])),
        ))
        db.send_create_signal(u'IonInspector', ['Tag'])


    def backwards(self, orm):
        # Deleting model 'Archive'
        db.delete_table(u'IonInspector_archive')

        # Deleting model 'Diagnostic'
        db.delete_table(u'IonInspector_diagnostic')

        # Deleting model 'Tag'
        db.delete_table(u'IonInspector_tag')


    models = {
        u'IonInspector.archive': {
            'Meta': {'object_name': 'Archive'},
            'archive_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'site': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'submitter_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'summary': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'IonInspector.diagnostic': {
            'Meta': {'object_name': 'Diagnostic'},
            'archive': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'diagnostics'", 'to': u"orm['IonInspector.Archive']"}),
            'details': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'html': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'priority': ('django.db.models.fields.IntegerField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'IonInspector.tag': {
            'Meta': {'object_name': 'Tag'},
            'archive': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tags'", 'to': u"orm['IonInspector.Archive']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['IonInspector']