from unittest import TestCase

from app.common.decorators.retry_with_backoff_decorator import retry_with_backoff


class RetryWithBackoffTestCase(TestCase):
    def test_retry_with_backoff(self):
        random_value = {"some_key": 5}

        class TestRetry:
            def __init__(self):
                self.call_count = 0

            @retry_with_backoff(
                retries=3, backoff_in_secs=1, fail_open=False, test_mode=True
            )
            def do_work(self):
                try:
                    self.call_count += 1
                    if random_value["non_existent_key"]:
                        raise "This code should not be hit"
                except KeyError:
                    raise

        retry_class_object = TestRetry()
        self.assertRaises(KeyError, retry_class_object.do_work)
        self.assertEqual(retry_class_object.call_count, 3)
