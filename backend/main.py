from flask import request, jsonify
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from config import app, db
from models import Destination
import aux_functions
from flask import send_from_directory, Flask, send_file

hubLatitude = None
hubLongitude = None
numRoutes = None

@app.route("/")
def serve_frontend():
    return send_from_directory("../frontend", "index.html")

# Serve static assets
@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("../frontend", path)

@app.route("/plan_optimized_route", methods=["POST"])
def plan_optimized_route_handler():
    global hubLatitude, hubLongitude, numRoutes
    if hubLatitude is None or hubLongitude is None or numRoutes is None:
        return jsonify({"message": "Hub or number of routes address not available"}), 400
    #print(f"Printing from plan_optimized_route_handler: {hubLatitude} and {hubLongitude}")
    destinations_data = request.json.get("destinations")
    destinations = [(d.get('id'),d.get('latitude'), d.get('longitude'), d.get('deadline')) for d in destinations_data]
    print(destinations)
    optimized_routes = aux_functions.plan_optimized_route(destinations, hubLatitude, hubLongitude, numRoutes)
    return jsonify({"optimized_route": optimized_routes }), 200

@app.route("/route_map")
def serve_route_map():
    return send_from_directory(directory='backend', path='route_map.html')
    

@app.route("/destinations", methods=["GET"])
def get_destinations():
    destinations = Destination.query.all()
    json_destinations = list(map(lambda x: x.to_json(), destinations))
    return jsonify({"destinations": json_destinations})

@app.route("/create_hub", methods=["POST"])
def print_hub():
    global hubLatitude, hubLongitude, numRoutes
    hubLatitude=request.json.get("hubLatitude")
    hubLongitude=request.json.get("hubLongitude")
    numRoutes=request.json.get('numRoutes')
    print(f"the hubLatitiude is{hubLatitude} and hubLongitude is {hubLongitude}, and numRoutes are {numRoutes}")
    if hubLatitude and hubLongitude:
        return jsonify({"message": "Hub Address committed"}), 201

@app.route("/create_destination", methods=["POST"])
def create_destination():
    address = request.json.get("address")
    latitude = request.json.get("latitude")
    longitude = request.json.get("longitude")
    deadline = request.json.get("deadline")

    if not latitude or not longitude or not deadline:
        return (
            jsonify({"message": "You must include the coordinates and deadline"}),
            400,
        )

    new_destination = Destination(address=address,latitude=latitude, longitude=longitude, deadline=deadline)
    try:
        db.session.add(new_destination)
        db.session.commit()
    except Exception as e:
        return jsonify({"message": str(e)}), 400

    return jsonify({"message": "Destination created!"}), 201


@app.route("/update_destination/<int:user_id>", methods=["PATCH"])
def update_destination(user_id):
    destination = session.get(Destination, user_id)

    if not destination:
        return jsonify({"message": "User not found"}), 404

    data = request.json
    destination.latitude = data.get("latitude", destination.latitude)
    destination.longitude = data.get("longitude", destination.longitude)
    destination.deadline = data.get("deadline", destination.deadline)

    db.session.commit()

    return jsonify({"message": "User updated."}), 200


@app.route("/delete_destination/<int:user_id>", methods=["DELETE"])
def delete_destination(user_id):
    destination = session.get(Destination, user_id)

    if not destination:
        return jsonify({"message": "destination not found"}), 404

    db.session.delete(destination)
    db.session.commit()

    return jsonify({"message": "destination deleted!"}), 200


if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Done 1")
        print("Done 2")
    
    app.run(debug=True)
