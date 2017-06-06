import zmq
import threading
import config
import calendar
import time
import pickle
import logging
from . Message import Message

module_logger = logging.getLogger('Messaging')


class BaseMessaging(threading.Thread):

    def __init__(self, up, down, heartbeat_enable):
        threading.Thread.__init__(self)
        self.is_running = True
        self.handlers = {}
        self.up = up
        self.down = down
        self.last_up = 0
        self.last_down = calendar.timegm(time.gmtime())
        self.last_retry = calendar.timegm(time.gmtime())
        self.retry_cnt = 0
        self.heartbeat_enable = heartbeat_enable

    def run(self):
        if self.down is not None:
            module_logger.info('started')
            while self.is_running:
                events = self.down.poll(timeout=1.0)
                if events == zmq.POLLIN:
                    msg = self.wait()
                    if Message.verify(msg):
                        self.last_down = calendar.timegm(time.gmtime())
                        self.retry_cnt = 0
                        if msg['id'] == Message.Heartbeat:
                            continue
                        if msg['id'] in self.handlers:
                            module_logger.info('%s' % Message.msg_info(msg))
                            self.handlers[msg['id']](msg)
                        else:
                            module_logger.info('no handler found for frame %i' % (msg['id']))
                        if '*' in self.handlers:
                            self.handlers['*'](msg)

                curr_time = calendar.timegm(time.gmtime())

                # send heartbeat to uplink
                if self.last_up + 10 < curr_time:
                    self.send(Message.msg_heartbeat())

                # check received heartbeat status
                if self.heartbeat_enable and self.last_down + 300 < curr_time and self.last_retry + min(self.retry_cnt, 10) * 60 < curr_time:
                    time_since_msg = curr_time - self.last_down
                    time_since_retry = curr_time - self.last_retry
                    module_logger.info('reconnect attempt %u. last msg %u s ago, last retry %s s ago' % (self.retry_cnt, time_since_msg, time_since_retry))
                    self.down.disconnect(self.down.LAST_ENDPOINT)
                    self.down.connect(self.down.LAST_ENDPOINT)
                    self.last_retry = curr_time
                    self.retry_cnt += 1

            self.down.close()
            module_logger.info('stopped')
        else:
            module_logger.info('no downlink socket given. not starting receive thread')

    def wait(self):
        try:
            return self.down.recv_pyobj()
        except pickle.UnpicklingError as e:
            module_logger.info('Error: UnpicklingError')
            return None
        except (AttributeError, EOFError, ImportError, IndexError) as e:
            module_logger.info('Error: Other')
            return None
        except Exception as e:
            return None

    def send(self, msg):
        if self.up is not None:
            try:
                self.last_up = calendar.timegm(time.gmtime())
                return self.up.send_pyobj(msg, protocol=2)
            except zmq.ZMQError:
                module_logger.info('Error: unable to send msg')
                return None
        else:
            module_logger.info('no uplink socket given. unable to send message')

    def install(self, frame, handler):
        self.handlers[frame] = handler

    def stop(self):
        self.is_running = False
        if self.up is not None:
            self.up.close()


class ServerMessaging(BaseMessaging):

    def __init__(self):
        self.context = zmq.Context()
        incoming = "tcp://*:%i" % config.upload_port
        outgoing = "tcp://*:%i" % config.msg_port

        downlink = self.context.socket(zmq.PULL)
        downlink.bind(incoming)
        downlink.setsockopt(zmq.RCVTIMEO, 1000)

        uplink = self.context.socket(zmq.PUB)
        uplink.bind(outgoing)

        module_logger.info('listening to incoming %s, outgoing %s (Server)' % (incoming, outgoing))
        super(ServerMessaging, self).__init__(uplink, downlink, False)


class ClientMessaging(BaseMessaging):

    def __init__(self):
        self.context = zmq.Context()
        outgoing = "tcp://%s:%i" % (config.upload_ip, config.upload_port)
        incoming = "tcp://%s:%i" % (config.upload_ip, config.msg_port)

        uplink = self.context.socket(zmq.PUSH)
        uplink.connect(outgoing)

        downlink = self.context.socket(zmq.SUB)
        downlink.connect(incoming)
        downlink.setsockopt(zmq.SUBSCRIBE, b'')
        downlink.setsockopt(zmq.RCVTIMEO, 1000)

        module_logger.info('connecting to outgoing %s, incoming %s (Client)' % (outgoing, incoming))
        super(ClientMessaging, self).__init__(uplink, downlink, True)


class LocalServerMessaging(BaseMessaging):

    def __init__(self):
        self.context = zmq.Context()
        outgoing = "tcp://127.0.0.1:9996"
        incoming = "tcp://127.0.0.1:9997"

        # forwards messages locally from the cameras
        uplink = self.context.socket(zmq.PUB)
        uplink.bind(outgoing)

        # forwards messages locally to the cameras
        downlink = self.context.socket(zmq.PULL)
        downlink.bind(incoming)
        downlink.setsockopt(zmq.RCVTIMEO, 1000)

        # module_logger.info('listening to %s (LocalServer)' % incoming)
        super(LocalServerMessaging, self).__init__(uplink, downlink, False)


class LocalClientMessaging(BaseMessaging):

    def __init__(self):
        self.context = zmq.Context()
        incoming = "tcp://127.0.0.1:9996"
        outgoing = "tcp://127.0.0.1:9997"

        # incoming messages from the cameras
        downlink = self.context.socket(zmq.SUB)
        downlink.connect(incoming)
        downlink.setsockopt(zmq.SUBSCRIBE, b'')
        downlink.setsockopt(zmq.RCVTIMEO, 1000)

        # incoming messages from the cameras
        uplink = self.context.socket(zmq.PUSH)
        uplink.connect(outgoing)

        # module_logger.info('connecting to %s (LocalClient)' % outgoing)
        super(LocalClientMessaging, self).__init__(uplink, downlink, False)
