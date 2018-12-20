"""
Apptuit Pyformance Reporter
"""
import sys
from pyformance import MetricsRegistry
from pyformance.reporters.reporter import Reporter
from apptuit import Apptuit, DataPoint, timeseries, ApptuitSendException
from apptuit.utils import _get_tags_from_environment

NUMBER_OF_TOTAL_POINTS = "apptuit.reporter.send.total"
NUMBER_OF_SUCCESSFUL_POINTS = "apptuit.reporter.send.successful"
NUMBER_OF_FAILED_POINTS = "apptuit.reporter.send.failed"
API_CALL_TIMER = "apptuit.reporter.send.time"

def default_error_handler(apptuit_send_exception, **kwargs):
    """
    This is a default error handler for Apptuit.send() api
    :param apptuit_send_exception: An ApptuitSendException object
        containing error details.
    :param kwargs: In case you need additional params, you can pass them as kwargs.
    :return: None
    """
    sys.stderr.write(str(apptuit_send_exception))

class ApptuitReporter(Reporter):

    def __init__(self, registry=None, reporting_interval=10, token=None,
                 api_endpoint="https://api.apptuit.ai", prefix="", tags=None,
                 error_handler=default_error_handler, **kwargs_for_error_handler):
        """
            :param registry: A metric registry object which contains all metrics.
            :param reporting_interval: An integer specifying time to report.
            :param token: A string containing Apptuit API Token.
            :param prefix: A string containing prefix added to for all metrics.
            :param tags: A dictionary containing tags and values included to all metrics.
            :param error_handler: A function object refer _error_handler for more details.
            :param kwargs_for_error_handler: kwargs for error handler.
        """
        super(ApptuitReporter, self).__init__(registry=registry,
                                              reporting_interval=reporting_interval)
        self.endpoint = api_endpoint
        self.token = token
        self.tags = tags
        environ_tags = _get_tags_from_environment()
        if environ_tags:
            if self.tags is not None:
                environ_tags.update(self.tags)
            self.tags = environ_tags
        self.prefix = prefix if prefix is not None else ""
        self.__decoded_metrics_cache = {}
        self.client = Apptuit(token, api_endpoint, ignore_environ_tags=True)
        self._meta_metrics_registry = MetricsRegistry()
        self.error_handler = error_handler
        self.kwargs_for_error_handler = kwargs_for_error_handler

    def _update_counter(self, key, value):
        self._meta_metrics_registry.counter(key).inc(value)

    def report_now(self, registry=None, timestamp=None):
        """
        Report the data
        Params:
            registry: pyformance Registry containing all metrics
            timestamp: timestamp of the data point
        """
        dps = self._collect_data_points(registry or self.registry, timestamp)
        self._update_counter(NUMBER_OF_TOTAL_POINTS, len(dps))
        meta_dps = self._collect_data_points(self._meta_metrics_registry)
        if dps:
            try:
                with self._meta_metrics_registry.timer(API_CALL_TIMER).time():
                    self.client.send(dps + meta_dps)
                    self._update_counter(NUMBER_OF_SUCCESSFUL_POINTS, len(dps))
                    self._update_counter(NUMBER_OF_FAILED_POINTS, 0)
            except ApptuitSendException as e:
                e.success -= len(meta_dps)
                self._update_counter(NUMBER_OF_SUCCESSFUL_POINTS, e.success)
                self._update_counter(NUMBER_OF_FAILED_POINTS, e.failed)
                if self.error_handler:
                    self.error_handler(e, **self.kwargs_for_error_handler)
                raise e

    def _get_tags(self, key):
        """
        Get tags of a metric
        Params:
            metric key
        Returns:
            metric name, dictionary of tags
        """
        val = self.__decoded_metrics_cache.get(key)
        if val:
            return val[0], val[1]

        metric_name, metric_tags = timeseries.decode_metric(key)
        self.__decoded_metrics_cache[key] = (metric_name, metric_tags)
        return metric_name, metric_tags

    def _collect_data_points(self, registry, timestamp=None):
        """
        will collect all metrics from registry and convert them to DataPoints
        Params:
            registry: pyformance registry object
            timestamp: timestamp of the data point
        Returns:
            list of DataPoints
        """
        timestamp = timestamp or int(round(self.clock.time()))
        metrics = registry.dump_metrics()
        dps = []
        global_tags = self.tags if self.tags else {}
        for key in metrics.keys():
            metric_name, metric_tags = self._get_tags(key)
            if metric_tags and global_tags:
                tags = global_tags.copy()
                tags.update(metric_tags)
            elif metric_tags:
                tags = metric_tags
            else:
                tags = global_tags
            for value_key in metrics[key].keys():
                dps.append(DataPoint(metric="{0}{1}.{2}".format(self.prefix, metric_name, value_key),
                                     tags=tags,
                                     timestamp=timestamp,
                                     value=metrics[key][value_key]))
        return dps
