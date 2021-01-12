from flask import request
from flask_restful import Resource
import app.models.streaming
import app.common.janus_api
from app.api.resources.schema import PhotoSchema
import re
import datetime
from flask_jwt_extended import jwt_required, current_user
from app import is_normal_user


class PhotosSearch(Resource):
    """
      risorsa ideata per le ricerche su foto
    """
    @jwt_required
    @is_normal_user
    def get(self):

        # role: admin, normal user
        searchkeys = request.args
        query = []

        device_id = searchkeys.get('device_id', None)

        if device_id is not None:
            stream_info_objs = app.models.streaming.StreamInfo.objects(device_id=app.models.device.Device.objects(
                name=device_id,
                organization=current_user.organization
            ).first(), deleted=False)

            if len(stream_info_objs) == 0:
                return []

            p_query = {"stream": {"$in": [ stream_info_obj.id for stream_info_obj in stream_info_objs]}}

            query.append(p_query)

        stream_id = searchkeys.get('stream_id', None)
        if stream_id is not None:
            stream_info_obj = app.models.streaming.StreamInfo.objects(s_id=stream_id, deleted=False).first()

            if stream_info_obj is None:
                return []

            p_query = {"stream": stream_info_obj.id}
            query.append(p_query)

        # date format: YYYYMMGGHHmmss 20200121093945 => 2020-01-21 09:39:45
        date_from = searchkeys.get('datefrom', None)

        if date_from is not None:
            try:
                date_obj = datetime.datetime.strptime(date_from, "%Y%m%d%H%M%S")
                p_query = {'date_start': {"$gte": date_obj}}
                query.append(p_query)
            except ValueError:
                date_obj = None  # TODO send a error message

        date_to = searchkeys.get('dateto', None)
        if date_to is not None:
            try:
                date_obj = datetime.datetime.strptime(date_to, "%Y%m%d%H%M%S")
                p_query = {'date_stop': {"$lte": date_obj}}
                query.append(p_query)
            except ValueError:
                date_obj = None  # TODO send a error message

        label = searchkeys.get('label', None)
        if label is not None and len(label.strip()) > 0:
            label = label.strip()
            try:
                regx = re.compile(label, re.IGNORECASE)
                p_query = {'label': regx}
                query.append(p_query)
            except:
                pass

        # I can't use $regex operator because I need MongoDB > 4.02


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
                areas = search_area.split("|")  # get areas
                for area in areas:
                    points = area.split(';')
                    points_a = [[float(p.split(',')[0]), float(p.split(',')[1])] for p in points]
                    polygons.append(points_a)

                p_query = {"pos": {
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
        org_clause = {'organization': current_user.organization.id}
        query.append(del_clause)
        query.append(org_clause)

        total_query = {"$and": query}  # build query
        photo_schema = PhotoSchema()

        return photo_schema.dump(
            app.models.streaming.Photo.objects(__raw__=total_query),
            many=True
        )

