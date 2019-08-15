from google.appengine.ext import ndb
from google.appengine.api import search 
import os, random
import json


class Family(ndb.Model):
    name = ndb.StringProperty(required=True)
    name_lower = ndb.ComputedProperty(lambda self: self.name.lower())
    city = ndb.StringProperty(required=True)
    state = ndb.StringProperty(required=True)
    family_image = ndb.StringProperty(required=False)
    house_image = ndb.StringProperty(required=False)
    ratings = ndb.StringProperty(required=False)


class User(ndb.Model):
    user_id = ndb.StringProperty(required = True)
    ratings = ndb.StringProperty(required= False)

def make_Family(name, city, state):
    new_family = Family(name=name, city=city, state=state)
    new_family.family_image = str(random.randint(1,61))
    new_family.house_image = str(random.randint(1,69))
    new_family.ratings = json.dumps([{
        'total_rating': random.randint(2, 5),
        'times_rated': 1,
    },{
        'total_rating': random.randint(2, 5),
        'times_rated': 1,
    },{
        'total_rating': random.randint(2, 5),
        'times_rated': 1,
    },{
        'total_rating': random.randint(2, 5),
        'times_rated': 1,
    },{
        'total_rating': random.randint(2, 5),
        'times_rated': 1,
    }])
    new_family.put()


def make_User(user_id):
    user = User(user_id=user_id)
    user.ratings = json.dumps({})
    user.put()
    return user
