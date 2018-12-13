class BaseAdapter(object):
    """
    PubSub adapter base class
    """

    def publish(self, channel, message):
        raise NotImplementedError('Not implemented')

    def bulk_publish(self, channel, messages):
        raise NotImplementedError('Not implemented')

    def get_topics(self):
        raise NotImplementedError('Not implemented')

    def subscribe(self, channel, callback, create_topic=False):
        raise NotImplementedError('Not implemented')

    def delete_topic(self, topic):
        raise NotImplementedError('Not implemented')

    def ack(self, message):
        pass
