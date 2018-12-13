import functools
import logging

from requests import Session
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import pubsub_v1
from grpc import StatusCode

from pubsub.adapters.base import BaseAdapter
from pubsub.adapters.exceptions import IdentifierRequiredException, TopicNotFound, SubscriptionNotFound

log = logging.getLogger('pubsub')


class GooglePubsub(BaseAdapter):
    """
    Google-cloud adapter class
    """

    def __init__(self, project_id, client_identifier='default', pubsub_rest_proxy=None):
        if pubsub_rest_proxy:
            self.pubsub_rest_proxy = pubsub_rest_proxy
            self.session = Session()
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        self.client_identifier = client_identifier
        self.project_id = project_id

    def ack(self, message):
        message.ack()

    def publish(self, topic_name, message):
        if self.pubsub_rest_proxy:
            log.warning("PubSub Rest Proxy configured but not used by `publish()`. Rather use faster `bulk_publish()`")
        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        self.get_topic(topic_path)
        self.publisher.publish(topic_path, message)

    def bulk_publish(self, topic_name, messages):
        if not self.pubsub_rest_proxy:
            raise NotImplementedError('`bulk_publish()` not possible without a PubSub Rest Proxy')
        response = self.session.post('{}/messages/{}'.format(self.pubsub_rest_proxy, topic_name), json=messages)
        response.raise_for_status()
        return response.json()

    def subscribe(self, topic_name, callback, create_topic=False):
        # This makes sure the subscription exists
        self.get_subscription(topic_name, create_topic)

        subscription_path = self.subscriber.subscription_path(
            self.project_id, '{}.{}'.format(self.client_identifier, topic_name))

        log.info('Starting to listen on: %s', subscription_path)
        policy = self.subscriber.subscribe(subscription_path)
        return policy.open(callback=callback)

    def get_subscription(self, topic_name, create_topic=False):
        if not self.client_identifier:
            raise IdentifierRequiredException("Use obj.set_client_identifier('name')")

        subscription_path = self.subscriber.subscription_path(self.project_id, '{}.{}'.format(
            self.client_identifier, topic_name))
        try:
            return self.subscriber.get_subscription(subscription_path)
        except GoogleAPICallError as exc:
            if exc.grpc_status_code != StatusCode.NOT_FOUND:
                raise

        topic_path = self.subscriber.topic_path(self.project_id, topic_name)
        try:
            return self.subscriber.create_subscription(subscription_path, topic_path)
        except GoogleAPICallError as exc:
            if exc.grpc_status_code != StatusCode.NOT_FOUND:
                raise
            if not create_topic:
                raise TopicNotFound("Can't subscribe to unknown topic: {}".format(topic_name))
            self.publisher.create_topic(topic_path)

    def delete_topic(self, topic_name):
        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        try:
            self.publisher.delete_topic(topic_path)
        except GoogleAPICallError as exc:
            if exc.grpc_status_code != StatusCode.NOT_FOUND:
                raise
            raise TopicNotFound("Can't delete unknown topic: {}".format(topic_path))

    def delete_subscription(self, topic_name):
        subscription_path = self.subscriber.subscription_path(
            self.project_id, '{}.{}'.format(self.client_identifier, topic_name))
        try:
            self.subscriber.delete_subscription(subscription_path)
        except GoogleAPICallError as exc:
            if exc.grpc_status_code != StatusCode.NOT_FOUND:
                raise
            raise SubscriptionNotFound("Can't delete unknown subscription: {}".format(subscription_path))

    def get_topics(self):
        project_path = self.publisher.project_path(self.project_id)
        return self.publisher.list_topics(project_path)

    @functools.lru_cache(maxsize=128)
    def get_topic(self, topic_path):
        try:
            return self.publisher.get_topic(topic_path)
        except GoogleAPICallError as exc:
            if exc.grpc_status_code != StatusCode.NOT_FOUND:
                raise
            return self.publisher.create_topic(topic_path)
