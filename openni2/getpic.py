from primesense import openni2
import gzip

openni2.initialize()
dev = openni2.Device.open_any()
depth_stream = dev.create_depth_stream()
depth_stream.start()
frame = depth_stream.read_frame()
frame_data = frame.get_buffer_as_uint16()
depth_stream.stop()
f = gzip.open("deph.bin.gz","wb")
f.write( frame_data )
f.close()

col = dev.create_color_stream()
col.start()
frame = col.read_frame()
print frame.width, frame.height
col.stop()
frame_data = frame.get_buffer_as_uint16()
f = gzip.open("pic.bin.gz","wb")
f.write( frame_data )
f.close()

