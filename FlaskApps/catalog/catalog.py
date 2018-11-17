import flask
from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify, make_response
from flask import session as login_session
from sqlalchemy import create_engine, func, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, CategoryItem, User

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import random
import string
import requests
import httplib2
import json


CLIENT_ID = json.loads(
    open('/var/www/FlaskApps/catalog/client_secrets.json', 'r').read())['web']['client_id']

app = Flask(__name__)

engine = create_engine('sqlite:////var/www/FlaskApps/catalog/dbfile/catalog.db',
                       connect_args={'check_same_thread': False},)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    """show login page"""
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['GET', 'POST'])
def gconnect():
    """login connection flow"""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/FlaskApps/catalog/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    # result = json.loads(h.request(url, 'GET')[1])
    result = h.request(url, 'GET')[1]
    result = json.loads(result.decode("utf-8"))
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is \
                                  already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("you are now logged in as %s" % login_session['username'])
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; border-radius:\
    150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print("done!")
    return output


# User Helper Functions
def createUser(login_session):
    """create new user in database for every unique login account"""
    newUser = User(name=login_session['username'], email=login_session[
                   'email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    """get user object"""
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    """get user ID"""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    """logout"""
    access_token = login_session['access_token']
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user \
                                 not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
           % login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("You are now logged out.")
        return redirect('/catalog')
        return response
    else:

        response = make_response(json.dumps('Failed to revoke token\
                                            for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Home page
@app.route('/')
@app.route('/catalog/')
def showcategories():
    """home page show categories and latest added items """
    categories = session.query(Categories).all()
    items = session.query(CategoryItem).order_by(CategoryItem
                                                 .id.desc()).limit(3)
    return render_template('categories.html',
                           categories=categories, items=items)


# Create a category
@app.route('/catalog/new/', methods=['GET', 'POST'])
def newCategory():
    """create a new category from logged in users"""
    if 'username' not in login_session:
        return redirect('/login')

    user_id = login_session['user_id']

    if request.method == 'POST':
        newCategory = Categories(name=request.form['name'], user_id=user_id)
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showcategories'))
    else:
        return render_template('newcategory.html')


# Edit a category
@app.route('/catalog/<int:category_id>/edit/', methods=['GET', 'POST'])
def editcategory(category_id):
    """edit a category from logged in users"""
    if 'username' not in login_session:
        return redirect('/login')
    editedCategory = session.query(
        Categories).filter_by(id=category_id).one()
    if editedCategory.user_id != login_session['user_id']:
        flash('Category can only be edited by the creator')
        return redirect(url_for('showcategories'))
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            return redirect(url_for('showcategories'))
    else:
        return render_template(
            'editcategory.html', category=editedCategory)


# Delete a category
@app.route('/catalog/<int:category_id>/delete/', methods=['GET', 'POST'])
def deletecategory(category_id):
    """delete a category from logged in users"""
    if 'username' not in login_session:
        return redirect('/login')
    categoryToDelete = session.query(
        Categories).filter_by(id=category_id).one()
    if categoryToDelete.user_id != login_session['user_id']:
        flash('Category can only be deleted by the creator')
        return redirect(url_for('showcategories'))
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        return redirect(
            url_for('showcategories'))
    else:
        return render_template(
            'deletecategory.html', category=categoryToDelete)


# Display categories on the left and items for selected category on the right
@app.route('/catalog/<int:category_id>/')
@app.route('/catalog/<int:category_id>/items/')
def categoryitem(category_id):
    """display categories on the left and items for
    selected category on the right"""
    categories = session.query(Categories).all()
    category = session.query(Categories).filter_by(id=category_id).one()
    items = session.query(CategoryItem).filter_by(category_id=category.id)
    items_count = session.query(CategoryItem).filter_by(category_id=category
                                                        .id).count()
    return render_template('categoryitem.html', categories=categories,
                           category=category, items=items,
                           items_count=items_count)


# Create a new category item
@app.route('/catalog/<int:category_id>/new/', methods=['GET', 'POST'])
def newitem(category_id):
    """create new item page"""
    if 'username' not in login_session:
        return redirect('/login')

    user_id = login_session['user_id']
    category = session.query(Categories).filter_by(id=category_id).one()
    if request.method == 'POST':
        newItem = CategoryItem(name=request.form['name'],
                               description=request.form['description'],
                               category_id=category_id,
                               category_name=category.name,
                               user_id=user_id)
        session.add(newItem)
        flash('New Item %s Successfully Created' % newItem.name)
        session.commit()
        return redirect(url_for('categoryitem', category_id=category_id))
    else:
        return render_template('newitem.html', category_id=category_id,
                               category=category)


# Edit a category item
@app.route('/catalog/<int:category_id>/items/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editItem(category_id, item_id):
    """edit item page"""
    if 'username' not in login_session:
        return redirect('/login')

    editedItem = session.query(CategoryItem).filter_by(id=item_id).one()
    categories = session.query(Categories).all()
    if editedItem.user_id != login_session['user_id']:
        flash('Item can only be edited by the creator')
        return redirect(url_for('categoryitem', category_id=category_id))

    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category']:
            editedItem.category_name = request.form['category']
        session.add(editedItem)
        session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('categoryitem', category_id=category_id))
    else:
        return render_template('edititem.html', categories=categories,
                               item=editedItem)


# Delete a category item
@app.route('/catalog/<int:category_id>/items/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    """delete an item from logged in users"""
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Categories).filter_by(id=category_id).one()
    itemToDelete = session.query(CategoryItem).filter_by(id=item_id).one()
    if itemToDelete.user_id != login_session['user_id']:
        flash('Item can only be deleted by the creator')
        return redirect(url_for('categoryitem', category_id=category_id))
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Category Item Successfully Deleted')
        return redirect(url_for('categoryitem', category_id=category_id))
    else:
        return render_template('deleteitem.html', item=itemToDelete)


# Show description of a category item
@app.route('/catalog/<int:category_id>/<int:item_id>/')
def showitemdescription(category_id, item_id):
    """show descriptions for an item"""
    item = session.query(CategoryItem).filter_by(id=item_id).one()
    return render_template('itemdescription.html', item=item)


# ADD JSON ENDPOINT
@app.route('/catalog/JSON')
def categoriesJSON():
    """all category JSON endpoint"""
    categories = session.query(Categories).all()
    return jsonify(categories=[dict(c.serialize, items=[i.serialize
                                    for i in c.item])
                   for c in categories])


@app.route('/catalog/<int:category_id>/JSON')
def categoryJSON(category_id):
    """selected category JSON endpoint"""
    category = session.query(Categories).filter_by(id=category_id).one()
    items = session.query(CategoryItem).filter_by(
        category_id=category_id).all()
    return jsonify(items=[i.serialize for i in items])


@app.route('/items/JSON')
def itemsJSON():
    """all items JSON endpoint"""
    items = session.query(CategoryItem).all()
    return jsonify(items=[i.serialize for i in items])


@app.route('/catalog/<int:category_id>/items/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    """selected item JSON endpoint"""
    item = session.query(CategoryItem).filter_by(id=item_id).one()
    return jsonify(item=item.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.run()
