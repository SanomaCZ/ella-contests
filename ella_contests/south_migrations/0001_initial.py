# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Contest'
        db.create_table('ella_contests_contest', (
            ('publishable_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.Publishable'], unique=True, primary_key=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('text_results', self.gf('django.db.models.fields.TextField')()),
            ('active_from', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('active_till', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('ella_contests', ['Contest'])

        # Adding model 'Question'
        db.create_table('ella_contests_question', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contest', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ella_contests.Contest'])),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('photo', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['photos.Photo'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('is_required', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True)),
        ))
        db.send_create_signal('ella_contests', ['Question'])

        # Adding unique constraint on 'Question', fields ['contest', 'order']
        db.create_unique('ella_contests_question', ['contest_id', 'order'])

        # Adding model 'Choice'
        db.create_table('ella_contests_choice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ella_contests.Question'])),
            ('choice', self.gf('django.db.models.fields.TextField')()),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('is_correct', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('inserted_by_user', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('ella_contests', ['Choice'])

        # Adding unique constraint on 'Choice', fields ['question', 'order']
        db.create_unique('ella_contests_choice', ['question_id', 'order'])

        # Adding model 'Contestant'
        db.create_table('ella_contests_contestant', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contest', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ella_contests.Contest'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('surname', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('phone_number', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('count_guess', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
            ('winner', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('ella_contests', ['Contestant'])

        # Adding unique constraint on 'Contestant', fields ['contest', 'email']
        db.create_unique('ella_contests_contestant', ['contest_id', 'email'])

        # Adding model 'Answer'
        db.create_table('ella_contests_answer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contestant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ella_contests.Contestant'])),
            ('choice', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ella_contests.Choice'])),
            ('answer', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('ella_contests', ['Answer'])

        # Adding unique constraint on 'Answer', fields ['contestant', 'choice']
        db.create_unique('ella_contests_answer', ['contestant_id', 'choice_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Answer', fields ['contestant', 'choice']
        db.delete_unique('ella_contests_answer', ['contestant_id', 'choice_id'])

        # Removing unique constraint on 'Contestant', fields ['contest', 'email']
        db.delete_unique('ella_contests_contestant', ['contest_id', 'email'])

        # Removing unique constraint on 'Choice', fields ['question', 'order']
        db.delete_unique('ella_contests_choice', ['question_id', 'order'])

        # Removing unique constraint on 'Question', fields ['contest', 'order']
        db.delete_unique('ella_contests_question', ['contest_id', 'order'])

        # Deleting model 'Contest'
        db.delete_table('ella_contests_contest')

        # Deleting model 'Question'
        db.delete_table('ella_contests_question')

        # Deleting model 'Choice'
        db.delete_table('ella_contests_choice')

        # Deleting model 'Contestant'
        db.delete_table('ella_contests_contestant')

        # Deleting model 'Answer'
        db.delete_table('ella_contests_answer')


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
        'core.author': {
            'Meta': {'object_name': 'Author'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'photo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['photos.Photo']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '255'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'core.category': {
            'Meta': {'unique_together': "(('site', 'tree_path'),)", 'object_name': 'Category'},
            'app_data': ('app_data.fields.AppDataField', [], {'default': "'{}'"}),
            'content': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'template': ('django.db.models.fields.CharField', [], {'default': "'category.html'", 'max_length': '100'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tree_parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Category']", 'null': 'True', 'blank': 'True'}),
            'tree_path': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'core.publishable': {
            'Meta': {'object_name': 'Publishable'},
            'announced': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'app_data': ('app_data.fields.AppDataField', [], {'default': "'{}'"}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Author']", 'symmetrical': 'False'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Category']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'photo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['photos.Photo']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'publish_from': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(3000, 1, 1, 0, 0, 0, 2)', 'db_index': 'True'}),
            'publish_to': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Source']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'static': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'core.source': {
            'Meta': {'object_name': 'Source'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'ella_contests.answer': {
            'Meta': {'unique_together': "(('contestant', 'choice'),)", 'object_name': 'Answer'},
            'answer': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'choice': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ella_contests.Choice']"}),
            'contestant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ella_contests.Contestant']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'ella_contests.choice': {
            'Meta': {'ordering': "('order',)", 'unique_together': "(('question', 'order'),)", 'object_name': 'Choice'},
            'choice': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inserted_by_user': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_correct': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ella_contests.Question']"})
        },
        'ella_contests.contest': {
            'Meta': {'ordering': "('-active_from',)", 'object_name': 'Contest', '_ormbases': ['core.Publishable']},
            'active_from': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'active_till': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'publishable_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.Publishable']", 'unique': 'True', 'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'text_results': ('django.db.models.fields.TextField', [], {})
        },
        'ella_contests.contestant': {
            'Meta': {'ordering': "('-created',)", 'unique_together': "(('contest', 'email'),)", 'object_name': 'Contestant'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'contest': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ella_contests.Contest']"}),
            'count_guess': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'winner': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'ella_contests.question': {
            'Meta': {'ordering': "('order',)", 'unique_together': "(('contest', 'order'),)", 'object_name': 'Question'},
            'contest': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ella_contests.Contest']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_required': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'photo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['photos.Photo']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'photos.photo': {
            'Meta': {'object_name': 'Photo'},
            'app_data': ('app_data.fields.AppDataField', [], {'default': "'{}'"}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'photo_set'", 'symmetrical': 'False', 'to': "orm['core.Author']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'height': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '255'}),
            'important_bottom': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'important_left': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'important_right': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'important_top': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Source']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['ella_contests']