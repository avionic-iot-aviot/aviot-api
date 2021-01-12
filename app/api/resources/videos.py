from flask import request
from flask_restful import Resource
from app.api.resources.schema import VideosSearch
import random
import time
from flask_jwt_extended import jwt_required, get_jwt_identity


class Videos(Resource):
    """
    risorsa ideata per le ricerche su video TODO DA COMPLETARE!!!
    """

    @jwt_required
    def get(self):

        json_data = request.get_json()
        videos_schema = VideosSearch()
        data, error = videos_schema.load(json_data)

        print(data, error)

