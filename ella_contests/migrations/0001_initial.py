# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings
import ella.core.cache.fields


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0001_initial'),
        ('core', '0002_auto_20150430_1332'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('answer', models.TextField(verbose_name='Answer text', blank=True)),
            ],
            options={
                'verbose_name': 'Answer',
                'verbose_name_plural': 'Answers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('choice', models.TextField(verbose_name='Choice text')),
                ('order', models.PositiveIntegerField(verbose_name='Order', db_index=True)),
                ('is_correct', models.BooleanField(default=False, db_index=True, verbose_name='Is correct')),
                ('inserted_by_user', models.BooleanField(default=False, verbose_name='Answare inserted by user')),
            ],
            options={
                'ordering': ('order',),
                'verbose_name': 'Choice',
                'verbose_name_plural': 'Choices',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Contest',
            fields=[
                ('publishable_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='core.Publishable')),
                ('text', models.TextField(verbose_name='Text')),
                ('text_results', models.TextField(verbose_name='Text with results', blank=True)),
                ('text_announcement', models.TextField(verbose_name='Text with announcement', blank=True)),
                ('active_from', models.DateTimeField(null=True, verbose_name='Active from', blank=True)),
                ('active_till', models.DateTimeField(null=True, verbose_name='Active till', blank=True)),
            ],
            options={
                'ordering': ('-active_from',),
                'verbose_name': 'Contest',
                'verbose_name_plural': 'Contests',
            },
            bases=('core.publishable',),
        ),
        migrations.CreateModel(
            name='Contestant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, verbose_name='First name')),
                ('surname', models.CharField(max_length=50, verbose_name='Last name')),
                ('email', models.EmailField(max_length=75, verbose_name='email')),
                ('address', models.CharField(max_length=200, verbose_name='Address')),
                ('phone_number', models.CharField(max_length=20, verbose_name='Phone number', blank=True)),
                ('winner', models.BooleanField(default=False, verbose_name='Winner')),
                ('created', models.DateTimeField(verbose_name='Created', editable=False)),
                ('contest', ella.core.cache.fields.CachedForeignKey(verbose_name='Contest', to='ella_contests.Contest')),
                ('user', ella.core.cache.fields.CachedForeignKey(verbose_name='User', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-created',),
                'verbose_name': 'Contestant',
                'verbose_name_plural': 'Contestants',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveIntegerField(verbose_name='Order', db_index=True)),
                ('text', models.TextField()),
                ('is_required', models.BooleanField(default=True, db_index=True, verbose_name='Is required')),
                ('contest', ella.core.cache.fields.CachedForeignKey(verbose_name='Contest', to='ella_contests.Contest')),
                ('photo', ella.core.cache.fields.CachedForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='Photo', blank=True, to='photos.Photo', null=True)),
            ],
            options={
                'ordering': ('order',),
                'verbose_name': 'Question',
                'verbose_name_plural': 'Questions',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='question',
            unique_together=set([('contest', 'order')]),
        ),
        migrations.AlterUniqueTogether(
            name='contestant',
            unique_together=set([('contest', 'email')]),
        ),
        migrations.AddField(
            model_name='choice',
            name='question',
            field=ella.core.cache.fields.CachedForeignKey(verbose_name='Question', to='ella_contests.Question'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='choice',
            unique_together=set([('question', 'order')]),
        ),
        migrations.AddField(
            model_name='answer',
            name='choice',
            field=ella.core.cache.fields.CachedForeignKey(verbose_name='Choice', to='ella_contests.Choice'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='answer',
            name='contestant',
            field=ella.core.cache.fields.CachedForeignKey(verbose_name='Contestant', to='ella_contests.Contestant'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='answer',
            unique_together=set([('contestant', 'choice')]),
        ),
    ]
