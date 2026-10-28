import os
from flask import Flask, jsonify, request
from flask_cors import CORS

from services.auth_service import (
    SESSION_COOKIE_NAME,
    SESSION_DURATION_SECONDS,
    auth_service,
    require_auth,
)
from services.soil_service import soil_service
from services.crop_service import crop_service
from services.fertilizer_service import fertilizer_service
from services.season_service import season_service

app = Flask(__name__)
CORS(app)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "message": "AI-Based Smart Agriculture System API is operational.",
        "ml_models": {
            "soil_model": soil_service.model is not None,
            "crop_disease_model": crop_service.model is not None,
            "fertilizer_model": fertilizer_service.model is not None,
            "crop_season_dataset": season_service.df is not None
        }
    })

def set_auth_cookie(response, token):
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=SESSION_DURATION_SECONDS,
        httponly=True,
        secure=request.is_secure,
        samesite="Lax",
        path="/",
    )
    return response


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    user, error = auth_service.register(data.get("email"), data.get("password"))
    if error:
        status = 409 if error.startswith("An account") else 400
        return jsonify({"error": error}), status

    token = auth_service.create_session(user["id"])
    response = jsonify({"user": user})
    response.status_code = 201
    return set_auth_cookie(response, token)


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    user = auth_service.authenticate(data.get("email"), data.get("password"))
    if user is None:
        return jsonify({"error": "Email or password is incorrect."}), 401

    token = auth_service.create_session(user["id"])
    return set_auth_cookie(jsonify({"user": user}), token)


@app.route("/api/auth/me", methods=["GET"])
@require_auth
def current_user():
    return jsonify({"user": request.auth_user})


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    token = request.cookies.get(SESSION_COOKIE_NAME)
    auth_service.delete_session(token)
    response = jsonify({"message": "Logged out."})
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        httponly=True,
        secure=request.is_secure,
        samesite="Lax",
        path="/",
    )
    return response

# PAGE 1 API: Soil Image -> Soil Type Prediction -> ML Fertilizer Recommendation
@app.route("/api/soil/analyze", methods=["POST"])
@require_auth
def analyze_soil():
    if "image" not in request.files:
        return jsonify({"error": "No soil image file provided in request."}), 400

    image_file = request.files["image"]
    if image_file.filename == "":
        return jsonify({"error": "Empty image filename."}), 400

    # Optional form parameter inputs for precision recommendation
    crop = request.form.get("crop", None)
    N = request.form.get("N", None)
    P = request.form.get("P", None)
    K = request.form.get("K", None)
    pH = request.form.get("pH", None)

    image_bytes = image_file.read()
    result = soil_service.analyze_soil_image(
        image_bytes,
        crop=crop,
        N=N,
        P=P,
        K=K,
        pH=pH
    )

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)

# PAGE 2 API: Crop Image -> Crop/Disease Prediction -> ML Treatment Recommendation
@app.route("/api/crop/analyze", methods=["POST"])
@require_auth
def analyze_crop():
    if "image" not in request.files:
        return jsonify({"error": "No crop/plant image file provided in request."}), 400

    image_file = request.files["image"]
    if image_file.filename == "":
        return jsonify({"error": "Empty image filename."}), 400

    image_bytes = image_file.read()
    result = crop_service.analyze_crop_image(image_bytes)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)

# Direct ML Fertilizer Recommendation API
@app.route("/api/fertilizer/recommend", methods=["POST"])
@require_auth
def recommend_fertilizer():
    data = request.get_json() or {}
    soil_type = data.get("soil_type", "Black Soil")
    crop = data.get("crop", "Rice")
    N = data.get("N", 50)
    P = data.get("P", 40)
    K = data.get("K", 35)
    pH = data.get("pH", 6.5)
    organic_matter = data.get("organic_matter", 2.0)
    moisture = data.get("moisture", 45)
    temperature = data.get("temperature", 28)
    season = data.get("season", "Kharif")

    result = fertilizer_service.recommend(
        soil_type=soil_type, crop=crop, N=N, P=P, K=K, pH=pH,
        organic_matter=organic_matter, moisture=moisture,
        temperature=temperature, season=season
    )

    return jsonify(result)

# PAGE 3 API: Crop Name -> Season & Regional Recommendation
@app.route("/api/crop/season", methods=["GET", "POST"])
@require_auth
def crop_season():
    if request.method == "POST":
        data = request.get_json() or {}
        crop = data.get("crop", "")
        region = data.get("region", "")
    else:
        crop = request.args.get("crop", "")
        region = request.args.get("region", "")

    if not crop:
        return jsonify({"error": "Please specify a crop name parameter."}), 400

    result = season_service.get_crop_season(crop_name=crop, region=region)
    return jsonify(result)

# Helper API: List Available Crops
@app.route("/api/crops", methods=["GET"])
@require_auth
def list_crops():
    crops = season_service.list_available_crops()
    return jsonify({"crops": crops})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
