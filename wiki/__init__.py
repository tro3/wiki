
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask.ext.wtf import Form
from wtforms import (TextField, TextAreaField, PasswordField)
from wtforms.validators import (InputRequired, ValidationError)

from wiki import Wiki
from processors import Processors


bprint = Blueprint('wiki', 'wiki',
                   url_prefix='/wiki',
                   template_folder='templates')

wiki = Wiki('wiki/content')



## Forms

class URLForm(Form):
    url = TextField('', [InputRequired()])

    def validate_url(form, field):
        if wiki.exists(field.data):
            raise ValidationError('The URL "%s" exists already.' % field.data)

    def clean_url(self, url):
        return Processors().clean_url(url)


class SearchForm(Form):
    term = TextField('', [InputRequired()])


class EditorForm(Form):
    title = TextField('', [InputRequired()])
    body = TextAreaField('', [InputRequired()])
    tags = TextField('')



## Views

@bprint.route('/')
#@protect
def home():
    page = wiki.get('home')
    if page:
        return display('home')
    return render_template('home.html')


@bprint.route('/index/')
#@protect
def index():
    pages = wiki.index()
    return render_template('index.html', pages=pages)


@bprint.route('/<path:url>/')
#@protect
def display(url):
    page = wiki.get_or_404(url)
    return render_template('page.html', page=page)


@bprint.route('/create/', methods=['GET', 'POST'])
#@protect
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for('.edit', url=form.clean_url(form.url.data)))
    return render_template('create.html', form=form)


@bprint.route('/edit/<path:url>/', methods=['GET', 'POST'])
#@protect
def edit(url):
    page = wiki.get(url)
    form = EditorForm(obj=page)
    if form.validate_on_submit():
        if not page:
            page = wiki.get_bare(url)
        form.populate_obj(page)
        page.save()
        flash('"%s" was saved.' % page.title, 'success')
        return redirect(url_for('wiki.display', url=url))
    return render_template('editor.html', form=form, page=page)


@bprint.route('/preview/', methods=['POST'])
#@protect
def preview():
    a = request.form
    data = {}
    processed = Processors(a['body'])
    data['html'], data['body'], data['meta'] = processed.out()
    return data['html']


@bprint.route('/move/<path:url>/', methods=['GET', 'POST'])
#@protect
def move(url):
    page = wiki.get_or_404(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        newurl = form.url.data
        wiki.move(url, newurl)
        return redirect(url_for('.display', url=newurl))
    return render_template('move.html', form=form, page=page)


@bprint.route('/delete/<path:url>/')
#@protect
def delete(url):
    page = wiki.get_or_404(url)
    wiki.delete(url)
    flash('Page "%s" was deleted.' % page.title, 'success')
    return redirect(url_for('home'))


@bprint.route('/tags/')
#@protect
def tags():
    tags = wiki.get_tags()
    return render_template('tags.html', tags=tags)


@bprint.route('/tag/<string:name>/')
#@protect
def tag(name):
    tagged = wiki.index_by_tag(name)
    return render_template('tag.html', pages=tagged, tag=name)


@bprint.route('/search/', methods=['GET', 'POST'])
#@protect
def search():
    form = SearchForm()
    if form.validate_on_submit():
        results = wiki.search(form.term.data)
        return render_template('search.html', form=form,
                               results=results, search=form.term.data)
    return render_template('search.html', form=form, search=None)
