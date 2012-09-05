import re
from docutils.core import publish_parts

from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound

from pyramid.view import view_config
from pyramid.view import forbidden_view_config

from pyramid.security import remember
from pyramid.security import forget
from pyramid.security import authenticated_userid

from .models import DBSession
from .models import Page
from .models import Dog
from .security import USERS

# regular expression used to find WikiWords
wikiwords = re.compile(r"\b([A-Z]\w+[A-Z]+\w+)")

@view_config(route_name='view_wiki')
def view_wiki(request):
    return HTTPFound(location = request.route_url('view_page',
                                                  pagename='FrontPage'))

@view_config(route_name='view_page', renderer='templates/view_page.pt')
def view_page(request):
    pagename = request.matchdict['pagename']
    page = DBSession.query(Page).filter_by(name=pagename).first()
    if page is None:
        return HTTPNotFound('No such page')

    def check(match):
        word = match.group(1)
        exists = DBSession.query(Page).filter_by(name=word).all()
        if exists:
            view_url = request.route_url('view_page', pagename=word)
            return '<a href="%s">%s</a>' % (view_url, word)
        else:
            add_url = request.route_url('add_page', pagename=word)
            return '<a href="%s">%s</a>' % (add_url, word)

    content = publish_parts(page.data, writer_name='html')['html_body']
    content = wikiwords.sub(check, content)
    edit_url = request.route_url('edit_page', pagename=pagename)
    logged_in = authenticated_userid(request)
    return dict(page=page, content=content, logged_in=logged_in, edit_url=edit_url)

@view_config(route_name='add_page', renderer='templates/edit_page.pt', permission='edit')
def add_page(request):
    name = request.matchdict['pagename']
    if 'form.submitted' in request.params:
        body = request.params['body']
        page = Page(name, body)
        DBSession.add(page)
        return HTTPFound(location = request.route_url('view_page',
                                                      pagename=name))
    save_url = request.route_url('add_page', pagename=name)
    page = Page('', '')
    logged_in = authenticated_userid(request)
    return dict(page=page, logged_in=logged_in, save_url=save_url)

@view_config(route_name='edit_page', renderer='templates/edit_page.pt', permission='edit')
def edit_page(request):
    name = request.matchdict['pagename']
    page = DBSession.query(Page).filter_by(name=name).one()
    if 'form.submitted' in request.params:
        page.data = request.params['body']
        DBSession.add(page)
        return HTTPFound(location = request.route_url('view_page',
                                                      pagename=name))
    logged_in = authenticated_userid(request)
    return dict(
        page=page,
        logged_in=logged_in,
        save_url = request.route_url('edit_page', pagename=name),
        )


# Public view
@view_config(route_name='view_dog', renderer='templates/view_dog.pt')
def view_dog(request):
    dogid = request.matchdict['dogid']
    dogid = int(dogid)
    dog = DBSession.query(Dog).filter_by(id=dogid).first()
    if dog is None:
        return HTTPNotFound('No such dog')

    edit_url = request.route_url('edit_dog', dogid=dogid)
    return dict(dog=dog, content='', edit_url=edit_url)


@view_config(route_name='add_dog', renderer='templates/edit_dog.pt', permission='edit')
def add_dog(request):
    dogid = request.matchdict['dogid']
    if 'form.submitted' in request.params:
        name = request.params['name']
        age = int(request.params['age']) or 0
        race = request.params['race']
        dog = Dog(name, age, race)
        DBSession.add(dog)
        return HTTPFound(location = request.route_url('view_dog',
                                                      dogid=dogid))
    save_url = request.route_url('add_dog', dogid=dogid)
    dog = Dog('', 0, '')
    logged_in = authenticated_userid(request)
    return dict(dog=dog, logged_in=logged_in, save_url=save_url)


@view_config(route_name='edit_dog', renderer='templates/edit_dog.pt', permission='edit')
def edit_dog(request):
    dogid = request.matchdict['dogid']
    dogid = int(dogid)
    dog = DBSession.query(Dog).filter_by(id=dogid).one()
    if 'form.submitted' in request.params:
        dog.name = request.params['name']
        dog.age = int(request.params['age']) or 0
        dog.race = request.params['race']
        DBSession.add(dog)
        return HTTPFound(location = request.route_url('view_dog',
                                                      dogid=dogid))
    logged_in = authenticated_userid(request)
    return dict(
        dog=dog,
        logged_in=logged_in,
        save_url = request.route_url('edit_dog', dogid=dogid),
        )


# Login/Logout Views
@view_config(route_name='login', renderer='templates/login.pt')
@forbidden_view_config(renderer='templates/login.pt')
def login(request):
    login_url = request.route_url('login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/' # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    message = ''
    login = ''
    password = ''
    if 'form.submitted' in request.params:
        login = request.params['login']
        password = request.params['password']
        if USERS.get(login) == password:
            headers = remember(request, login)
            return HTTPFound(location = came_from,
                             headers = headers)
        message = 'Failed login'

    return dict(
        message = message,
        url = request.application_url + '/login',
        came_from = came_from,
        login = login,
        password = password,
        )


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location = request.route_url('view_wiki'),
                     headers = headers)


conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_tutorial_db" script
    to initialize your database tables.  Check your virtual
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""

