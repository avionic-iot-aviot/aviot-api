from flask import Blueprint
from flask_restful import Api
from .resources.streaming import StreamingEndpoint
from .resources.photo import PhotoEndpoint
from .resources.videos import Videos
from .resources.janus_event_handler import JanusEH
from .resources.videoroom import VideoroomEndpoint
from .resources.device_services import DeviceServicesEndpoint
from .resources.devices import DevicesEndpoint
from .resources.organization import OrganizationEndpoint
from .resources.user import UserAuthEndpoint, UsersEndpoint
from .resources.streamings import StreamingsSearch
from .resources.photos import PhotosSearch
from .resources.video import VideoEndpoint

device_streaming_api = Blueprint('doorkeeper_api', __name__)
api = Api(device_streaming_api)

"""
    POST - create new organization
    GET - get organization info
"""
api.add_resource(
    OrganizationEndpoint,
    '/organization',  # POST create a new organization
)

"""
    POST - create new streaming endpoint and device to be included
    GET - get info streaming endpoint by stream id
    DELETE - 
        1. destroy streaming endpoint janus
        2. change state streaming in 'processing'
        3. convert .mjr file in .mp4 and copy the file to the root directory served by nginx
        4. processing of all photo
    PUT - change label of streaming endpoint
"""
api.add_resource(
    StreamingEndpoint,
    '/streaming_endpoint',  # POST create new streaming endpoint
    '/streaming_endpoint/<string:stream_id>/<string:organization_d>',  # DELETE delete streaming endpoint, GET stream info
    '/streaming_endpoint/<string:stream_id>',  # PUT to modify stream's label
   # '/streaming_endpoint/<string:stream_id>/photos',  # GET photos related to stream
)

"""
    POST - create new screenshot from streaming video
    GET - get info photo by photo_id
    PUT - modify photo label
    DELETE - remove photo
"""
api.add_resource(
    PhotoEndpoint,
    '/streaming_endpoint/<string:stream_id>/photo',  # POST create new photo by stream id
    '/photo/<string:photo_id>'  # ,  # GET get photo infos, DELETE to delete photo
    #'/photo/<string:photo_id>/label',  # PUT modify photo's label
)


"""
 POST - create new videoroom
 GET  - get info videoroom by name
 DELETE  - remove videoroom and send "stop-videoroom" command to all device in the videroom conf
 PUT - modify devices in videoroom
"""
api.add_resource(
    VideoroomEndpoint,
    '/videoroom/<string:videoroom_name>',
    '/videoroom'
)

"""
 POST - send command to devices ['start/stop-streaming', 'start/stop-videoroom' and performes other operations
"""
api.add_resource(
    DeviceServicesEndpoint,
    '/device_service/<string:device_id>/<string:op>'
)

# for handling janus event related to video streaming
api.add_resource(
    JanusEH,
    '/janus_event_handler'
    )

"""
    POST - create a new device
    GET - get device info
    PUT - TODO da implementare!
"""
api.add_resource(
    DevicesEndpoint,
    "/devices",  # GET info of all devices
    "/devices/<string:device_id>",  # GET info by device_id
    "/devices/<string:device_id>/status"  # PUT change status devices
)

"""
    POST - create a new user
    GET - get user info
"""
api.add_resource(
    UsersEndpoint,
    "/user"
)

"""
    POST - performe a user authentication for JWT token
"""
api.add_resource(
    UserAuthEndpoint,
    "/user/auth"
)

api.add_resource(
    StreamingsSearch,
    "/streaming_endpoints"
)

api.add_resource(
    PhotosSearch,
    '/photos'
)

api.add_resource(
    Videos,
    '/videos'
)

api.add_resource(
    VideoEndpoint,
    '/video/<string:stream_id>'
)