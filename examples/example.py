from python_publish_subscribe import PythonPublishSubscribe, test

### WON'T BE PART OF THE FRAMEWORK, ONLY DOING THIS FOR QUICK TESTING
import os

os.environ["PUBSUB_EMULATOR_HOST"] = "localhost:8085"

###############################
app = PythonPublishSubscribe()

app.publisher.create_topic('new_topic')
app.publisher.publish('new_topic', "Hello")

future = app.publisher.publish('new_topic', "Hello", asynchronous=True)
# Doing other stuff
future.result()

app.publisher.publish_batch('new_topic', ["Wow", "multiple messages", "can be sent!"])

@app.publish('new_topic')
def send_hello(name):
    return f"Hello {name}!"

send_hello("Swansea")

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