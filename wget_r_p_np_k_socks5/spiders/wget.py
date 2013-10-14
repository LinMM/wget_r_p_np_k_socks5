#coding:utf-8
'''
Created on 2013-10-6

@author: lingshao.zzy
'''
from scrapy.contrib.spiders import CrawlSpider,Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.http import Request
from scrapy.http import Response
import urllib
import re
import os

class testLinkExtractorSpider(CrawlSpider):
    name="testLinkExtractor"
    
    start_urls=[]
    
    
    MY_IGNORED_EXTENSIONS = [
    # audio
    'mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au', 'aiff',

    # video
    '3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt', 'rm', 'swf', 'wmv',
    'm4a',

    # office suites
    'xls', 'ppt', 'doc', 'docx', 'odt', 'ods', 'odg', 'odp',

    # other
    'pdf', 'doc', 'exe', 'bin', 'rss', 'zip', 'rar',
    ]
    linkExtractor = SgmlLinkExtractor(deny_extensions=MY_IGNORED_EXTENSIONS,tags=('a', 'area','img','script'), attrs=('href','src'))
    
    
    
    pattern_html='text/html'
    pattern_image='image/'
    pattern_javascript='text/javascript'
    pattern_css='text/css'
    pattern_plain='text/plain'
    
    #url与文件名的对应表
    url_file={}
    
    def __init__(self,url,location):
        super(CrawlSpider,self).__init__()
        self.start_urls.append(url)

        #取域名和保存位置
        self.prefix=location        
        self.domain=self._getDomain(url)

    #处理response    
    def parse(self,response):
        #处理header的contentType字段
        if(response.headers.has_key("content-type")):
            content_type=response.headers["content-type"]
            #html页面
            if(None !=re.search(self.pattern_html, content_type)):
                proto,rest = urllib.splittype(response.url)
                domain,rest=urllib.splithost(rest)
                #是需要的域名就处理
                if(domain==self.domain):
                    #保存，修改链接
                    self._save(response)
                    
                    return self._parseHTML(response)
                    
            #文本资源页面
            elif(None!=re.search(self.pattern_css+'|'+self.pattern_javascript+'|'+self.pattern_plain,content_type)):
                #保存，修改链接
                self._save(response)
            #图片资源
            elif(None != re.search(self.pattern_image,content_type)):
                #保存，修改链接
                self._save(response, 'wb')
    
    #保存数据
    def _save(self,response,writeflag='w'):
        #文件前缀+path
        name=self._getPath(response.url)
        if(os.path.basename(name)==''):
            name =  name + 'index.html'
        fileName=self.prefix+name
        #生成改文件的文件名
        self.url_file[response.url]=fileName
        
        #生成文件目录
        self._mkdir(fileName)
        #写入文件
        f=open(fileName,writeflag)
        f.write(response.body)
        f.close()
        #修改referer上的相对链接
        #如果该链接有referer
        if(response.request.headers.has_key("Referer")):
            referer=response.request.headers["Referer"]
            if(self.url_file[referer]!=self.fileName):
                #将当前编辑的缓冲区写入文件
                f=open(self.fileName,'w')
                f.write(self.htmlBody)
                f.close()
                
                #读取新的html到缓冲区
                f=open(self.url_file[referer],"r")
                self.htmlBody=f.read()
                f.close()
                
                #记录缓冲区对应的文件名
                self.fileName=self.url_file[referer]
                
            #将缓冲区中的本链接找到，转为相对链接
            
            self.htmlBody=self._setRelativeLink(self.htmlBody,referer,response.url)
                
                
        #没referer表示是第一个请求，把自己当做referer
        else:
            self.fileName=fileName
            #读取新的html到缓冲区
            f=open(fileName,"r")
            self.htmlBody=f.read()
            f.close()
    
    def _parseHTML(self,response):
        f=open(self.url_file[response.url],'r')
        _htmlBody=f.read()
        f.close()
        
        for link in self.linkExtractor.extract_links(response):
            if(self.url_file.has_key(link.url)):
                _htmlBody=self._setRelativeLink(_htmlBody, response.url, link.url)
            elif(self._getDomain(link.url)==self.domain):
                self.log('lingk"'+link.url)
                yield Request(link.url)
                        
        f=open(self.url_file[response.url],'w')
        f.write(_htmlBody)
        f.close()
    
    #获取url path
    def _getPath(self,url):
        proto,rest=urllib.splittype(url)
        host,rest=urllib.splithost(rest)
        path,query=urllib.splitquery(rest)
        return path
    
    #获取url的host
    def _getDomain(self,url):
        proto,rest=urllib.splittype(url)
        host,rest=urllib.splithost(rest)
        return host
    
    #设置缓冲区的绝对链接为相对链接
    def _setRelativeLink(self,_htmlBody,contexturl,url):
        #准备工作    
        contextDir=os.path.dirname(self._getPath(contexturl))
        urlDir=os.path.dirname(self._getPath(url))
        urlBase=os.path.basename(url)
        contextDir=contextDir.split('/')[1:]
        urlDir=urlDir.split('/')[1:]
        
        #生成相对链接
        parentLength=len(contextDir)
        for i in range(parentLength):
            if(len(urlDir)<i+1 or contextDir[i]!=urlDir[i]):
                break
            parentLength=parentLength-1        
        parent=[]
        for i in range(parentLength):
            parent.append(os.pardir)
            
        path=[]
        pathLength=len(contextDir)-parentLength
        if(len(urlDir)>pathLength):
            for p in urlDir[pathLength:]:
                path.append(p)
        parent.extend(path)
        parent.append(urlBase)
        relativeLink='/'.join(parent)
        #替换相对链接
        return re.sub(url,relativeLink,_htmlBody,flags=re.S)
    
    
    
    #生成文件目录
    def _mkdir(self,fileName):
        if(not os.path.isdir(os.path.dirname(fileName))):
            os.makedirs(os.path.dirname(fileName))

