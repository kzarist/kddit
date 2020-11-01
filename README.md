# kddit.kalli.st
### reddit frontend


Running

~~~
$ uwsgi --ini app.ini
~~~

Nginx config

~~~
server {
    listen 80;
    merge_slashes off;
    location / {
        include uwsgi_params;
        uwsgi_pass unix:/path/to/kddit.kalli.st/socket;
    }
} 
~~~