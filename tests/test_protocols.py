# -*- coding: utf-8 -*-
import threading
from collections import defaultdict, deque
from datetime import datetime
from socket import gethostname
from time import sleep
from unittest import TestCase
from uuid import uuid4

from google.cloud.pubsub_v1 import futures
from jsonschema import ValidationError as SchemaValidationError

from pubsub.adapters.base import BaseAdapter
from pubsub.adapters.exceptions import TopicNotFound
from pubsub.protocol import Protocol
from pubsub.serializers.serializer import JSONSerializer
from pubsub.validators.validator import SchemaValidator, ValidationError


class MockGoogleAdapter(BaseAdapter):
    """
    PubSub adapter base class
    """

    def __init__(self, client_identifier, topics=None):
        self.client_id = client_identifier
        self.topics = topics or []
        self._messages = {topic: deque() for topic in self.topics}

    def clear_messages(self):
        self._messages = defaultdict(deque)

    def get_topics(self):
        return self.topics

    def delete_topic(self, topic):
        raise NotImplementedError('Not implemented')

    def publish(self, channel, message, create_topic=True):
        if create_topic and (channel not in self._messages):
            self._messages[channel] = deque()
        self._messages[channel].appendleft(message)

    def bulk_publish(self, channel, messages, create_topic=True):
        for message in messages:
            self.publish(channel, message, create_topic)

    def subscribe(self, channel, callback, create_topic=False):
        class MockMessage(object):
            def __init__(self, message):
                self.data = message

        if channel not in self._messages:
            if create_topic:
                self._messages[channel] = deque()
            else:
                raise TopicNotFound("Topic {} doesn't exist".format(channel))

        future = futures.Future()

        def create_message():
            sleep(0.1)
            while self._messages[channel]:
                r = MockMessage(self._messages[channel].pop())
                try:
                    return callback(r)
                except Exception as exc:
                    future.set_exception(exc)

        thread = threading.Thread(target=create_message)
        thread.start()
        return future


class DoneException(Exception):
    pass


class ProtocolTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid_message = {
            u'meta': {
                u'date': u'2017-02-01T12:39:12+00:00',
                u'hostname': u'superbalist-api-1935885982-59xk1',
                u'service': u'api',
                u'uuid': u'5AB2ABB6-8617-4DDA-81F7-DD47D5882B19'
            },
            u'schema': u'http://schema.superbalist.com/events/shopping_cart/created/1.0.json',
            u'shopping_cart': {
                u'id': 1070486,
                u'is_expired': False,
                u'is_restorable': True,
                u'items': [],
                u'user': {
                    u'email': u'matthew@superbalist.com',
                    u'first_name': u'Matthew',
                    u'id': 2,
                    u'last_name': u'G\u0151slett'
                }
            }
        }
        cls.invalid_message = {'blah': 'blah'}

    def test_valid_message(self):
        protocol = Protocol(
            adapter=MockGoogleAdapter('test-client'),
            serializer=JSONSerializer(),
            validator=SchemaValidator())
        protocol.publish('python_test', self.valid_message)

        def callback(message, data):
            assert data == self.valid_message
            raise DoneException()

        future = protocol.subscribe('python_test', callback=callback)
        with self.assertRaises(DoneException):
            future.result(timeout=1)

    def test_missing_topic(self):
        protocol = Protocol(
            adapter=MockGoogleAdapter('test-client'),
            serializer=JSONSerializer(),
            validator=SchemaValidator())

        def callback(message, data):
            assert data == self.valid_message
            raise DoneException()

        with self.assertRaises(TopicNotFound):
            future = protocol.subscribe('python_test', callback=callback)
            future.result(timeout=1)

    def test_create_missing_topic(self):
        protocol = Protocol(
            adapter=MockGoogleAdapter('test-client'),
            serializer=JSONSerializer(),
            validator=SchemaValidator())

        def callback(message, data):
            assert data == self.valid_message
            raise DoneException()

        with self.assertRaises(futures.exceptions.TimeoutError):
            future = protocol.subscribe('python_test', callback=callback, create_topic=True)
            future.result(timeout=0.01)

    def test_invalid_message(self):
        protocol = Protocol(
            adapter=MockGoogleAdapter('test-client'),
            serializer=JSONSerializer(),
            validator=SchemaValidator())
        with self.assertRaises(SchemaValidationError):
            protocol.publish('python_test', self.invalid_message)

    # Only have one of these just to test its actually working
    # def test_real_google(self):
    #     protocol = Protocol(adapter=GooglePubsub(client_identifier='test_'), serializer=JSONSerializer(),
    #                         validator=SchemaValidator())
    #     protocol.publish('python_test', self.valid)
    #     sub = protocol.subscribe('python_test')
    #     for message in sub:
    #         assert message == self.valid


class TestValidationErrorPublisher(TestCase):
    @classmethod
    def setUp(cls):
        cls.valid_message = {
            'schema': 'https://raw.githubusercontent.com/Superbalist/python-pubsub/gh-pages/examples/schema/card.json',
            'familyName': 'foo',
            'givenName': 'bar',
        }
        cls.invalid_message = {
            'schema': 'https://raw.githubusercontent.com/Superbalist/python-pubsub/gh-pages/examples/schema/card.json',
            'givenName': 'baz',
        }
        cls.protocol = Protocol(
            adapter=MockGoogleAdapter('test-client'),
            serializer=JSONSerializer(),
            validator=SchemaValidator())

    def tearDown(self):
        self.protocol.adapter.clear_messages()

    def test_publish_error_defaults_to_false(self):
        with self.assertRaises(ValidationError):
            self.protocol.publish('python_test', self.invalid_message)

    def test_invalid_message(self):
        topic = 'validation_error'
        schema = 'https://raw.githubusercontent.com/Superbalist/python-pubsub/gh-pages/examples/schema/validation-error.json'

        def validation_error_callback(event, exception, protocol):
            message = {
                'meta': {
                    'date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'hostname': gethostname(),
                    'service': 'example-app',
                    'uuid': str(uuid4())
                },
                'schema': schema
            }
            message.update(event=event, errors=[err.message for err in exception.errors])
            protocol.publish(topic, message)

        def callback(message, data):
            raise DoneException

        with self.assertRaises(ValidationError):
            self.protocol.publish('python_test', self.invalid_message, validation_error_callback)

        future = self.protocol.subscribe('validation_error', callback=callback)
        with self.assertRaises(DoneException):
            future.result(timeout=1)

    def test_invalid_validation_error_message(self):
        topic = 'validation_error'
        schema = 'https://raw.githubusercontent.com/Superbalist/python-pubsub/gh-pages/examples/schema/validation-error.json'

        def validation_error_callback(event, exception, protocol):
            message = {
                'meta': {
                    'date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'hostname': gethostname(),
                    'service': 'example-app',
                    'uuid': str(uuid4())
                },
                'schema': schema,
                'errors': [err.message for err in exception.errors]
            }
            protocol.publish(topic, message)

        with self.assertRaises(ValidationError):
            self.protocol.publish('python_test', self.invalid_message, validation_error_callback)
