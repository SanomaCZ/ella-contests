from django.test.client import RequestFactory

from nose import tools

from .cases import ContestTestCase


class TestContestUrls(ContestTestCase):
    def setUp(self):
        super(TestContestUrls, self).setUp()
        self.rf = RequestFactory()
        self.url = self.contest.get_absolute_url()

    def test_unregistered_custom_url(self):
        response = self.client.get(self.url + 'results/')
        tools.assert_equals(404, response.status_code)
        response = self.client.get(self.url + 'question/a/')
        tools.assert_equals(404, response.status_code)

    def test_custom_url_for_questions_wizard(self):
        response = self.client.get(self.url + 'question/1/')
        tools.assert_equals(200, response.status_code)

    def test_detail_url_for_contest(self):
        response = self.client.get(self.url)
        tools.assert_equals(200, response.status_code)
