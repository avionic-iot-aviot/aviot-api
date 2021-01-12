from flask import request
from flask_restful import Resource
from flask import current_app
import app.models.streaming
import app.models.device
from app.api.resources.schema import StreamingEndpointSchema,  StreamInfoSchema
import app.common.janus_api
import datetime
import re
import random
import time
from flask_jwt_extended import jwt_required, current_user, get_jwt_claims
from app import is_normal_user, is_device_user


"""
from mongoengine.queryset.visitor import Q

# Get published posts
Post.objects(Q(published=True) | Q(publish_date__lte=datetime.now()))

# Get top posts
Post.objects((Q(featured=True) & Q(hits__gte=1000)) | Q(hits__gte=5000))
"""


class StreamingsSearch(Resource):

    @jwt_required
    @is_normal_user
    def get(self):

        # role: admin, normal user
        searchkeys = request.args
        query = []
        live = searchkeys.get('live', None)

        # with pymongo query... but with QuerySet? TODO I will try as soon as possible...
        if live is not None:
            live = True if re.match("[TtRrUe]", live) else False
            if live is True:
                p_query = {'status': 'live'}
            else:
                p_query = {'status': {"$in": ['processing', 'stored']}}

            query.append(p_query)

        device_id = searchkeys.get('device_id', None)

        claims = get_jwt_claims()
        organization_d = None  # organization's domain

        if "super-admin" in claims.keys():
            if claims['super-admin'] is True:
                organization_d = searchkeys.get('organization', None)
                if organization_d is None:
                    return {
                               'error': {
                                   'id': 2,
                                   'description': "validation error",
                                   'details': {}
                               }
                           }, 422

                organization = app.models.organization.Organization.objects(domain=organization_d).first()

                if organization is None:
                    return {
                               'error': {
                                   'id': 2,
                                   'description': "organization doesn't not exist",
                                   'details': {}
                               }
                           }, 422
        else:
            organization = current_user.organization

        if device_id is not None:
            device_obj = app.models.device.Device.objects(
                name=device_id,
                organization=organization
            ).first()
            if device_obj is None:
                return []

            p_query = {"device_id": device_obj.id}
            query.append(p_query)

        # date format: YYYYMMGGHHmmss 20200121093945 => 2020-01-21 09:39:45
        date_from = searchkeys.get('datefrom', None)

        if date_from is not None:
            try:
                date_obj = datetime.datetime.strptime(date_from, "%Y%m%d%H%M%S")
                p_query = {'date_start': {"$gte": date_obj}}
                query.append(p_query)
            except ValueError:
                date_obj = None

        date_to = searchkeys.get('dateto', None)
        if date_to is not None:
            try:
                date_obj = datetime.datetime.strptime(date_to, "%Y%m%d%H%M%S")
                p_query = {'date_stop': {"$lte": date_obj}}
                query.append(p_query)
            except ValueError:
                date_obj = None

        label = searchkeys.get('label', None)
        if label is not None and len(label.strip()) > 0:

            label = label.strip()
            regx = re.compile(label, re.IGNORECASE)
            # I can't use $regex operator because I need MongoDB > 4.02
            p_query = {'label': regx}
            query.append(p_query)

        """
        db.<collection>.find( { <location field> :
                         { $geoIntersects :
                           { $geometry :
                             { type : "<GeoJSON object type>" ,
                               coordinates : [ <coordinates> ]
                      } } } } )
        
        tracking = [[0, 3], [4, 4], [4, 7], [0, 7], [0, 3]]  # OK
        tracking = [[0, 5], [4, 5], [4, 7], [0, 7], [0, 5]]   # KO
        """

        # example data:
        # [long1-1,lat1-1;long2-1,lat2-1;long3-1,lat3-1; ...;longN-1,latN-1 |
        # long1-2,lat1-2;long2-2,lat2-2;long3-2,lat3-2;  ...;longN-2,latN-2 |
        # long1-N,lat1-N;long2-N,lat2-N;long3-N,lat3-N;  ...;longN-N,latN-N ]
        search_area = searchkeys.get('search_area', None)
        polygons = []
        if search_area is not None:
            try:
                search_area = search_area[1:-1]  # remove brackets
                areas = search_area.split("|")   # get areas
                for area in areas:
                    points = area.split(';')
                    points_a = [[float(p.split(',')[0]), float(p.split(',')[1])] for p in points]
                    polygons.append(points_a)

                p_query = {"tracking.steps": {
                    "$geoIntersects": {
                        "$geometry": {
                            "type": "Polygon",
                            "coordinates": polygons
                        }
                    }
                }}

                query.append(p_query)

            except:
                search_area = None

        # retrieve streaminfo with deleted flag set to False

        del_clause = {'deleted': False}
        org_clause = {'organization': organization.id}
        query.append(del_clause)
        query.append(org_clause)

        total_query = {"$and": query}  # build query
        stream_schema = StreamInfoSchema()

        return stream_schema.dump(
            app.models.streaming.StreamInfo.objects(__raw__=total_query),
            many=True
        )[0], 200



