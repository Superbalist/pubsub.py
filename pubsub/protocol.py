import logging
import threading
import time
from datetime import datetime

from pubsub.serializers.serializer import JSONSerializer


class Protocol:
    """
    Protocol used to instantiate publisher/subscriber adapters with optional parameters(serializer, validator, filter)
    """

    def __init__(self, adapter, serializer=None, validator=None, filter=None):
        self.adapter = adapter
        self.serializer = serializer or JSONSerializer()
        self.validator = validator
        self.filter = filter

    def publish(self, topic, message):
        self.validator.validate_message(message)
        serialized = self.serializer.encode(message=message)
        self.adapter.publish(topic, serialized)

    def subscribe(self, topic, callback=None, exception_handler=lambda x, y: None, always_raise=True):
        # It is probably saner to just require a callback
        if callback is None:
            def callback(message, data):
                print('Received message: {}'.format(data))
                message.ack()

        lock = threading.Lock()
        global last_message
        last_message = None
        global time_since_last
        time_since_last = 0

        def deserializer_callback(message):
            with lock:
                global last_message
                if last_message is None:
                    last_message = datetime.utcnow()
                else:
                    now = datetime.utcnow()
                    global time_since_last
                    time_since_last = now - last_message
                    last_message = now

            try:
                deserialized = self.serializer.decode(message)
                callback(message, deserialized)
            except Exception as exc:
                exception_handler(message, exc)
                if always_raise:
                    raise exc

        self.adapter.subscribe(topic, callback=deserializer_callback)

        # The subscriber is non-blocking, so we must keep the main thread from
        # exiting to allow it to process messages in the background.
        while True:
            time.sleep(60)
            if time_since_last.seconds > 300:
                logging.critical("It's been a while since we saw a message. Subscribing thread might be dead.")
                break
