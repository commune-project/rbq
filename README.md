# RBQ - Robust Broadcasting Queue
RBQ is an ActivityPub-enabled forum software in its very very very early stage of development.

DO NOT use it in a production environment, NO function is done.

# Dependencies
* Python3 (tested with 3.6.1 PyPy 7.1.1)
* PostgreSQL (tested with 10)

# Development
You must prepare a PostgreSQL database for it.

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Copy `rbq/settings.example.py` to `rbq/settings.py`.
Configure `SECRET_KEY`, `DATABASES["default"]`, `RBQ_LOCAL_DOMAINS` and so on.

    ./manage.py migrate
    ./manage.py createsuperuser
    ./manage.py runserver 0.0.0.0:8000

And you can access the unfinished page on `http://localhost:8000`.
You may need to set a proper reverse proxy before it…

# License

Copyright (C) 2019 Misaka 0x4e21

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If not, see https://www.gnu.org/licenses/.