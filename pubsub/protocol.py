from pubsub.serializers.serializer import JSONSerializer
from pubsub.validators.validator import ValidationError


class Protocol(object):
    """
    Protocol used to instantiate publisher/subscriber adapters with optional parameters(serializer, validator, filter)
    """

    def __init__(self, adapter, serializer=None, validator=None, filter=None):
        self.adapter = adapter
        self.serializer = serializer or JSONSerializer()
        self.validator = validator
        self.filter = filter

    def publish(self, topic, message, validation_error_callback=None):
        if self.validator:
            try:
                self.validator.validate_message(message)
            except ValidationError as exc:
                if validation_error_callback:
                    validation_error_callback(event=message, exception=exc, protocol=self)
                raise
        serialized = self.serializer.encode(message=message)
        self.adapter.publish(topic, serialized)

    def bulk_publish(self, topic, messages, validation_error_callback=None):
        if self.validator:
            for message in messages:
                try:
                    self.validator.validate_message(message)
                except ValidationError as exc:
                    if validation_error_callback:
                        validation_error_callback(event=message, exception=exc, protocol=self)
                    raise
        serialized = self.serializer.encode(message=dict(messages=messages))
        self.adapter.bulk_publish(topic, serialized)

    def subscribe(
            self, topic, callback, create_topic=False, exception_handler=lambda x, y: None, always_raise=True, *args, **kwargs):

        def deserializer_callback(message):
            try:
                deserialized = self.serializer.decode(message)
                callback(message, deserialized)
            except Exception as exc:
                exception_handler(message, exc)
                if always_raise:
                    raise exc
            self.adapter.ack(message)

        return self.adapter.subscribe(topic, callback=deserializer_callback, create_topic=create_topic, *args, **kwargs)

    def get_topics(self):
        return self.adapter.get_topics()

    def delete_topic(self, topic):
        self.adapter.delete_topic(topic)
