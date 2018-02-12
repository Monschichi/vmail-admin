#!/usr/bin/env python3

import flask_admin as admin
from flask import Flask
from flask_admin.contrib import sqla
from flask_sqlalchemy import SQLAlchemy

application = Flask(__name__, instance_relative_config=True)
application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
application.config.from_pyfile("settings.py")

db = SQLAlchemy(application)


class Accounts(db.Model):
    __tablename__ = "accounts"
    username = db.Column(db.String(64), primary_key=True, nullable=False)
    domain = db.Column(db.String(255), primary_key=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    sendonly = db.Column(db.Boolean, nullable=False, default=False)

    def __str__(self):
        return self.desc


class AccountsAdmin(sqla.ModelView):
    column_display_pk = True
    form_columns = ["username", "domain", "password", "enabled", "sendonly"]


class Aliases(db.Model):
    __tablename__ = "aliases"
    address = db.Column(db.String(320), primary_key=True, nullable=False)
    goto = db.Column(db.String(320), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)


class AliasesAdmin(sqla.ModelView):
    column_display_pk = True
    form_columns = ["address", "goto", "active"]


class Domains(db.Model):
    __tablename__ = "domains"
    domain = db.Column(db.String(255), primary_key=True, nullable=False)


class DomainsAdmin(sqla.ModelView):
    column_display_pk = True
    form_columns = ["domain"]


# Create admin
admin = admin.Admin(application, name="vmail admin", template_mode="bootstrap3")
admin.add_view(AccountsAdmin(Accounts, db.session))
admin.add_view(AliasesAdmin(Aliases, db.session))
admin.add_view(DomainsAdmin(Domains, db.session))

if __name__ == "__main__":
    # Create DB
    db.create_all()

    # Start app
    application.run()
