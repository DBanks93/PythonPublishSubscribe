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
- [Database Connectivity](#database-connectivity)
  - [Connecting to a database](#connecting-to-a-database)
  - [Useful info on creating ORMs](#creating-orms)
  - [Info about the provided DatabaseHelper](#databasehelper)
- [Configuration](#pythonpublishsubscribe-config)
- [Useful functions](#useful-functions)

## Initialising the framework
In order to use the framework you must create an instance of `PythonPublishSubscribe`.
```python
app = PythonPublishSubscribe()

app = PythonPublishSubscribe(database_connectivity=True)
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

## Database Connectivity
PythonPublishSubscribe uses sqlalchemy as a way to connect to database.
To enable database connectivity, you must set `database_connectivity` to true when initialising the framework.
```python
app = PythonPublishSubscribe(database_connectivity=True)
```

The database support is handled via [sqlalchemy](https://www.sqlalchemy.org),
the PythonPublishSubscribe framework will automatically on initialisation connect to the database and set up an engine.
[Sessions](#sessions) are then created and passed through to callback functions when a message is received.

### Connecting to a database
If you've enabled database connectivity when the framework is initialised,
it will automatically attempt to connect to it using [sqlalchemy's database engine](https://docs.sqlalchemy.org/en/20/core/engines.html).
In order to connect to a database a URL is needed. 

You can simply create your own url, using the sqlalchemy docs on [generating urls](https://docs.sqlalchemy.org/en/20/core/engines.html#mysql),
and pass it into the config as `DATABASE_URL`.
Or if you wish, you can enter the following into the config and let the framework build the url for you:

| Name              | Required* | Default Value used in [DatabaseHelper](#databasehelper) | Meaning                                           |
|-------------------|-----------|---------------------------------------------------------|---------------------------------------------------|
| DATABASE_DIALECT  | ✅         | -                                                       | Dialect/Driver to use to connect to the database  |
| DATABASE_NAME     |           | default_schema                                          | Name of the Database to connect to                |
| DATABASE_USERNAME |           | appuser                                                 | Username to login to the database                 |
| DATABASE_PASSWORD |           |                                                         | Password to login to the database to (plain text) |
| DATABASE_HOST     |           | -                                                       | Database Host                                     |
| DATABASE_PORT     |           | -                                                       | Port to connect to the database                   |

*PythonSubscribe Requires the config, depending on dialect 
and other config values entered sqlalchemy may still require extra bits of config.

_Note: you may not need all the db config values, but check your database configuration.
Errors will be thrown if values are missing._


To make it easier, there are some [supported Dialects](#supported-shortened-dialects),
meaning you don't have enter the whole driver name.
If the shortened driver name is not available you can simply pass through the whole driver i.e.
```yaml
DATABASE_DIALECT='psycopg2'
# Yields the same results as...
DATABASE_DIALECT='postgresql+psycopg2'
```
You MUST make sure that you have the driver installed or else your program will throw an error.
For a full list of all dialicts supported see [the sqlalchemy docs](https://docs.sqlalchemy.org/en/20/dialects/index.html).

Once the url has be generated or gathered, this url is passed to sqlalchemy which will then connect to the database
using an engine, and you'll be good to go.
All of this happens when you initialise the framework.
#### Supported shortened dialects
| Supported DATABASE_DIALECT | Full driver         |
|----------------------------|---------------------|
| postgresql                 | postgresql          |
| psycopg2                   | postgresql+psycopg2 |
| pg8000                     | postgresql+pg8000   |
| mysql                      | mysql               |
| pymysql                    | mysql+pymysq        |


### Creating ORMs

```python
Base = declarative_base()
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)

# can be simplified to be...
class User(BaseModel, tablename="users"):
    name = Column(String(80), nullable=False)
```

### Sessions
[SQLAlchemy Sessions](https://docs.sqlalchemy.org/en/20/orm/session_basics.html) are provided by the framework and are automatically commited/rollback and closed after calling a given callback function.
In order to use the session, the signature of your callback sessions has to be changed slightly to accept a `Session` 
as well as the message:
```python
@app.subscribe("database_subscription")
def function(message, session: Session):
    ...
```
If the callback function raises an error or returns `False` then the session will automatically rolled back 
(simular to how message negatively acknowledgment works), 
otherwise it always commits the session.

If you wish to create a session you can simply call,
```python
from python_publish_subscribe.src.db.DatabaseHelper import DatabaseHelper

session: Session = DatabaseHelper().create_session()
```
This will create a sqlalchemy session based on the engine generated upon the initialisation.

### DatabaseHelper
The `DatabaseHelper` is a singleton class that contains helpful functions that can be used to interact with a given database.
It's created upon initialisation if the framework if `database_conecitivy` is enabled 
and stores all the needed SQLAlchemy objects needed to connect to a database.

You can use the helper to get objects that maybe useful such as the Engine, Sessions....

you can access the helper like so
```python
from python_publish_subscribe.src.db.DatabaseHelper import DatabaseHelper

DatabaseHelper()

# or for example
DatabaseHelper().get_engine()
```

## PythonPublishSubscribe Config
Config is handled by the `Config` class.
This can be accessed through the config attribute in PythonPublishSubscribe.
```python
app.config
```

Configuration is saved in a dictionary meaning you can access and set data
though calling the following methods: `config.update`, `config.set`, `config.get` and `config.add_value_to_key`.
These can be called at any point within your application.

### Passing in values
In order to pass through values to the config class upon the frameworks initialisation,
there are two main ways.

1. Using a .env file
2. Passing a dict in when creating a PythonPublishSubscribe instance.

### Config Attributes 
| Name                | Default Value  | Required | Format                                     | Meaning                                                                                             |
|---------------------|----------------|----------|--------------------------------------------|-----------------------------------------------------------------------------------------------------|
| PROJECT_ID          |                | ✅        | 'project'                                  | GCP Project to link to                                                                              |
| DEFAULT_TIMEOUT     | 10             |          |                                            | Default timeout for publishing - if not given will use Google's default value                       |
| PUBLISH_TOPICS      |                |          | {topic_name: topic}                        | Topics to publish to                                                                                |
| SUBSCRIPTION_TOPICS |                |          | {subscription_name: subscription_path}     | Map of subscription names to path - so you can use the subscription name rather than the whole path |
| DATABASE_URL        |                |          | [More Info](#connecting-to-a-database)     | Full URL of the database to connect to                                                              ||
| DATABASE_DIALECT    |                |          | [More Info](#supported-shortened-dialects) | Dialect/Driver to use to connect to the database                                                    |
| DATABASE_NAME       | default_schema |          | [More Info](#connecting-to-a-database)     | Name of the Database to connect to                                                                  |
| DATABASE_USERNAME   | appuser        |          | [More Info](#connecting-to-a-database)     | Username to login to the database                                                                   |
| DATABASE_PASSWORD   |                |          | [More Info](#connecting-to-a-database)     | Password to login to the database to (plain text)                                                   |
| DATABASE_HOST       |                |          | [More Info](#connecting-to-a-database)     | Database Host                                                                                       |
| DATABASE_PORT       |                |          | [More Info](#connecting-to-a-database)     | Port to connect to the database                                                                     |



## Full Example
The full example can be seen in the [example directory](./examples).
The example shows some of the approaches you can use, and is configured using a .env file.
_Note: The example was created using google's pub/sub emulator, you may need to change .env file to get your example working_

## Useful Functions

- `app.publisher.create_topic(<topic>)`: Creates a topic if it doesn't already exist.
- `app.create_subscription(<subscription_name>, <topic_name>)`: Creates a subscription for a topic if it doesn't already exist