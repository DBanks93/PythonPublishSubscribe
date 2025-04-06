# def test_create_subscription(app, capfd):
#     # Given
#     topic_name = "test_topic"
#     subscription_name = "test_subscription"
#
#     # When
#     subscription = app.create_subscription(subscription_name, topic_name)
#
#     # Then
#     # assert subscription.name == f"projects/test-project/subscriptions/{subscription_name}"
#     assert capfd.readouterr().out is '', "Expected no error/warnings"