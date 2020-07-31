import logging

from influxdb import DataFrameClient

from analyst.utils import get_timestamp

logger = logging.getLogger(__name__)


class InfluxDBAdapter(object):
    def __init__(self, database=None, **kwargs):
        assert database, "Database must be set"
        self.database = database

        self.client = DataFrameClient(database=database, **kwargs)

        if database not in [db.get("name") for db in self.client.get_list_database()]:
            self.client.create_database(database)

        self.client.switch_database(database)

    def delete(self):
        return self.client.drop_database(self.database)

    def list(self):
        return [measure.get("name") for measure in self.client.get_list_measurements()]

    def drop(self, name):
        return self.client.drop_measurement(name)

    def get(self, name, fields="*", start=None, end=None, extra_query=None):
        query = f"select {fields} from {name}"

        time_filter = []
        if start:
            time_filter.append(f"time >= {get_timestamp(start)}s")
        if end:
            time_filter.append(f"time <= {get_timestamp(end)}s")

        if time_filter:
            query += f" WHERE {' AND '.join(time_filter)}"

        if extra_query:
            query += f" {extra_query}"

        return self.client.query(query)

    def store(self, name, measures, reset=False):
        return self.client.write_points(measures, name)
