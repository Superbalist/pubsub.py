# pubsub.py

A python abstraction for various pubsub providers.

[![Author](http://img.shields.io/badge/author-@superbalist-blue.svg?style=flat-square)](https://twitter.com/superbalist)
[![PyPI](https://img.shields.io/pypi/v/pubsub.py.svg?style=flat-square)](https://pypi.python.org/pypi/pubsub.py)
[![Github All Releases](https://img.shields.io/github/downloads/superbalist/pubsub.py/total.svg?style=flat-square)](https://github.com/Superbalist/pubsub.py)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg?style=flat-square)](https://github.com/Superbalist/pubsub.py)

## Adapters

* GoogleCloudAdapter - Working

## Installation

```bash
pip install pubsub.py
```

## Usage

* Import the Protocol and any sub-modules you may require
* Instantiate a Protocol object that that takes the following parameters
  * adapter(Required)
  * serializer
  * validator
  * filter
* Use the Protocol to subscribe or publish.

```python
from pubsub.protocol import Protocol
from pubsub.adapters.googlecloud import GooglePubsub


protocol = Protocol(
    adapter=GooglePubsub("GOOGLE_PROJECT_IDENTIFIER", client_identifier="CLIENT_IDENTIFIER"))
```

#### PubSub Rest Proxy

The GooglePubSub Adapter can optionally make use of a [PubSub Rest Proxy](https://github.com/Superbalist/js-pubsub-rest-proxy) which allows
for faster publishing as messages are dispatched in bulk and published by the proxy.

```python
from pubsub.protocol import Protocol
from pubsub.adapters.googlecloud import GooglePubsub


protocol = Protocol(
    adapter=GooglePubsub("GOOGLE_PROJECT_IDENTIFIER", client_identifier="CLIENT_IDENTIFIER", pubsub_rest_proxy="http://127.0.0.1:3000"))
```

### Subscribe to a topic

```python
# Create a callback handler method
def callback(message, data):
    print(data)

future = protocol.subscribe(topic='topic_name', callback=callback)

try:
    future.result()
except Exception as e:
    print(e)
```

And set an optional `exception_handler`:

```python
# If you want to capture exceptions, you can create an optional exception handler, like one that uses Sentry

from raven import Client

sentry_client = Client()
def exception_handler(message, exc):
    sentry_client.captureException()

# If you use `always_raise=True` exceptions will be handed to `exception_handler` and then cause messages to remain unack'd
# If you use `always_raise=False` exceptions will be handed to `exception_handler` and you can choose to re-raise or ignore and ack messages

future = protocol.subscribe(topic='topic_name', callback=callback, exception_handler=exception_handler, always_raise=False)
```

### Publish a message to topic

```python
protocol.publish('topic_name', message)
```

When using a PubSub rest proxy you can make use of the faster `bulk_publish` method
```python
protocol.bulk_publish('topic_name', [message])
```

`protocol.publish` and `protocol.bulk_publish` also support a custom `validation_error_callback`:

```python
from datetime import datetime
from socket import gethostname


def validation_error_callback(invalid_message, exception, protocol):
    message = {
        'meta': {
            'date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'hostname': gethostname(),
            'service': 'example-app',
        },
        'message': invalid_message,
        'errors': [err.message for err in exception.errors]
    }
    protocol.publish('invalid-messages', message)

protocol.publish(topic, example_message, validation_error_callback)
protocol.bulk_publish(topic, [example_message], validation_error_callback)
```

## Tests

The tests currently use a MockGooglePubsub adapter to test code functionality rather than GooglePubsub connection.
