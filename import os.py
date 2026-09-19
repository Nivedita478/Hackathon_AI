import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


load_dotenv()

app = Flask(__name__)

CORS(app)

# -----------------------------
# DATABASE CONFIGURATION
# -----------------------------

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL is missing from .env")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# -----------------------------
# JWT CONFIGURATION
# -----------------------------

app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY",
    "darukaa-earth-secret-key"
)

db = SQLAlchemy(app)
jwt = JWTManager(app)


# ============================================================
# DATABASE MODELS
# ============================================================

class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    projects = db.relationship(
        "Project",
        backref="owner",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Project(db.Model):

    __tablename__ = "projects"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    sites = db.relationship(
        "Site",
        backref="project",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Site(db.Model):

    __tablename__ = "sites"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    latitude = db.Column(
        db.Float,
        nullable=False
    )

    longitude = db.Column(
        db.Float,
        nullable=False
    )

    polygon = db.Column(
        db.JSON,
        nullable=True
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False
    )

    carbon = db.Column(
        db.Float,
        default=0
    )

    biodiversity = db.Column(
        db.Float,
        default=0
    )


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return jsonify({
        "success": True,
        "message": "Darukaa.Earth API is running"
    })


# ============================================================
# REGISTER
# ============================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required"
        }), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:

        return jsonify({
            "success": False,
            "message": "Name, email and password are required"
        }), 400

    existing_user = User.query.filter_by(
        email=email
    ).first()

    if existing_user:

        return jsonify({
            "success": False,
            "message": "Email already registered"
        }), 409

    user = User(
        name=name,
        email=email,
        password=generate_password_hash(password)
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Registration successful"
    }), 201


# ============================================================
# LOGIN
# ============================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "Request body is required"
        }), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(
        email=email
    ).first()

    if not user:

        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401

    if not check_password_hash(
        user.password,
        password
    ):

        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401

    token = create_access_token(
        identity=str(user.id)
    )

    return jsonify({
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    })


# ============================================================
# PROFILE
# ============================================================

@app.route("/api/profile", methods=["GET"])
@jwt_required()
def profile():

    user_id = int(get_jwt_identity())

    user = db.session.get(
        User,
        user_id
    )

    if not user:

        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    return jsonify({
        "success": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    })


# ============================================================
# CREATE PROJECT
# ============================================================

@app.route("/api/projects", methods=["POST"])
@jwt_required()
def create_project():

    user_id = int(get_jwt_identity())

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "Request body is required"
        }), 400

    name = data.get("name", "").strip()
    description = data.get(
        "description",
        ""
    ).strip()

    if not name:

        return jsonify({
            "success": False,
            "message": "Project name is required"
        }), 400

    project = Project(
        name=name,
        description=description,
        user_id=user_id
    )

    db.session.add(project)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Project created successfully",
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description
        }
    }), 201


# ============================================================
# GET PROJECTS
# ============================================================

@app.route("/api/projects", methods=["GET"])
@jwt_required()
def get_projects():

    user_id = int(get_jwt_identity())

    projects = Project.query.filter_by(
        user_id=user_id
    ).all()

    result = []

    for project in projects:

        result.append({
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "site_count": len(project.sites)
        })

    return jsonify({
        "success": True,
        "projects": result
    })


# ============================================================
# ADD SITE
# ============================================================

@app.route(
    "/api/projects/<int:project_id>/sites",
    methods=["POST"]
)
@jwt_required()
def add_site(project_id):

    user_id = int(get_jwt_identity())

    project = Project.query.filter_by(
        id=project_id,
        user_id=user_id
    ).first()

    if not project:

        return jsonify({
            "success": False,
            "message": "Project not found"
        }), 404

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "Request body is required"
        }), 400

    name = data.get(
        "name",
        "Unnamed Site"
    )

    latitude = data.get("latitude")
    longitude = data.get("longitude")
    polygon = data.get("polygon")

    if latitude is None or longitude is None:

        return jsonify({
            "success": False,
            "message": "Latitude and longitude are required"
        }), 400

    site = Site(
        name=name,
        latitude=float(latitude),
        longitude=float(longitude),
        polygon=polygon,
        project_id=project.id,
        carbon=float(data.get("carbon", 0)),
        biodiversity=float(
            data.get("biodiversity", 0)
        )
    )

    db.session.add(site)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Site added successfully",
        "site": {
            "id": site.id,
            "name": site.name,
            "latitude": site.latitude,
            "longitude": site.longitude,
            "polygon": site.polygon,
            "carbon": site.carbon,
            "biodiversity": site.biodiversity
        }
    }), 201


# ============================================================
# GET PROJECT DETAILS
# ============================================================

@app.route(
    "/api/projects/<int:project_id>",
    methods=["GET"]
)
@jwt_required()
def get_project(project_id):

    user_id = int(get_jwt_identity())

    project = Project.query.filter_by(
        id=project_id,
        user_id=user_id
    ).first()

    if not project:

        return jsonify({
            "success": False,
            "message": "Project not found"
        }), 404

    sites = []

    for site in project.sites:

        sites.append({
            "id": site.id,
            "name": site.name,
            "latitude": site.latitude,
            "longitude": site.longitude,
            "polygon": site.polygon,
            "carbon": site.carbon,
            "biodiversity": site.biodiversity
        })

    return jsonify({
        "success": True,
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "sites": sites
        }
    })


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

with app.app_context():

    db.create_all()


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )