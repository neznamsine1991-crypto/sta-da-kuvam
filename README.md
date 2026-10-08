# Šta Da Kuvam?

Moderna Django platforma za srpske recepte, približne nutritivne vrednosti i **DEMO** upoređivanje cena namirnica.

## Pokretanje

1. Napravite virtuelno okruženje: `python -m venv .venv`
2. Aktivirajte ga i instalirajte pakete: `python -m pip install -r requirements.txt`
3. Kopirajte `.env.example` kao `.env` i promenite `SECRET_KEY`.
4. Napravite bazu: `python manage.py makemigrations recipes prices shopping meal_plans users` pa `python manage.py migrate`.
5. Učitajte uzorak: `python manage.py seed_data`.
6. Pokrenite: `python manage.py runserver`.

Administracija je na `/admin/`; nalog se pravi komandom `python manage.py createsuperuser`.

## Besplatno javno objavljivanje

Projekt je pripremljen za Render: napravi GitHub repozitorij, pošalji ovaj projekt na GitHub i u Renderu izaberi **New > Blueprint**, pa odaberi repozitorij. Render će pročitati `render.yaml` i objaviti aplikaciju na besplatnoj `.onrender.com` adresi.

Besplatni Render plan služi za demonstraciju: uspava se nakon neaktivnosti i lokalna SQLite baza nije trajna nakon redeploya. Za trajne korisničke naloge, liste i slike potreban je plaćeni persistent disk ili PostgreSQL baza.

## Cene

Uzorke cena označava `DEMO / uzorak`. One nisu uživo niti predstavljaju stvarne prodajne cene. Model `IngredientPrice` namerno odvaja poreklo i period važenja, što omogućava kasniji CSV/API uvoz bez vezivanja za jedan market.
