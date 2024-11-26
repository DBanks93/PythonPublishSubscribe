from python_publish_subscribe import PythonPublishSubscribe, test

### WON'T BE PART OF THE FRAMEWORK, ONLY DOING THIS FOR QUICK TESTING
from google.cloud import pubsub_v1

PROJECT_ID = 'test-project-id'
TOPIC_NAME = 'projects/{project_id}/topics/{topic}'.format(
    project_id=PROJECT_ID,
    topic='test-topic',  # Set this to something appropriate.
)

publisher = pubsub_v1.PublisherClient()

try:
    publisher.create_topic(name=TOPIC_NAME)
    print(f"Topic '{TOPIC_NAME}' created in emulator.")
except Exception as e:
    print(f"Topic '{TOPIC_NAME}' already exists: {e}")

###############################
app = PythonPublishSubscribe()
app.run()
app.test_run()

app.config.update('PUBLISH_TOPICS', TOPIC_NAME)

test()

@app.test_decorators
def test_function():
    print("foo but with no bar :(")

@app.test_decorator_with_params("foo")
def test_param():
    print("bar")

@app.test_map_function("hello_subscription")
def test_call_function():
    print("callback")

test_param()