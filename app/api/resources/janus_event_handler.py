from flask_restful import Resource
from flask import request
import app.common.video2image
import app.models.streaming
import subprocess
from flask import current_app
import datetime
from app import is_device_user


class JanusEH(Resource):

    #@is_device_user
    def post(self):

        # role: device user JANUS
        #TODO autenticare anche Janus??

        """
            [{
                'emitter': 'MyJanusInstance',
                'type': 64,
                'timestamp': 1574346215607016,
                'session_id': 4263778186181629,
                'handle_id': 1869482203929689,
                'event':
                    {'plugin': 'janus.plugin.streaming',
                    'data': {
                        'event': 'destroyed',
                        'id': 2827999271
                        }
                    }
            }]
        """

        json_data = request.get_json()

        if json_data['event']['plugin'] == 'janus.plugin.streaming' and \
            json_data['event']['data']['event'] == 'destroyed':

            stream_id = json_data['event']['data']['id']
            video_filename = str(stream_id) + ".mp4"
            video_path = current_app.config['PATH_VIDEOS'] + "/" + video_filename

            try:
                out_bytes = subprocess.check_output(
                    [
                        "/opt/janus/bin/janus-pp-rec",
                        "/opt/janus/bin/%s.mjr" % stream_id,
                        video_path
                    ],
                    stderr=subprocess.STDOUT
                )

                #TODO check output
                stream_obj = app.models.streaming.StreamInfo.objects(s_id=stream_id).first()
                stream_obj.status = 'stored'
                stream_obj.url = current_app.config['URL_VIDEOS'] + video_filename
                video_start_ts = float(stream_obj.date_start.timestamp())
                stream_obj.save()

                # array of photos
                photos = app.models.streaming.Photo.objects(
                    stream=stream_obj)

                if len(photos) == 0 or photos is None:
                    return

                for photo in photos:
                    frame_ts = float(photo.date.timestamp())
                    photo_filename = str(photo.photo_id) + ".jpg"
                    photo_path = current_app.config['PATH_IMGS'] + "/" + photo_filename

                    try:

                        app.common.video2image.save_frame(
                            video_path,
                            video_start_ts,
                            frame_ts,
                            photo_path
                        )

                        photo.url = current_app.config['URL_IMGS'] + photo_filename
                        photo.status = "available"
                    except (app.common.video2image.InputError, app.common.video2image.OutputError,
                            app.common.video2image.TimestampError) as e:
                        continue

                    try:
                        l_date_streaming = stream_obj.tracking.l_date
                        date_photo = photo.date

                        last_td = None
                        index_ts = -1
                        for d in l_date_streaming:
                            td = abs((d - date_photo).total_seconds())

                            if last_td is None or td < last_td:
                                last_td = td
                                index_ts += 1
                            else:
                                break

                        photo.pos = stream_obj.tracking.steps['coordinates'][index_ts]
                    except AttributeError:
                        pass
                    finally:
                        photo.save()

            except subprocess.CalledProcessError as e:
                out_bytes = e.output
                # Output generated before error
                code = e.returncode
                print("[ janus-pp-rec ] => ", out_bytes, code)
                print("[ janus-pp-rec ] => ", out_bytes.decode('utf-8'))


        print(json_data)
