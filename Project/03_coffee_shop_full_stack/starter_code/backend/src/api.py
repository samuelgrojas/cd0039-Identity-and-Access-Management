import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


db_drop_and_create_all()

# ROUTES
@app.route('/drinks', methods=['GET'])
def get_drinks():
    try:
        drinks = Drink.query.all()
        drinks_short = [drink.short() for drink in drinks]

        return jsonify({
            "success": True,
            "drinks": drinks_short
        }), 200
    except Exception as e:
        print(e)
        abort(500)


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    try:
        drinks = Drink.query.all()
        drinks_long = [drink.long() for drink in drinks]

        return jsonify({
            "success": True,
            "drinks": drinks_long
        }), 200
    except Exception as e:
        print(e)
        abort(500)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drinks(payload):
    try:
        body = request.get_json()
        title = body.get('title', None)
        recipe = body.get('recipe', None)

        if title is None or recipe is None:
            abort(400)

        if isinstance(recipe, dict):
            recipe = [recipe]

        drink = Drink(title=title, recipe=json.dumps(recipe))
        drink.insert()

        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        }), 200
    except Exception as e:
        print(e)
        abort(500)


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drinks(payload, drink_id):
    try:
        drink = Drink.query.get(drink_id)
        if drink is None:
            abort(404)

        body = request.get_json()
        title = body.get('title', None)
        recipe = body.get('recipe', None)

        if title is not None:
            drink.title = title
        if recipe is not None:
            if isinstance(recipe, dict):
                recipe = [recipe]
            drink.recipe = json.dumps(recipe)

        drink.update()

        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        }), 200
    except Exception as e:
        print(e)
        abort(500)


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, drink_id):
    try:
        drink = Drink.query.get(drink_id)
        if drink is None:
            abort(404)

        drink.delete()

        return jsonify({
            "success": True,
            "delete": drink_id
        }), 200
    except Exception as e:
        print(e)
        abort(500)


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify({
        "success": False,
        "error": ex.status_code,
        "message": ex.error['description']
    })
    response.status_code = ex.status_code
    return response
