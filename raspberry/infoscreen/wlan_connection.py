import network
import time


class WlanConnection:
    def __init__(
        self,
        ssid,
        password,
        debug=False,
        logger=None,
        max_wait=10,
        wait_seconds=2,
    ):
        self.ssid = ssid
        self.password = password
        self.debug = debug
        self.logger = logger
        self.max_wait = max_wait
        self.wait_seconds = wait_seconds
        self.wlan = network.WLAN(network.STA_IF)

    def _log(self, message):
        if self.debug and self.logger is not None:
            self.logger(message)

    def connect(self):
        self.wlan.active(True)

        if self.wlan.status() != 3:
            self.wlan.connect(self.ssid, self.password)

        max_wait = self.max_wait
        while max_wait > 0:
            status = self.wlan.status()
            if status < 0 or status >= 3:
                break

            max_wait -= 1
            self._log("waiting for connection...")
            time.sleep(self.wait_seconds)

        status = self.wlan.status()
        if status != 3:
            raise OSError("network connection failed (status=%s)" % status)

        self._log("network connected")
        return self.wlan

    def disconnect(self):
        self.wlan.disconnect()
        self.wlan.active(False)

    def is_connected(self):
        return self.wlan.status() == 3

    def status(self):
        return self.wlan.status()

    def ifconfig(self):
        return self.wlan.ifconfig()