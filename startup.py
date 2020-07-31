from influxdb import InfluxDBClient, DataFrameClient
import influxdb

influx_conn_args = {
    "host": "influxdb",
    "database": "test"
}

indb = InfluxDBClient(**influx_conn_args)
indf = DataFrameClient(**influx_conn_args)

from portfolio.models import *

aa = Asset.objects.all()
af = aa.first()
al = aa.last()

from analyst.adapter import *
av = AlphaVantageAdapter()

idb = InfluxDBAdapter()

from portfolio.scrapper import *
from pprint import pprint

isc = InvestingScrapper()

pp = Portfolio.objects.all()
p = Portfolio.objects.first()

for _p in pp:
  df = _p.get_dataframe(fields="close")

ii = Index.objects.all()
i = Index.objects.first()

for _i in ii:
  dg = _i.get_dataframe(fields="close")
  dh = _i.get_dataframe(objects=[_i.indice], fields="close")
