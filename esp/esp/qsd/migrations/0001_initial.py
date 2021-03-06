# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'QuasiStaticData'
        db.create_table('qsd_quasistaticdata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('path', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['datatree.DataTree'])),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('nav_category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['web.NavBarCategory'])),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('disabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('keywords', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('qsd', ['QuasiStaticData'])

        # Adding model 'ESPQuotations'
        db.create_table('qsd_espquotations', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('display', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 8, 21, 20, 34, 43, 561773))),
        ))
        db.send_create_signal('qsd', ['ESPQuotations'])

    def backwards(self, orm):
        
        # Deleting model 'QuasiStaticData'
        db.delete_table('qsd_quasistaticdata')

        # Deleting model 'ESPQuotations'
        db.delete_table('qsd_espquotations')

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'datatree.datatree': {
            'Meta': {'unique_together': "(('name', 'parent'),)", 'object_name': 'DataTree'},
            'friendly_name': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lock_table': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child_set'", 'null': 'True', 'to': "orm['datatree.DataTree']"}),
            'range_correct': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'rangeend': ('django.db.models.fields.IntegerField', [], {}),
            'rangestart': ('django.db.models.fields.IntegerField', [], {}),
            'uri': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'uri_correct': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'qsd.espquotations': {
            'Meta': {'object_name': 'ESPQuotations'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 8, 21, 20, 34, 43, 561773)'}),
            'display': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'qsd.quasistaticdata': {
            'Meta': {'object_name': 'QuasiStaticData'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'nav_category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['web.NavBarCategory']"}),
            'path': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['datatree.DataTree']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'users.espuser': {
            'Meta': {'object_name': 'ESPUser', 'db_table': "'auth_user'", '_ormbases': ['auth.User'], 'proxy': 'True'}
        },
        'web.navbarcategory': {
            'Meta': {'object_name': 'NavBarCategory'},
            'anchor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['datatree.DataTree']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'include_auto_links': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'long_explanation': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        }
    }

    complete_apps = ['qsd']
