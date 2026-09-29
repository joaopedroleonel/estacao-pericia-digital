from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from app.routes.api import api_bp
from app.routes.dashboard import dashboard_bp


ERROR_CODES = {
    400: "bad_request",
    404: "not_found",
    405: "method_not_allowed",
    415: "unsupported_media_type",
}


def register_blueprints(app: Flask) -> None:
    for blueprint in (dashboard_bp, api_bp):
        app.register_blueprint(blueprint)


def register_error_handlers(app: Flask) -> None:
    app.register_error_handler(HTTPException, _handle_http_error)


def _handle_http_error(failure: HTTPException):
    if request.path.startswith("/api/"):
        return jsonify(error=ERROR_CODES.get(failure.code, "error")), failure.code
    return render_template("error.html", status=failure.code), failure.code
