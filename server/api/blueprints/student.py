import flask
from flask import Blueprint
from flask_login import current_user, login_required, logout_user
from functools import wraps
from datetime import datetime

from server.api.utils import jsonify_response, paginate
from server.error_handling import RouteError
from server.api.database.models import Topic, Student, Lesson
from server.api.blueprints.teacher import teacher_required

student_routes = Blueprint("student", __name__, url_prefix="/student")


def init_app(app):
    app.register_blueprint(student_routes)


@student_routes.route("/<int:student_id>/topics", methods=["GET"])
@jsonify_response
@login_required
def topics(student_id: int):
    """show topics by: finished, unfinished or haven't started"""
    student = Student.get_by_id(student_id)
    if not student:
        raise RouteError("Student does not exist.", 404)
    finished_topics = [topic.to_dict() for topic in student.topics(is_finished=True)]
    in_progress_topics = [
        topic.to_dict() for topic in student.topics(is_finished=False)
    ]
    new_topics = [
        topic.to_dict()
        for topic in Topic.query.all()
        if topic.to_dict() not in in_progress_topics
        and topic.to_dict() not in finished_topics
    ]
    return {
        "data": {
            "finished": finished_topics,
            "in_progress": in_progress_topics,
            "new": new_topics,
        }
    }


@student_routes.route("/<int:student_id>/approve", methods=["GET"])
@jsonify_response
@login_required
def approve(student_id):
    student = Student.get_by_id(student_id)
    if not student:
        raise RouteError("Student does not exist.", 404)

    if current_user != student.creator and (
        current_user.teacher == student.teacher
        or current_user.student == student
        or current_user.is_admin
    ):
        # only allow approving for the user himself or
        # the teacher that is requested. don't allow for the requester to approve.
        student.update(is_approved=True)
        return {"data": student.to_dict()}

    raise RouteError("Not authorized.", 401)


@student_routes.route("/<int:student_id>/deactivate", methods=["GET"])
@jsonify_response
@teacher_required
def deactivate(student_id):
    student = Student.get_by_id(student_id)
    if not student:
        raise RouteError("Student does not exist.", 404)

    if student.teacher != current_user.teacher:
        raise RouteError("Not authorized.", 401)

    student.update(is_active=False)
    return {"data": student.to_dict()}
