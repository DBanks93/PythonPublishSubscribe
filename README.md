# PythonPublishSubscribe

This is a framework designed to handle Publish Subscribe interactions.



Currently, it only supports Google Pub/Sub Messaging Broker, however,
there might be plans to support other message brokers
such as RabbitMQ, Redis and AWS' Pub/Sub.

## Initialising the framework
In order to use the framework you must create an instance of `PythonPublishSubscribe`.
```python
app = PythonPublishSubscribe()
```

Your GCP project MUST be specified somewhere other wise the framework won't know where to publish/subscribe!
The easiest way to do this is by adding the following to your .env file, which is loaded when the framework is initalised:
```
PROJECT_ID = '<project>'
```

However you can also achieve the same by setting it in [PythonPublishSubscribe's Config](#pythonpublishsubscribe-config) when it's initialised:
```python
app = PythonPublishSubscribe({'PROJECT_ID': '<project>'})
```

## Publishing
### Simple Function
The most basic way to publish messages is to call the publish function.
```python
app.publisher.publish('<topic>', '<message/data>')
```

| Attribute Name | Required | Data Type                   |
|----------------|----------|-----------------------------|
| topic_name     | ✅        | str                         |
| data           | ✅        | Any                         |
| attributes     | ❌        | Dict                        |
| timeout        | ❌        | int                         |
| retry          | ❌        | google.api_core.retry.Retry |
| asynchronous   | ❌        | bool                        |

### Decorator
You can also use a decorator on a function to use the return value of your function as the message data:
```python
@app.publish('<topic>')
def function(args):
    return "foo" + args

# Call the function later on
function("bar")
```

### Batching/Mass message sending
Multiple messages can be handled at once.

_Note: All messages will be sent to one topic and can't be sent to individual ones_

```python
app.publisher.publish_batch('<topic>', [])
```
| Attribute Name | Required | Data Type                   |
|----------------|----------|-----------------------------|
| topic_name     | ✅        | str                         |
| messages       | ✅        | List[Any]                   |
| attributes     | ❌        | Dict                        |
| timeout        | ❌        | int                         |
| retry          | ❌        | google.api_core.retry.Retry |


## Subscribing

## PythonPublishSubscribe Config
Config is handled by the `Config` class.
This can be accessed through the config attribute in PythonPublishSubscribe.
```python
app.config
```

Configuration is saved in a dictionary meaning you can access and set data
though calling the following methods: `config.update`, `config.set`, `config.get` and `config.add_value_to_key`.
These can be called at anypoint within your application.

### Config Attributes

| Name            | Default Value | Required | Format              | Meaning                                                                       |
|-----------------|---------------|----------|---------------------|-------------------------------------------------------------------------------|
| PROJECT_ID      |               | ✅        | 'Topic'             | GCP Project to link to                                                        |
| DEFAULT_TIMEOUT |               |          |                     | Default timeout for publishing - if not given will use Google's default value |
| PUBLISH_TOPICS  |               |          | {topic_name: topic} | Topics to publish to                                                          |
|                 |               |          |                     |                                                                               |
|                 |               |          |                     |                                                                               |
|                 |               |          |                     |                                                                               |
|                 |               |          |                     |                                                                               |
|                 |               |          |                     |                                                                               |


## Full Example

## Useful Functions

- `app.publisher.create_topic('<topic>')`: Creates a topic if it doesn't already exist.