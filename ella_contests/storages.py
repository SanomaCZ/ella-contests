from django.conf import settings
from django.utils import simplejson


class BaseStorage(object):

    def set_data(self, contest, step, data, *args, **kwargs):
        raise NotImplementedError("Override set_data in %s!" % self.__class__.__name__)

    def get_data(self, contest, step, *args, **kwargs):
        raise NotImplementedError("Override get_data in %s!" % self.__class__.__name__)

    def remove_data(self, contest, step, *args, **kwargs):
        pass

    def remove_all_data(self, contest, step_max, *args, **kwargs):
        pass

    def set_last_step(self, contest, step, *args, **kwargs):
        raise NotImplementedError("Override set_last_step in %s!" % self.__class__.__name__)

    def get_last_step(self, contest, step, *args, **kwargs):
        raise NotImplementedError("Override get_last_step in %s!" % self.__class__.__name__)


class CookieStorage(BaseStorage):
    cookie_name_step = 'contest_%s_step_%s'
    cookie_name_last_step = 'contest_%s_last_step'
    cookie_domain = settings.SESSION_COOKIE_DOMAIN
    cookie_max_age = 86400 * 31

    def _get_cookie_name_step(self, contest, step):
        return self.cookie_name_step % (contest.pk, step)

    def _get_cookie_name_last_step(self, contest):
        return self.cookie_name_step % (contest.pk)

    def _data_to_json(self, data):
        return simplejson.dumps(data)

    def _data_to_dict(self, str_data):
        return simplejson.loads(str_data)

    def set_data(self, contest, step, data, response, *args, **kwargs):
        response.set_cookie(
            self._get_cookie_name_step(contest, step),
            self._data_to_json(data),
            domain=self.cookie_domain,
            max_age=self.cookie_max_age
        )

    def get_data(self, contest, step, request, *args, **kwargs):
        data = request.COOKIES.get(self._get_cookie_name_step(contest, step), None)
        if data is not None:
            data = self._data_to_dict(data)
        return data

    def set_last_step(self, contest, step, response, *args, **kwargs):
        response.set_cookie(
            self._get_cookie_name_last_step(contest),
            str(step),
            domain=self.cookie_domain,
            max_age=self.cookie_max_age
        )

    def get_last_step(self, contest, request, *args, **kwargs):
        data = request.COOKIES.get(self._get_cookie_name_last_step(contest), None)
        if data is not None:
            data = int(data)
        return data


storage = CookieStorage()
