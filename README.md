# PythonPublishSubscribe

This is a framework designed to handle Publish Subscribe interactions.



Currently, it only supports Google Pub/Sub Messaging Broker, however,
there might be plans to support other message brokers
such as RabbitMQ, Redis and AWS' Pub/Sub.

## Table of contents:
- [Initialising](#initialising-the-framework)
- [Publishing](#publishing)
- [Subscribing](#subscribing)
  - [Configuring Callbacks and subscriptions](#configuring-callbacks-and-subscriptions)
  - [Listening for messages](#start-listening-to-subscriptions)
- [Configuration](#pythonpublishsubscribe-config)
- [Useful functions](#useful-functions)

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
The framework handles subscriptions in two parts;
- [Configuring Callbacks and subscriptions](#configuring-callbacks-and-subscriptions)
- [Listening for messages](#start-listening-to-subscriptions)

### Configuring Callbacks and subscriptions
In order to subscribe to messages, you need to create a callback function 
which takes in an instance of Google's Pub/Sub Message class.

You do not have to worry about message acknowledgment/negatively acknowledgment this is handled by the framework.
The framework will automatically ack the message unless any errors are thrown in which case the message is nacked.

#### Decorator
You can use a decorator to define the endpoint/callback function for a subscription.
In the decorator you must pass through the name of a subscription, with the name being either the full path,
or just the name of the subscription.
__(the subscription must already been created for a topic)__.

```python
@app.subscribe(<subscription_name>)
def function(message):
    ...
```

If you want to create a subscription for a topic as well subscribing to it, you can pass through the topic name:
```python
@app.subscribe(<subscription_name>, topic_name=<topic_name>)
def function(message):
    ...
```
This is the same as calling `app.create_subscription(<subscription_name>, <topic_name>)` and then subscribing.
It will try and create the subscription in GCP Pub/Sub weather it exists or not, so a warning will be printed if this is the case.

#### Simple function call
If you wish you can just simply call the `add_subscription` function
and pass through the subscription name and callback function:

```python
def function(message):
    ...

app.subscriber.add_subscription(<subscription_name>, function)
```

### Start listening to subscriptions
Now that all the callbacks have been configured for each subscription,
the framework must be started so that it can listen to them concurrently:

```python
if __name__ == "__main__":
    app.run()
```

Without running `app.main()` you won't be able to start listening.

Each subscription is listened to asynchronously, 
but something to note is that currently, if your callback function is intensive,
it could block other subscriptions on that topic until it's complete.

## PythonPublishSubscribe Config
Config is handled by the `Config` class.
This can be accessed through the config attribute in PythonPublishSubscribe.
```python
app.config
```

Configuration is saved in a dictionary meaning you can access and set data
though calling the following methods: `config.update`, `config.set`, `config.get` and `config.add_value_to_key`.
These can be called at any point within your application.

### Config Attributes

| Name                | Default Value | Required | Format                                 | Meaning                                                                                             |
|---------------------|---------------|----------|----------------------------------------|-----------------------------------------------------------------------------------------------------|
| PROJECT_ID          |               | ✅        | 'project'                              | GCP Project to link to                                                                              |
| DEFAULT_TIMEOUT     |               |          |                                        | Default timeout for publishing - if not given will use Google's default value                       |
| PUBLISH_TOPICS      |               |          | {topic_name: topic}                    | Topics to publish to                                                                                |
| SUBSCRIPTION_TOPICS |               |          | {subscription_name: subscription_path} | Map of subscription names to path - so you can use the subscription name rather than the whole path |



## Full Example
The full example can be seen in the [example directory](./examples).
The example shows some of the approaches you can use, and is configured using a .env file.
_Note: The example was created using google's pub/sub emulator, you may need to change .env file to get your example working_

## Useful Functions

- `app.publisher.create_topic(<topic>)`: Creates a topic if it doesn't already exist.
- `app.create_subscription(<subscription_name>, <topic_name>)`: Creates a subscription for a topic if it doesn't already exist