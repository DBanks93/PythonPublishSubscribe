import random

from python_publish_subscribe import PythonPublishSubscribe

### WON'T BE PART OF THE FRAMEWORK, ONLY DOING THIS FOR QUICK TESTING
import os

os.environ["PUBSUB_EMULATOR_HOST"] = "localhost:8085"

###############################
app = PythonPublishSubscribe(database_connectivity=True)

app.create_topic('new_topic') # Will produce a warning if topic already exists
app.publisher.publish('new_topic', "Hello")

future = app.publisher.publish('new_topic', "Hello", asynchronous=True)
# Doing other stuff
future.result()

results = app.publisher.publish_batch('new_topic', ["Wow", "multiple messages", "can be sent!"])

@app.publish('new_topic')
def send_hello(name):
    return f"Hello {name}!"

send_hello("Swansea")


### Subscribing ###

# Will produce a warning if subscription already exists
app.create_subscription('new_subscription', 'new_topic')

@app.subscribe("new_subscription")
def hello(message):
    print(message.data)

app.create_topic('new_topic2') # Will produce a warning if topic already exists
app.publisher.publish('new_topic2', "Hello2")
# app.create_subscription('new_subscription2', 'new_topic2')

# Will produce a warning if subscription already exists
@app.subscribe("new_subscription2", topic_name="new_topic2")
def hello2(message):
    print(message.data)

# app.subscriber.add_subscription("new_subscription", hello)


### Database Handling ###
from python_publish_subscribe.src.db.DatabaseHelper import DatabaseHelper
from sqlalchemy.orm import Session
from sqlalchemy import Column, String

from python_publish_subscribe.src.db.ORMUtility import orm_model, get_base
from python_publish_subscribe.src.db.BaseModel import BaseModel


# Creating a User model using the Base Model
class User(BaseModel, tablename="users"):
    name = Column(String(80), nullable=False)


# Using the engine created by the framework
DatabaseHelper.drop_all()
DatabaseHelper.create_all()

app.create_topic('database_topic') # Will produce a warning if topic already exists

# Getting the session passed through automatically.
@app.subscribe("database_subscription2", topic_name="database_topic")
def database_call(message, session: Session):
    session.add(User(name=message.data))
    print("Added user", message.data)
    all_users = ", ".join(f"{user.id}:{user.name}" for user in session.query(User).all())
    print(all_users)

app.publisher.publish('database_topic', "User" + str(random.randint(1,100)))



if __name__ == "__main__":
    app.run()
