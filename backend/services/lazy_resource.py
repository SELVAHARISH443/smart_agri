import logging
import threading


class ResourceLoadError(RuntimeError):
    pass


class LazyResource:
    def __init__(self, name):
        self.name = name
        self._lock = threading.Lock()
        self._state = "not_loaded"
        self._value = None
        self._error = None

    @property
    def status(self):
        result = {"status": self._state}
        if self._error:
            result["error"] = self._error
        return result

    def get(self, loader):
        if self._state == "loaded":
            return self._value
        if self._state == "failed":
            raise ResourceLoadError(self._error)

        with self._lock:
            if self._state == "loaded":
                return self._value
            if self._state == "failed":
                raise ResourceLoadError(self._error)

            self._state = "loading"
            try:
                self._value = loader()
            except Exception as error:
                self._error = f"Unable to load {self.name}: {error}"
                self._state = "failed"
                logging.getLogger(__name__).exception(self._error)
                raise ResourceLoadError(self._error) from error

            self._state = "loaded"
            return self._value
