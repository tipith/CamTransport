import zmq
import cam_config


class MessageSubscriber(object):

    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.bind("tcp://*:%s" % cam_config.upload_port)
        self.socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.socket.setsockopt(zmq.RCVTIMEO, 1000)

    def wait_for_pub(self):
        try:
            return self.socket.recv_pyobj()
        except zmq.ZMQError:
            return None

    def close(self):
        self.socket.close()
