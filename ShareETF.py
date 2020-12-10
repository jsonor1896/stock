import datetime
import os
import time

import requests


class ShareETF:
    """
    获取指定ETF的份额信息
    """

    def __init__(self, code):
        self.code = code
        self.data = []

    def crawl(self):
        """
        获取指定代码的ETF的份额信息
        从集思录获取信息列表，web页面地址：https://www.jisilu.cn/data/etf/detail/code
        实际请求地址：https://www.jisilu.cn/data/etf/detail_hists/?___jsl=LST___t=1607428487104
        :return: 字典形式的代码信息
        """

        url = 'https://www.jisilu.cn/data/etf/detail_hists/?___jsl=LST___t={unixTimestamp}'.format(
            unixTimestamp=time.time() * 1000)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/87.0.4280.67 Safari/537.36 Edg/87.0.664.55',
            'Origin'    : 'https://www.jisilu.cn',
            'Referer'   : 'https://www.jisilu.cn/data/etf/detail/{code}'.format(code=self.code)
        }

        payload = {
            'is_search': 1,
            'fund_id'  : self.code,
            'rp'       : 1,
            'page'     : 1
        }

        content = requests.post(url=url, headers=headers, data=payload).json()

        for item in content['rows']:
            cell = item['cell']

            self.data.append({
                'date'  : cell['hist_dt'],
                'price' : float(cell['trade_price']),
                'amount': float(cell['amount'])
            })

    @staticmethod
    def crawlToday(codeList):
        """
        抓取今日最新值
        :return: 数据字典
        """

        todayDataList = []

        if datetime.datetime.now().hour >= 15: return todayDataList

        url = 'https://www.jisilu.cn/data/etf/etf_list/?___jsl=LST___t={unixTimestamp}&rp=25&page=1'.format(
            unixTimestamp=time.time() * 1000)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/87.0.4280.67 Safari/537.36 Edg/87.0.664.55',
            'Referer'   : 'https://www.jisilu.cn/data/etf/'
        }

        content = requests.get(url=url, headers=headers).json()
        for row in content['rows']:
            item = row['cell']
            if str(item['fund_id']) in codeList:
                todayDataList.append({
                    'code'  : item['fund_id'],
                    'price' : float(item['price']),
                    'amount': float(item['amount']),
                    'date'  : datetime.datetime.now().strftime('%Y-%m-%d')
                })

        return todayDataList


class ETFDao:

    def __init__(self, code):
        self.code = code
        self.dir = './db'
        self.filename = f'{self.dir}/{self.code}.txt'
        self.data = []
        self.dates = []
        self.prices = []
        self.amounts = []
        if not os.path.isfile(self.filename):
            return
        self.read()

    def read(self):
        """
        从数据库中读取数据
        :return:
        """
        with open(self.filename, 'r') as f:
            lines = f.readlines()
            for line in lines:
                itemList = line.strip().split(',')
                self.appendDict(self.data, itemList[0], itemList[1], itemList[2])

        self.updateInnerSingleList()

    def updateInnerSingleList(self):
        """
        更新内部当独数据列表
        :return:
        """
        self.dates.clear()
        self.prices.clear()
        self.amounts.clear()

        for item in self.data:
            self.dates.append(item['date'])
            self.prices.append(item['price'])
            self.amounts.append(item['amount'])

    def write(self):
        """
        以全量式的方式写入文件
        """
        with open(self.filename, 'w') as f:
            for item in self.data:
                string = '{date},{price},{amount}\n'.format(date=item['date'],
                    price=item['price'], amount=item['amount'])
                f.write(string)

    def combineWithDate(self, valDict):
        """
        以日期的方式将数据合并处理
        :param valDict: 数据字典
        """
        tmp = []
        for item in valDict:
            if item['date'] in self.dates:
                continue
            self.appendDict(tmp, item['date'], item['price'], item['amount'])

        for item in self.data:
            self.appendDict(tmp, item['date'], item['price'], item['amount'])

        self.data = tmp
        self.updateInnerSingleList()

    @classmethod
    def appendDict(cls, dst, date, price, amount):
        dst.append({
            'date'  : date,
            'price' : float(price),
            'amount': float(amount)
        })


CodeDict = {
    '510500': 'ETF500',
    '510300': 'ETF300',
    '510050': 'ETF50',
    '515000': '科技ETF',
    '512880': '券商ETF',
    '512290': '医药ETF',
    '159949': '创业50ETF'
}

CodeList = [
    '510500', '510300', '510050', '515000',
    '512880', '512290', '159949',
]


def normalize(vals):
    vals.reverse()
    m = max(vals)
    return [val / m for val in vals]


def run():
    todayDataList = ShareETF.crawlToday(CodeList)
    for code, val in CodeDict.items():
        dao = ETFDao(code)
        shareETF = ShareETF(code)
        shareETF.crawl()
        dao.combineWithDate(shareETF.data)
        dao.write()

        for item in todayDataList:
            if code == item['code']:
                dao.dates.append(item['date'])
                dao.prices.append(item['price'])
                dao.amounts.append(item['amount'])
                break

        import matplotlib.pyplot as plt

        prices = normalize(dao.prices)
        amounts = normalize(dao.amounts)

        plt.title(code)
        plt.plot(range(len(prices)), prices, 'r-.', label='prices')
        plt.plot(range(len(amounts)), amounts, 'b-.', label='amounts')
        plt.legend()
        plt.show()

run()
