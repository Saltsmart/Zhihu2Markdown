import requests
import re
import os
import html2text
from urllib.parse import unquote

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15'


class Config:
    def __init__(self, user_agent=DEFAULT_USER_AGENT, download_image=False, asset_path='.'):
        self.user_agent = user_agent
        self.download_image = download_image
        self.asset_path = os.path.expanduser(asset_path)


class Article:
    def __init__(self, article_id, config):
        article_json = request_json(article_id, config.user_agent)
        self.id = article_json['id']
        self.title = article_json['title']
        self.created = article_json['created']
        self.updated = article_json['updated']
        content = article_json['content']

        self.content = preprocess_content(content, config.download_image, config.asset_path)
        self.markdown = html2text.html2text(self.content, bodywidth=0)
        # 在markdown中匹配公式
        latex_pattern = '!\[[\s\S^\]]+?\]\(https:\/\/www.zhihu.com\/equation\?tex=(.+?)\)'

        def latex_repl(matchobj):
            refinedobj: str = matchobj.group(1)
            # 匹配前面的文字要使用
            # refinedobj = refinedobj.replace("\(", "(")  # 替代\(
            # refinedobj = refinedobj.replace("\)", ")")  # 替代\)
            # refinedobj = refinedobj.replace("\[", "[")  # 替代\[
            # refinedobj = refinedobj.replace("\]", "]")  # 替代\]
            # refinedobj = refinedobj.replace("\\\\", "\\")  # 替代\\
            # 匹配tex=后面的文字要使用
            if refinedobj.find("+") >= 0:
                refinedobj = refinedobj.replace("+", " ")  # 将"+"换成空格
            if refinedobj.find("%5Cbegin") >= 0:  # 若为行间公式
                refinedobj = unquote(refinedobj)  # 将带%字符解码为对应内容
                return f'$${refinedobj}$$'
            else:  # 若为行内公式
                refinedobj = unquote(refinedobj)  # 将带%字符解码为对应内容
                return f'${refinedobj}$'
        self.markdown = re.sub(latex_pattern, latex_repl, self.markdown)


def request_json(article_id, user_agent):
    article_api_url = f'https://api.zhihu.com/articles/{article_id}'
    headers = {'user-agent': user_agent}
    return requests.get(article_api_url, headers=headers).json()


def preprocess_content(content, download_image, asset_path):
    # 不再在html中匹配公式
    # latex_pattern = '<img src="https:\/\/www.zhihu.com\/equation\?tex=.+?" alt="(.+?)".+?\/>'
    # def latex_repl(matchobj):
    # 	refinedobj : str = matchobj.group(1)
    # # 匹配alt=后面的文字要使用
    # 	if refinedobj.find("amp;") >= 0:
    # 		refinedobj = refinedobj.replace("amp;", "")  # 删除"amp;"
    # 	# 匹配tex=后面的文字要使用
    # 	# if refinedobj.find("+") >= 0:
    # 	# 	refinedobj = refinedobj.replace("+", " ")  # 将"+"换成空格
    # 	# refinedobj = unquote(refinedobj)  # 将带%字符解码为对应内容
    # 	return f'${refinedobj}$'
    # content = re.sub(latex_pattern, latex_repl, content)
    if download_image:
        if not os.path.exists(asset_path):
            os.makedirs(asset_path)
        image_pattern = r'<img src="(https?.+?)".+?/>'

        def image_repl(matchobj):
            image_url: str = matchobj.group(1)
            # 目前知乎会把公式当成图片，我们不要下载这些东西
            if image_url.find("equation?tex=") >= 0:
                return matchobj.group(0)  # 原样返回
            image_title = image_url.split('/')[-1]
            image_download_path = os.path.join(asset_path, image_title)
            image = requests.get(image_url).content
            with open(image_download_path, 'wb') as image_file:
                image_file.write(image)
            return f'<img src="{image_download_path}">'
        content = re.sub(image_pattern, image_repl, content)
    return content
