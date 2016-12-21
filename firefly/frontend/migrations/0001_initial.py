# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-19 13:38
from __future__ import unicode_literals

import audiofield.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import hitcount.models
import mezzanine.core.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blog', '0018_remove_blogpost_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('english_name', models.CharField(max_length=30, null=True, unique=True, verbose_name='英文姓名')),
                ('chinese_name', models.CharField(max_length=40, null=True, verbose_name='中文姓名')),
                ('country', models.CharField(max_length=40, null=True, verbose_name='国家')),
                ('description', models.TextField(verbose_name='作者简介')),
            ],
            options={
                'verbose_name_plural': '作者',
                'verbose_name': '作者',
            },
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('blogpost_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='blog.BlogPost')),
                ('titlezh', models.CharField(max_length=100, null=True, verbose_name='中文书名')),
                ('isbn', models.CharField(max_length=100, null=True, verbose_name='ISBN')),
                ('npid', models.CharField(default='npid', max_length=30, null=True)),
                ('publication_date', models.DateField(null=True, verbose_name='出版日期')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='frontend.Author', verbose_name='作者')),
            ],
            options={
                'verbose_name_plural': '图书',
                'verbose_name': '图书',
            },
            bases=('blog.blogpost', hitcount.models.HitCountMixin),
        ),
        migrations.CreateModel(
            name='BookCategory',
            fields=[
                ('blogcategory_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='blog.BlogCategory')),
                ('cover', models.ImageField(null=True, upload_to='categories', verbose_name='图片')),
                ('npid', models.CharField(default='npid', max_length=30, null=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name_plural': '书籍分类',
                'verbose_name': '书籍分类',
                'ordering': ('order',),
                'abstract': False,
            },
            bases=('blog.blogcategory', models.Model),
        ),
        migrations.CreateModel(
            name='Chapter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('no', models.IntegerField(db_index=True)),
                ('title', models.CharField(max_length=100, null=True, verbose_name='章节标题')),
                ('npid', models.CharField(default='npid', max_length=30, null=True)),
                ('content', mezzanine.core.fields.RichTextField(verbose_name='Content')),
                ('audio_file', audiofield.fields.AudioField(blank=True, help_text='Allowed type - .mp3, .wav, .ogg', upload_to='audiofiles', verbose_name='音频文件')),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='frontend.Book', verbose_name='所属书籍')),
            ],
            options={
                'verbose_name_plural': '章节管理',
                'verbose_name': '章节管理',
            },
        ),
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='名称')),
                ('website', models.URLField(verbose_name='网址')),
            ],
            options={
                'verbose_name_plural': '出版社',
                'verbose_name': '出版社',
            },
        ),
        migrations.CreateModel(
            name='TrackPosition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.DurationField(verbose_name='播放位置')),
                ('time', models.DateTimeField(blank=True, default=django.utils.timezone.now, verbose_name='时间')),
                ('chapter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='frontend.Chapter', verbose_name='章节')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name_plural': '文件位置',
                'verbose_name': '文件位置',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar', models.ImageField(blank=True, upload_to='avatar')),
                ('bio', models.TextField()),
                ('shirt_size', models.CharField(choices=[('S', 'Small'), ('M', 'Medium'), ('L', 'Large')], default='S', max_length=1)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': '会员管理',
                'verbose_name': '会员管理',
            },
        ),
        migrations.AddField(
            model_name='book',
            name='publisher',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='frontend.Publisher', verbose_name='出版社'),
        ),
    ]
