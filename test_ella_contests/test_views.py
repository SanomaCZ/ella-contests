from django.test.client import RequestFactory

from nose import tools

from .cases import ContestTestCase


class TestContestUrls(ContestTestCase):
    def setUp(self):
        super(TestContestUrls, self).setUp()
        self.rf = RequestFactory()
        self.url = self.contest.get_absolute_url()
        self.contest2_url = self.contest_question_less.get_absolute_url()

    def test_unregistered_custom_url(self):
        response = self.client.get(self.url + 'results/')
        tools.assert_equals(404, response.status_code)
        response = self.client.get(self.url + 'question/a/')
        tools.assert_equals(404, response.status_code)

    def test_custom_url_for_questions_wizard(self):
        response = self.client.get(self.url + 'question/1/')
        tools.assert_equals(200, response.status_code)
        response = self.client.get(self.url + 'question/2/')
        tools.assert_equals(302, response.status_code)
        response = self.client.get(self.url + 'question/3/')
        tools.assert_equals(302, response.status_code)
        response = self.client.get(self.url + 'question/0/')
        tools.assert_equals(302, response.status_code)
        response = self.client.get(self.url + 'question/4/')
        tools.assert_equals(302, response.status_code)

    def test_custom_url_for_questions_wizard_contest_without_questions(self):
        response = self.client.get(self.contest2_url + 'question/1/')
        tools.assert_equals(404, response.status_code)
        response = self.client.get(self.contest2_url + 'question/0/')
        tools.assert_equals(302, response.status_code)
        response = self.client.get(self.contest2_url + 'question/4/')
        tools.assert_equals(302, response.status_code)

    def test_detail_url_for_contest(self):
        response = self.client.get(self.url)
        tools.assert_equals(200, response.status_code)

    def test_detail_url_for_contest_without_questions(self):
        response = self.client.get(self.contest2_url)
        tools.assert_equals(200, response.status_code)

    def test_rest_custom_url_for_contest(self):
        response = self.client.get(self.url + 'contestant/')
        tools.assert_equals(302, response.status_code)
        response = self.client.get(self.url + 'result/')
        tools.assert_equals(200, response.status_code)
        response = self.client.get(self.url + 'conditions/')
        tools.assert_equals(200, response.status_code)
