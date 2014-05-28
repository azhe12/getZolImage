#!/usr/bin/env python
#encoding=utf-8

import random
import urllib2
import urllib
import cookielib
import re
import argparse
import string
import os
import thread
import threading
import time
from bs4 import BeautifulSoup
from time import clock


url_top = 'http://sj.zol.com.cn'
url_bizhi = url_top + '/bizhi'
USER_AGENTS = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
               'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100 101 Firefox/22.0',
               'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0',
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',
               'Mozilla/5.0 (Windows; Windows NT 6.1) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',)


headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}


class Download_theme_img(threading.Thread):
    def __init__(self, thread_id, theme_link):
        super(Download_theme_img, self).__init__()
        self.thread_id = thread_id
        self.theme_link = theme_link

    #依据最终link, 下载img
    def download_img(self, link, img_name_prefix):
        req = urllib2.Request(link, headers=headers) #GET
        res = urllib2.urlopen(req)
        #res_text = res.read()
    
        try:
            content_disposition = res.info()['Content-Disposition'] #如'attachment; filename="1395317658719.jpg"', 为了得到其中的图片格式, '.jpg'
            pat = '.*(\..*)"' 
            img_format = re.search(pat, content_disposition).group(1)
        except:
            print 'Warning: can\'t get "Content-Disposition" from response header!'
            img_format = '.jpg'
    
        
        img_name = img_name_prefix + img_format
    
        with open(img_name, 'w+') as f:
            f.write(res.read())
        f.close()
    
        print '\t%s done!' % img_name
    

    def get_img(self, thread_id, theme_link):
        print 'start Thread %d!' % thread_id
        req = urllib2.Request(theme_link, headers=headers) #GET
        res = urllib2.urlopen(req)
        res_text = res.read()
        #print res_text
        soup = BeautifulSoup(res_text)
    
        theme_title = soup('h1')[0].a.string        #标题
        img_download_dir = os.getcwd() + '/images/' + theme_title
        try:
            os.mkdir(img_download_dir.encode())          #图片下载目录
        except:
            pass
    
        max_links_num_str = soup.find(attrs={'id':'img1'}).i.contents[1].string     #如u'/16'之类的，最大图片张数
        pattern = '/([0-9]+)'
        match = re.search(pattern, max_links_num_str)
        max_links_num = match.group(1)  #如，得到16
    
        resolution = soup.find(attrs={'id':'maxcurSize'}).string    #图片的分辨率, 如`320x480`
    
        img_download_links = []
    
        pattern = 'http://.*detail_[0-9]+_([0-9]+).html'
        img_link = theme_link   #theme_link是第一个img_link
        first = True
        print 'Thread %d: Download images in: %s' % (thread_id, img_download_dir)
    
        for i in range(1, string.atoi(max_links_num) + 1):  #遍历本主题所有图片link
            '''
            link 'http://sj.zol.com.cn/bizhi/detail_5827_62326.html'中的62326即为img_htm_index
            '''
            img_link_index = re.search(pattern, img_link).group(1)
        
            img_download_link = url_bizhi + \
                                '/down_' + \
                                img_link_index + \
                                '_' + \
                                resolution + \
                                '.html' #http://sj.zol.com.cn/bizhi/down_62327_800x1280.html
            
            img_download_links.append(img_download_link)
    
            img_name_prefix = img_download_dir + '/' + theme_title + '_' + resolution + '_' + str(i)
            #下载图片
            #print '\tlink: ' + img_download_link
            self.download_img(img_download_link, img_name_prefix)
            '''
            计算next的link
            重新request img_url才能得到next
            '''
            if first:
                first = False
            else:
                req = urllib2.Request(img_link, headers=headers)
                soup = BeautifulSoup(urllib2.urlopen(req).read())
    
            next_link = url_top + soup.find(attrs={'class':'next'})['href']
            #print 'nextlink: ' + next_link
            img_link = next_link
        
            #print max_links_num, resolution, img_link_index, img_download_link
    
        #print img_download_links
        #print 'title: ', theme_title
        print 'Thread %d exit!' % thread_id
    

    def run(self):
        self.get_img(self.thread_id, self.theme_link)


def get_theme_links():
    req = urllib2.Request(url_bizhi, headers=headers) #GET
    res = urllib2.urlopen(req)
    
    res_text = res.read()
    #print res_text
    soup = BeautifulSoup(res_text)
    
    links = []
    for a in soup.findAll(attrs={'class':'pic'}):
        links.append(url_top + a['href'])
    return links
    
def get_zol_image():
    start = time.time()
    #cookie
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)

    #theme_links = get_theme_links()
    download_threads = []
    for i,theme_link in enumerate(get_theme_links()):
        t = Download_theme_img(i, theme_link)   #多线程下载img
        download_threads.append(t)
        t.setDaemon(True)
        t.start()

    for download_thread in download_threads:
        download_thread.join()
    #while True:
        #pass

    print 'Done! Elapse: %d s' % (time.time()-start)
    
'''
url_jpg = 'http://sj.zol.com.cn/bizhi/down_62327_800x1280.html'
req = urllib2.Request(url_jpg, headers=headers)
res = urllib2.urlopen(req)
#print res.info()['Content-Disposition']
#print res.info()

res_text = res.read()
jpg = open('/home/azhe/test.jpg', 'w+')
jpg.write(res_text)
jpg.close()
#print res_text
'''
if __name__ == '__main__':
    theme_link = 'http://sj.zol.com.cn/bizhi/detail_5839_62457.html'
    get_zol_image()
