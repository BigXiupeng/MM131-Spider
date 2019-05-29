#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-05-28 22:42:15
# @Author  : James_jiajia (976033262@qq.com)
# @Link    : http://example.org
# @Version : $Id$

import requests
import threading
import re
import time
import os


pic_links_list = []  # 图片链接集合
threads = []  # 线程集合
all_urls = []  # 我们拼接好的图片集和列表路径
g_lock = threading.Lock()  # 初始化一个锁
pic_group_urls = []  # 分组链接
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
        'Referer': 'https://www.mm131.net/xinggan/',
        'cookie' : 'Hm_lvt_672e68bf7e214b45f4790840981cdf99=1559054650; '
                   'Hm_lpvt_672e68bf7e214b45f4790840981cdf99=1559058461 '
    }



class Spider(object):

    """docstring for Spider"""

    def __init__(self, target_url, headers):
        super(Spider, self).__init__()
        self.target_url = target_url
        self.headers = headers

    # 获取所有想要抓取的url
    def getUrls(self, start_page, page_num):

        global all_urls
        # 循环得到url
        for i in range(start_page, page_num+1):
            if i==1:
                url = 'https://www.mm131.net/xinggan/'
            else:
                url = self.target_url.format(i)
            all_urls.append(url)


class Producer(threading.Thread):

    """docstring for Producer"""

    def run(self):
        while len(all_urls) > 0:
            g_lock.acquire()  # 在访问all_urls的时候，需要进程锁
            page_url = all_urls.pop()  # 通过pop方法移出最后一个元素，并且返回该值
            g_lock.release()  # 使用完成之后及时把锁释放，方便其他线程使用

            try:
                print('分析'+page_url)
                global headers
                response = requests.get(page_url, headers=headers)
                pic_group_link = re.findall(
                    '<a target="_blank" href="(.*?)">', response.text, re.S)

                global pic_group_urls
                g_lock.acquire()
                pic_group_urls += pic_group_link
                print(pic_group_urls)
                g_lock.release()
                
            except:
                pass
            time.sleep(0.5)


class Consumer(threading.Thread):
    def run(self):

        global pic_group_urls
        print('{} is running'.format(threading.current_thread))  # threading.current_thread()表示现在使用的线程
        while len(pic_group_urls)>0:
            g_lock.acquire()
            pic_group_url = pic_group_urls.pop()
            g_lock.release()
            try:
                pic_links = []
                global headers
                response = requests.get(pic_group_url, headers=headers)
                response.encoding = 'gb2312'
                title = re.search(r'<h5>(.*?)</h5>', response.text, re.S).group(1)
                pic_count = re.search(r'<span class="page-ch">共(\d+)页</span>', response.text, re.S).group(1)

                for num in range(1, int(pic_count)+1):
                    pic_link = 'https://img1.mm131.me/pic/' + pic_group_url[-9:-5] + '/{}.jpg'.format(num)
                    pic_links.append(pic_link)
                pic_dict = {title: pic_links}
                global pic_links_list
                g_lock.acquire()
                pic_links_list.append(pic_dict)
                print(title + ' 获取成功')
                g_lock.release()

            except Exception as e:
                print(e)


class Downpic(threading.Thread):
    def run(self):

        while True:
            global headers
            global pic_links_list
            # 上锁
            g_lock.acquire()
            if len(pic_links_list) == 0:
                # 如果没有图片，就释放锁
                g_lock.release()
                continue
            else:
                pic = pic_links_list.pop()
                g_lock.release()

                # 遍历字典列表
                for key,values in pic.items():
                    path = key
                    is_exists = os.path.exists(path)  # 判断是否存在文件夹
                    if not is_exists:
                        # 如果不存在文件夹，就创建一个
                        os.mkdir(path)
                        print(path+'创建成功')
                    else:
                        # 如果文件夹已经存在，就提示已存在
                        print(path+'已存在')
                    for photo in values:
                        filename = path + '/' + photo.split('/')[-1]
                        if os.path.exists(filename):
                            continue
                        else:
                            print('正在下载{}'.format(photo.split('/')[-1]))
                            response = requests.get(photo, headers=headers)
                            with open(filename, 'wb') as f:
                                f.write(response.content)


def main():
    """主程序"""
    kind = {
        '性感美女': 'xinggan',
        '清纯美眉': 'qingchun',
        '美女校花': 'xiaohua',
        '性感车模': 'chemo',
        '旗袍美女': 'qipao',
        '明星写真': 'mingxing',
    }
    select_kind = int(input('请输入你想要下载的图片类型：\n1.性感美女\n2.清纯美眉\n3.美女校花\n4.性感车模\n5.旗袍美女\n6.明星写真\n'))
    if select_kind == 1:
        select_kind = kind.get('性感美女')
    elif select_kind == 2:
        select_kind = kind.get('清纯美眉')
    elif select_kind == 3:
        select_kind == kind.get('美女校花')
    elif select_kind == 4:
        select_kind = kind.get('性感车模')
    elif select_kind == 5:
        select_kind = kind.get('旗袍美女')
    elif select_kind == 6:
        select_kind = kind.get('明星写真')
    else:
        print('输入错误，请重新输入')
        main()
    kind_url = 'https://www.mm131.net/{}/'.format(select_kind)
    target_url = kind_url + 'list_6_{}.html'  # 图片集和列表规则
    spider = Spider(target_url, headers)
    page_num = int(input('请输入你想要下载的页数:'))
    spider.getUrls(1, page_num)

    for x in range(2):
        t = Producer()
        t.start()
        threads.append(t)

    for tt in threads:
        tt.join()  # 等到子线程全部完成工作后才会进行接下来的代码

    print('进行到这里了呢~')

    for x in range(10):
        cpp = Consumer()
        cpp.start()

    for x in range(10):
        down_pic = Downpic()
        down_pic.start()


if __name__ == '__main__':
    main()
