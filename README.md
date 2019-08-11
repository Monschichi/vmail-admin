# vmail-admin
[![Build Status](https://travis-ci.org/Monschichi/vmail-admin.svg?branch=master)](https://travis-ci.org/Monschichi/vmail-admin)
[![Maintainability](https://api.codeclimate.com/v1/badges/63428d0d453b592b15f0/maintainability)](https://codeclimate.com/github/Monschichi/vmail-admin/maintainability)
[![Coverage Status](https://coveralls.io/repos/github/Monschichi/vmail-admin/badge.svg?branch=master)](https://coveralls.io/github/Monschichi/vmail-admin?branch=master)

This is a web interface for managing virtual mailboxes.

## setup
This setup is intended for postfix and dovecot. It may work with other software.
In this setup we assume the use of sqlite as database, other databases work as well.

### folders
Sqlite is stored in `/home/sqlite/mail`, the user which runs the wsgi must have write access, postfix and dovecot need read access. E.g. `0755` with `www-data` as owner works fine.
This git repository is cloned to `/var/www/vmail-admin`. 

### venv
We use a [virtual-env](https://docs.python.org/3/library/venv.html) to manage needed python libraries.
```shell script
root@example /var/www/vmail-admin # python3 -m venv .venv
root@example /var/www/vmail-admin # . .venv/bin/activate
(.venv) root@example /var/www/vmail-admin # pip install -r requirements.txt 
``` 

### nginx
/etc/nginx/nginx.conf:
```
server {
	listen 0.0.0.0:443 default_server ssl http2;
	listen [::]:443 default_server ssl http2;
	server_name mail.example.com;

	# certs sent to the client in SERVER HELLO are concatenated in ssl_certificate
	ssl_certificate /etc/ssl/cert.pem;
	ssl_certificate_key /etc/ssl/key.pem;
	ssl_trusted_certificate /etc/ssl/chain.pem;
    ssl_stapling_file /etc/ssl/ocsp.der;

	location /admin/ {
		auth_basic "login";
		auth_basic_user_file /etc/nginx/htpasswd;
		uwsgi_pass unix:///run/uwsgi/vmail-admin/socket;
		include /etc/nginx/uwsgi_params;
	}
}
```

Create and fill `/etc/nginx/htpasswd`.

### uwsgi
/etc/uwsgi/vmail-admin.ini:
```
[uwsgi]
uid = www-data
processes = 1
master = true
plugins = python3
wsgi-file = /var/www/vmail-admin/vmailadmin.py
virtualenv = /var/www/vmail-admin/.venv
chdir = /var/www/vmail-admin/
```

### postfix
If you want to use dedicated submission port for sending mail you want to add to your /etc/postfix/master.cf:
```
smtp      inet  n       -       n       -       -       smtpd
    -o smtpd_sasl_auth_enable=no
submission inet n       -       n       -       -       smtpd
    -o syslog_name=postfix/submission
    -o smtpd_tls_security_level=encrypt
    -o smtpd_sasl_auth_enable=yes
    -o smtpd_sasl_type=dovecot
    -o smtpd_sasl_path=private/auth
    -o smtpd_sasl_security_options=noanonymous
    -o smtpd_relay_restrictions=permit_sasl_authenticated,reject
    -o smtpd_sender_login_maps=sqlite:/etc/postfix/sql/sender-login-maps.cf
    -o smtpd_sender_restrictions=reject_non_fqdn_sender,reject_sender_login_mismatch,permit_sasl_authenticated,reject
    -o smtpd_client_restrictions=permit_sasl_authenticated,reject
    -o smtpd_recipient_restrictions=permit_sasl_authenticated,reject
    -o smtpd_helo_required=no
    -o smtpd_helo_restrictions=
    -o milter_macro_daemon_name=ORIGINATING
```

/etc/postfix/main.cf:
```
mydestination = 
smtpd_recipient_restrictions = permit_mynetworks
                               check_recipient_access sqlite:/etc/postfix/sql/recipient-access.cf
virtual_transport = lmtp:unix:private/dovecot-lmtp
virtual_alias_maps = sqlite:/etc/postfix/sql/aliases.cf
virtual_mailbox_maps = sqlite:/etc/postfix/sql/accounts.cf
virtual_mailbox_domains = sqlite:/etc/postfix/sql/domains.cf
local_recipient_maps = $virtual_mailbox_maps
alias_database =
alias_maps = 
```

/etc/postfix/sql/accounts.cf:
```
dbpath = /home/sqlite/mail
query = select 1 as found from accounts where username = '%u' and domain = '%d' and enabled = 1 LIMIT 1;
```

/etc/postfix/sql/aliases.cf:
```
dbpath = /home/sqlite/mail
table = aliases
select_field = goto
where_field = address
additional_conditions = and active = 1
```

/etc/postfix/sql/domains.cf:
```
dbpath = /home/sqlite/mail
query = SELECT domain FROM domains WHERE domain='%s'
```

/etc/postfix/sql/recipient-access.cf:
```
dbpath = /home/sqlite/mail
query = select case when sendonly = 1 then 'REJECT' else 'OK' end AS access from accounts where username = '%u' and domain = '%d' and enabled = 1 LIMIT 1;
```

/etc/postfix/sql/sender-login-maps.cf:
```
dbpath = /home/sqlite/mail
query = select username || '@' || domain as 'owns' from accounts where username = '%u' AND domain = '%d' and enabled = 1 union select goto AS 'owns' from aliases where address = '%u@%d' and active = 1;
```

### dovecot
/etc/dovecot/dovecot.conf:
```
service lmtp {
    unix_listener /var/spool/postfix/private/dovecot-lmtp {
        mode = 0660
        group = postfix
        user = postfix
    }
    process_min_avail = 4
    user = vmail
}

service auth {
    unix_listener /var/spool/postfix/private/auth {
        mode = 0660
        user = postfix
        group = postfix
    }

    unix_listener auth-userdb {
        mode = 0660
        user = vmail
        group = vmail
    }
}

passdb {
    driver = sql
    args = /etc/dovecot/dovecot-sql.conf
}

userdb {
    driver = sql
    args = /etc/dovecot/dovecot-sql.conf
}
```

/etc/dovecot/dovecot-sql.conf:
```
driver = sqlite
connect = /home/sqlite/mail
default_pass_scheme = SHA512-CRYPT 

password_query = SELECT username AS user, domain, password FROM accounts WHERE username = '%n' AND domain = '%d' and enabled = 1;
user_query = SELECT '*:storage=0M' AS quota_rule FROM accounts WHERE username = '%n' AND domain = '%d' AND sendonly = 0;
iterate_query = SELECT username, domain FROM accounts where sendonly = 0;
```
