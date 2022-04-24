import os
import random
import string
import tempfile

import pytest

from vmailadmin import application
from vmailadmin import db


def random_string(length=20):
    return ''.join(
        random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(length)
    )


@pytest.fixture
def client():
    db_fd, application.config['DATABASE'] = tempfile.mkstemp()
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{file}'.format(file=application.config['DATABASE'])
    application.config['TESTING'] = True
    client = application.test_client()

    with application.app_context():
        db.create_all()

    yield client

    os.close(db_fd)
    os.unlink(application.config['DATABASE'])


def test_slash(client):
    rv = client.get('/')
    assert rv.status_code == 404


def test_admin(client):
    rv = client.get('/admin/')
    assert rv.status_code == 200


def test_accounts(client):
    rv = client.get('/admin/accounts/')
    assert rv.status_code == 200
    username = random_string()
    password = random_string()
    domain = random_string()
    rv = client.post(
        '/admin/accounts/new/', data=dict(
            username=username,
            password=password,
            domain=domain,
            enabled='y',
            url='/admin/accounts/',
        ), follow_redirects=True,
    )
    assert rv.status_code == 200
    assert username in rv.data.decode('ascii')
    assert password in rv.data.decode('ascii')
    assert domain in rv.data.decode('ascii')
    rv = client.post(
        '/admin/accounts/delete/', data=dict(
            id='{username},{domain}'.format(username=username, domain=domain),
            url='/admin/accounts/',
        ), follow_redirects=True,
    )
    assert rv.status_code == 200
    assert username not in rv.data.decode('ascii')
    assert password not in rv.data.decode('ascii')
    assert domain not in rv.data.decode('ascii')


def test_aliases(client):
    rv = client.get('/admin/aliases/')
    assert rv.status_code == 200
    address = random_string()
    goto = random_string()
    rv = client.post(
        '/admin/aliases/new/', data=dict(
            address=address,
            goto=goto,
            active='y',
            url='/admin/aliases/',
        ), follow_redirects=True,
    )
    assert rv.status_code == 200
    assert address in rv.data.decode('ascii')
    assert goto in rv.data.decode('ascii')
    rv = client.post(
        '/admin/aliases/delete/', data=dict(
            id=address,
            url='/admin/aliases/',
        ), follow_redirects=True,
    )
    assert rv.status_code == 200
    assert address not in rv.data.decode('ascii')
    assert goto not in rv.data.decode('ascii')


def test_domains(client):
    rv = client.get('/admin/domains/')
    assert rv.status_code == 200
    domain = random_string()
    rv = client.post(
        '/admin/domains/new/', data=dict(
            domain=domain,
            url='/admin/domains/',
        ), follow_redirects=True,
    )
    assert rv.status_code == 200
    assert domain in rv.data.decode('ascii')
    rv = client.post(
        '/admin/domains/delete/', data=dict(
            id=domain,
            url='/admin/aliases/',
        ), follow_redirects=True,
    )
    assert rv.status_code == 200
    assert domain not in rv.data.decode('ascii')
