from python_publish_subscribe import PythonPublishSubscribe

### WON'T BE PART OF THE FRAMEWORK, ONLY DOING THIS FOR QUICK TESTING
import os

os.environ["PUBSUB_EMULATOR_HOST"] = "localhost:8085"

###############################
app = PythonPublishSubscribe()

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



if __name__ == "__main__":
    app.run()

# app.subscriber.subscribe('new_subscription', hello)

# app.config.update('PUBLISH_TOPICS', TOPIC_NAME)

# test()
#
# @app.test_decorators
# def test_function():
#     print("foo but with no bar :(")

# @app.test_decorator_with_params("foo")
# def test_param():
#     print("bar")
#
# @app.test_map_function("hello_subscription")
# def test_call_function():
#     print("callback")
#
# test_param()