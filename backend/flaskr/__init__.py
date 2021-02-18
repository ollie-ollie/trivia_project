import os
from flask import (
    Flask, request, abort, jsonify,
    redirect, url_for
)
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from  sqlalchemy.sql.expression import func

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    
    CORS(app)
    #CORS(app, resources={r"*": {'origins': '*'}})

    @app.after_request
    def after_request(response):
        response.headers.add('Acces-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Acces-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')

        return response

    def paginate_questions(request, query):
        page = request.args.get('page', 1, int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        questions = [question.format() for question in query]

        return questions[start:end]

    @app.route('/categories', methods=['GET'])
    def get_categories():
        query_categories = Category.query.order_by('id').all()
        categories = {category.id: category.type for category in query_categories}

        if len(categories) == 0:
            abort(404)

        else:
            return jsonify({
                'success': True,
                'categories': categories
                })

    @app.route('/questions', methods=['GET'])
    def get_questions():
        query_questions = Question.query.order_by('id').all()
        current_questions = paginate_questions(request, query_questions)

        query_categories = Category.query.order_by('id').all()
        
        if len(current_questions) == 0:
            abort(404)

        else:
            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(query_questions),
                'categories': {category.id: category.type for category in query_categories},
                'current_category': None
            })

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        try:
            if not ('question' in body and 'answer' in body and \
                'category' in body and 'difficulty' in body):
                abort(404)
            
            new_question = Question(
                question=body['question'],
                answer=body['answer'],
                category=body['category'],
                difficulty=body['difficulty']
            )
            new_question.insert()

            return jsonify({
                'success': True,
                'created_question': new_question.id
            })

        except:
            abort(422)


    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            query_questions = Question.query.order_by('id').all()
            current_questions = paginate_questions(request, query_questions)

            return jsonify({
                'success': True,
                'deleted_question': question_id,
                'questions': current_questions,
                'total_questions': len(query_questions)
            })

        except:
            abort(422)

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        try:
            body = request.get_json()
            search = body['search']

            query_questions = Question.query.order_by('id').\
                filter(Question.question.ilike('%{}%'.format(search))).all()
            current_questions = paginate_questions(request, query_questions)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(query_questions),
                'current_category': None
            })
        
        except:
            abort(400)

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        try:
            query_questions = Question.query.filter(Question.category == category_id).all()
            questions = paginate_questions(request, query_questions)
            
            current_category = Category.query.filter(Category.id == category_id).one().format()
            
            return jsonify({
                'success': True,
                'questions': questions,
                'total_questions': len(query_questions),
                'current_category': current_category['id']
            })

        except:
            abort(404)

    @app.route('/quizzes', methods=['POST'])
    def play_quizz():
        try:
            body = request.get_json()
            previous_questions = body['previous_questions']
            quizz_category = body['quiz_category']
            
            if quizz_category['id'] == 0:
                quizz_question_query = Question.query.\
                    filter(Question.id.notin_(previous_questions))
                    
            else:
                quizz_question_query = Question.query.\
                    filter(
                        Question.id.notin_(previous_questions),
                        Question.category == quizz_category['id']
                    )
            
            quizz_question = quizz_question_query.\
                order_by(func.random()).\
                first().\
                format()

            return jsonify({
                'success': True,
                'question': quizz_question
            })

        except:
            abort(422)
            
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'bad request'
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'not found'
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'method not allowed'
        }), 405

    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'unprocessable'
        }), 422
    
    return app

        