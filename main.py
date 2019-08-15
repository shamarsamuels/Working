import webapp2
import jinja2
import os
import time
from google.appengine.ext import ndb
from google.appengine.api import search
from google.appengine.api import users
from database import load
from app_models import make_User, User, Family
import json


the_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

families = Family.query()
states = {}

for family in families:
    if family.state in states:
        if not family.city in states[family.state]:
            states[family.state].append(family.city)
    else:
        states[family.state] = [family.city]

states = json.dumps(states)

families_query = Family.query()

def get_current_user(current_page):
    google_user = users.get_current_user()
    if google_user:
        google_user_id = str(google_user.user_id())
        print(google_user_id)
        user = User.query().filter(User.user_id == google_user_id).get()
        if not user:
            user = make_User(google_user_id)

        return user
    else:
        current_page.redirect('/')


def tokenize_autocomplete(phrase):
    a = []
    for i in range(0, len(phrase) + 1):
        a.append(phrase[0:i])

    return a


index = search.Index(name='item_autocomplete')
for item in families_query:  # item = ndb.model
    doc_id = item.key.urlsafe()
    name = ','.join(tokenize_autocomplete(item.name))
    state = item.state
    document = search.Document(
        doc_id=doc_id,
        fields=[
            search.TextField(name='name', value=name),
            search.TextField(name='state', value=state)
        ])
    index.put(document)


class LoginPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            nickname = user.nickname()
            logout_url = users.create_logout_url('/')
            self.response.write('Welcome, {}! (<a href="{}">sign out</a>)'.format(nickname, logout_url))
        else:
            login_url = users.create_login_url('/search')
            self.redirect(login_url)


class MainPage(webapp2.RequestHandler):
    def get(self):
        user = get_current_user(self)
        if user:
            main_page_template = the_jinja_env.get_template('templates/main_page.html')
            self.response.write(main_page_template.render({'states':states}))

    def post(self):
        family_id = self.request.get('id')
        if family_id:
            self.redirect('/family?id=' + family_id)
        else:
            self.redirect('/search')


class FamilyPage(webapp2.RequestHandler):
    def get(self):
        user = get_current_user(self)
        if user:
            family_id = self.request.get('id')
            if family_id:
                if family_id.isdigit():
                    family_id = int(family_id)
                    family = Family.get_by_id(family_id)
                    family_page_template = the_jinja_env.get_template('templates/family_page.html')
                    ratings = json.loads(family.ratings)
                    ratings = json.dumps(ratings)

                    user_ratings = json.loads(user.ratings)
                    user_family_ratings = [0, 0, 0, 0, 0]
                    if str(family_id) in user_ratings:
                        print('Visited Family')
                        user_family_ratings = user_ratings[str(family_id)]
                    else:
                        print('Never Visited Family')
                        user_ratings[str(family_id)] = [0, 0, 0, 0, 0]
                        user.user_ratings = json.dumps(user_ratings)
                        user.put()
                    
                    user_family_ratings = json.dumps(user_family_ratings)
                    self.response.write(family_page_template.render({'family_id': family_id, 'name':family.name, 'state':family.state, 'city':family.city, 'family_image':'/images/families/'+ family.house_image, 'house_image':'/images/houses/'+ family.house_image, 'ratings':ratings, 'user_ratings':user_family_ratings}))
                    return

            self.redirect('/search')


class Load(webapp2.RequestHandler):
    def get(self):
        load()

        families = Family.query()
        states = {}

        for family in families:
            if family.state in states:
                if not family.city in states[family.state]:
                    states[family.state].append(family.city)
            else:
                states[family.state] = [family.city]

        states = json.dumps(states)

        self.redirect('/search')


class InputHandler(webapp2.RequestHandler):
    def post(self):
        input = self.request.get('input')
        data = {
            'response': False,
        }

        results = search.Index(name="item_autocomplete").search(
            "name:" + input
        )
        families = []
        if results:
            for result in results:
                family = ndb.Key(urlsafe=result.doc_id).get()
                if family:
                    families.append({
                        'name': family.name,
                        'id': family.key.id(),
                    })
        if len(families) > 0:
            data['response'] = families

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(data))


class UpdateHandler(webapp2.RequestHandler):
    def post(self):
        user = get_current_user(self)
        if user:
            row = self.request.get('row')
            star = self.request.get('star')
            family_id = self.request.get('family_id')
            if row and star and family_id:
                user_ratings = json.loads(user.ratings)
                if family_id in user_ratings:
                    user_ratings[family_id][int(row) - 1] = int(star)
                else:
                    user_ratings[family_id] = [0, 0, 0, 0, 0]
                    user_ratings[family_id][int(row) - 1] = int(star)

                user.ratings = json.dumps(user_ratings)
                user.put()


app = webapp2.WSGIApplication([
    ('/', LoginPage),
    ('/search', MainPage),
    ('/load', Load),
    ('/family', FamilyPage),
    ('/input', InputHandler),
    ('/update', UpdateHandler)
], debug=True)
