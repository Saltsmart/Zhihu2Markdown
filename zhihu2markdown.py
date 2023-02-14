from lib.transformer import *
import argparse
import re
import os

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Transform zhihu article to Markdown format')
	parser.add_argument('article_url', help='URL of zhihu article')
	parser.add_argument('-o', '--output', help='path of output markdown file')
	parser.add_argument('-i', '--image_dir', help='If present, download image to the image dir path')
	parser.add_argument('-a', '--user_agent', help='User agent')

	args = parser.parse_args()

	config = Config()
	if args.image_dir:
		config.download_image = True
		config.asset_path = args.image_dir
	if args.user_agent:
		config.user_agent = args.user_agent

	article_pattern = r'https://zhuanlan.zhihu.com/p/(\d.+)/?'
	objmatch = re.search(article_pattern, args.article_url)
	if not objmatch.group(1):
		raise "Article URL not match. Must be: https://zhuanlan.zhihu.com/p/xxxxxxx"

	article = Article(objmatch.group(1), config)
	output_path = args.output if args.output else './' + article.title + ".md"
	output_path = os.path.expanduser(output_path)
	with open(output_path, 'w') as output_file:
		output_file.write(article.markdown)
