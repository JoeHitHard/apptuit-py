"""
Apptuit Pyformance Reporter
"""
from pyformance.reporters.reporter import Reporter
from apptuit import Apptuit, DataPoint, timeseries
from apptuit.apptuit_client import ApptuitSendException
from apptuit.utils import _get_tags_from_environment

NUMBER_OF_POINTS_SUCCESSFUL = "number_of_points_successful"
NUMBER_OF_POINTS_FAILED = "number_of_points_failed"
API_CALL_TIMER = "api_call_time"

class ApptuitReporter(Reporter):

    def __init__(self, registry=None, reporting_interval=10, token=None,
                 api_endpoint="https://api.apptuit.ai", prefix="", tags=None):
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
        self.client = Apptuit(token, api_endpoint, ignore_environ_tags=True)
        self.__decoded_metrics_cache = {}
        self.__meter_for_number_of_dps_successful = self.registry.meter(NUMBER_OF_POINTS_SUCCESSFUL)
        self.__meter_for_number_of_dps_failed = self.registry.meter(NUMBER_OF_POINTS_FAILED)
        self.__timer_for_api_calls = self.registry.timer(API_CALL_TIMER)
        self.__meta_metrics_count = len(self.registry._get_timer_metrics(API_CALL_TIMER)) +\

    def report_now(self, registry=None, timestamp=None):
        """
        Report the data
        Params:
            registry: pyformance Registry containing all metrics
            timestamp: timestamp of the data point
        """
        dps = self._collect_data_points(registry or self.registry, timestamp)
        if dps:
            try:
                with self.__timer_for_api_calls.time():
                    self.client.send(dps)
                    self.__meter_for_number_of_dps_successful.mark(
                        len(dps) - self.__meta_metrics_count
                    )
            except ApptuitSendException as e:
                self.__meter_for_number_of_dps_successful.mark(
                    e.success - self.__meta_metrics_count
                )
                self.__meter_for_number_of_dps_failed.mark(
                    e.failed
                )
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
