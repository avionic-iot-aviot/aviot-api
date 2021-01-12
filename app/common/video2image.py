import os
import sys

"""
ffmpeg-python is a third-party library (wrapper for ffmpeg).
Install with:
	pip install ffmpeg-python

NOTE: also exist python-ffmpeg but is NOT the same.
"""
import ffmpeg


class InputError(Exception):
	""" Raised when the video doesn't exist """	
	pass


class OutputError(Exception):
	""" Raised when the output path already exist """
	pass


class TimestampError(Exception):
	""" Raised when the timestamps are inconsistent """	
	pass


def save_frame(video_path, start_time, frame_time, save_path):
	""" Extract a single frame at time 'frame_time' """

	# Video doesn't exists
	if not os.path.exists(video_path):
		print("[Video2Image] Error: Input file doesn't exist.")
		raise InputError

	# frame_time should be greater (or equal) than start_time
	if frame_time < start_time:
		print("[Video2Image] Error: frame_time should be greater (or equal) than start_time.")
		raise TimestampError

	# Save path already occupied
	if os.path.exists(save_path):
		print("[Video2Image] Error: Output file already exist.")
		raise OutputError

	# Elapsed time
	elapsed_s = (frame_time - start_time)

	# FFmpeg
	try:
		(
			ffmpeg
			.input(video_path, ss=elapsed_s)
			.output(save_path, vframes=1)
			.run(capture_stdout=True, capture_stderr=True)
		)
	except ffmpeg.Error as e:
		print("[Video2Image] FFmpeg error:", e.stderr.decode(), file=sys.stderr)

		# Done
		print("[Video2Image] Frame extracted with success!")

