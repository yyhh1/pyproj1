# 导入需要的模块
import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import pandas as pd
import os
import json

rootdir = 'C:\\Users\\yuanhang\\PycharmProjects\\scraping'
datadir = os.path.join(rootdir, 'data')
PER = 49

idxurl = 'http://push2his.eastmoney.com/api/qt/stock/kline/get?cb=jQuery1124008791918140086752_1610520913527&secid={mkt}.{code}&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=101&fqt=0&beg=19900101&end=20230101'


def get_idx_data_raw(code):

    for mkt in '01':
        res = requests.get(idxurl.format(mkt=mkt, code=code))
        jsload = re.match('.*\((.*)\);$', res.text).groups(0)[0]
        data = json.loads(jsload)
        if data['data'] is not None:
            return data['data']

    raise ValueError('No data loaded for index {}'.format(code))


def get_idx_data(code, refresh=False):
    cache_file = os.path.join(datadir, code+'.csv')
    if not refresh and code+'.csv' in os.listdir(datadir):
        return pd.read_csv(cache_file, parse_dates=['ref_date']).set_index('ref_date')

    data = get_idx_data_raw(code)
    klines = data['klines']

    cols = ['ref_date', 'open', 'close', 'high', 'low', 'volume', 'v1', 'v2']
    df = pd.DataFrame([x.split(',') for x in klines], columns=cols)

    df['ref_date'] = pd.to_datetime(df['ref_date'])
    df[cols[1:]] = df[cols[1:]].astype(float)
    df['name'] = data['name']
    df['code'] = data['code']
    df['ret'] = df['close'].pct_change(1)
    df = df.set_index('ref_date')
    print('Caching code={} upto {}'.format(code, df.index[-1]))
    df.to_csv(cache_file)

    return df


# 抓取网页
def get_url(url, params=None, proxies=None):
    rsp = requests.get(url, params=params, proxies=proxies)
    rsp.raise_for_status()
    return rsp.text


# 从网页抓取数据
def get_fund_data_raw(code, sdate='', edate='', proxies=None):
    url = 'http://fund.eastmoney.com/f10/F10DataApi.aspx'
    params = {'type': 'lsjz', 'code': code, 'page': 1, 'per': PER}
    if sdate:
        params.update({'sdate': sdate})
    if edate:
        params.update({'edate': edate})

    html = get_url(url, params, proxies)
    soup = BeautifulSoup(html, 'html.parser')

    # 获取总页数
    pattern = re.compile(r'pages:(.*),')
    result = re.search(pattern, html).group(1)
    pages = int(result)

    # 获取表头
    heads = []
    for head in soup.findAll("th"):
        heads.append(head.contents[0])

    # 数据存取列表
    records = []

    # 从第1页开始抓取所有页面数据
    page = 1
    while page <= pages:
        params = {'type': 'lsjz', 'code': code, 'page': page, 'per': PER, 'sdate': sdate, 'edate': edate}
        html = get_url(url, params, proxies)
        soup = BeautifulSoup(html, 'html.parser')

        # 获取数据
        for row in soup.findAll("tbody")[0].findAll("tr"):
            row_records = []
            for record in row.findAll('td'):
                val = record.contents

                # 处理空值
                if val == []:
                    row_records.append(np.nan)
                else:
                    row_records.append(val[0])

            # 记录数据
            records.append(row_records)

        # 下一页
        page = page + 1

    # 数据整理到dataframe
    np_records = np.array(records)
    data = pd.DataFrame()
    for col, col_name in enumerate(heads):
        data[col_name] = np_records[:, col]

    return data


def get_fund_data(code, sdate='', edate='', refresh=False):
    cache_file = os.path.join(datadir, code+'.csv')
    if not refresh and code+'.csv' in os.listdir(datadir):
        return pd.read_csv(cache_file, parse_dates=['ref_date']).set_index('ref_date')

    data = get_fund_data_raw(code, sdate, edate)
    data['ref_date'] = pd.to_datetime(data['净值日期'], format='%Y/%m/%d')
    data['unit_val'] = data['单位净值'].astype(float)
    data['cval'] = data['累计净值'].astype(float)
    data['ret'] = data['日增长率'].str.strip('%').astype(float) / 100.

    data = data[['ref_date', 'unit_val', 'cval', 'ret']]
    data = data.sort_values(by='ref_date', axis=0, ascending=True).set_index('ref_date')
    print('Caching code={} upto {}'.format(code, data.index[-1]))
    data.to_csv(cache_file)

    return data


def get_fund_ret(code, **kwargs):
    data = get_fund_data(code, **kwargs)
    return data.set_index('ref_date')['ret']
