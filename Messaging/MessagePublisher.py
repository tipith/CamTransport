import zmq
import cam_config


class MessagePublisher(object):

    def __init__(self):
        self.context = zmq.Context()
        self.pub = self.context.socket(zmq.PUSH)
        self.pub.connect("tcp://%s:%i" % (cam_config.upload_ip, cam_config.upload_port))

    def publish(self, msg):
        self.pub.send_pyobj(msg, protocol=2)

    def close(self):
        self.pub.close()
