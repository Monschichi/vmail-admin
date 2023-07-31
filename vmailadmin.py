#!/usr/bin/env python3
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib import sqla
from flask_admin.form import SecureForm
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import DeclarativeMeta

application = Flask(__name__, instance_relative_config=True)
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
application.config.from_pyfile('settings.py')

db = SQLAlchemy(application)
BaseModel: DeclarativeMeta = db.Model

migrate = Migrate(application, db)


class Accounts(BaseModel):
    __tablename__ = 'accounts'
    username = db.Column(db.String(64), primary_key=True, nullable=False)
    domain = db.Column(db.String(255), primary_key=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    sendonly = db.Column(db.Boolean, nullable=False, default=False)


class AccountsAdmin(sqla.ModelView):
    column_display_pk = True
    form_base_class = SecureForm
    form_columns = ['username', 'domain', 'password', 'enabled', 'sendonly']


class Aliases(BaseModel):
    __tablename__ = 'aliases'
    address = db.Column(db.String(320), primary_key=True, nullable=False)
    goto = db.Column(db.String(320), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)


class AliasesAdmin(sqla.ModelView):
    column_display_pk = True
    form_base_class = SecureForm
    form_columns = ['address', 'goto', 'active']


class Domains(BaseModel):
    __tablename__ = 'domains'
    domain = db.Column(db.String(255), primary_key=True, nullable=False)


class DomainsAdmin(sqla.ModelView):
    column_display_pk = True
    form_base_class = SecureForm
    form_columns = ['domain']


class DeniedRecipients(BaseModel):
    __tablename__ = 'deniedrecipients'
    username = db.Column(db.String(64), primary_key=True, nullable=False)
    domain = db.Column(db.String(255), primary_key=True, nullable=False)


class DeniedRecipientsAdmin(sqla.ModelView):
    column_display_pk = True
    form_base_class = SecureForm
    form_columns = ['username', 'domain']


# Create admin
admin = Admin(
    application, name='vmail admin',
    template_mode='bootstrap3',
)
admin.add_view(AccountsAdmin(Accounts, db.session))
admin.add_view(AliasesAdmin(Aliases, db.session))
admin.add_view(DomainsAdmin(Domains, db.session))
admin.add_view(DeniedRecipientsAdmin(DeniedRecipients, db.session))

if __name__ == '__main__':
    # Start app
    application.run()  # pragma: no cover
