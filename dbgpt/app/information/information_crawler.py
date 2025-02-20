import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote
from typing import List, Dict
import logging
import traceback
from openai import OpenAI
from dbgpt._private.config import Config
import os
from dotenv import load_dotenv
load_dotenv(r"E:\work\code\DB-GPT\dbgpt\app\information\api.config")

logger = logging.getLogger(__name__)
CFG = Config()

class InformationsCrawler:
    def __init__(self):
        self.cookies = {
            'appmsglist_action_3975001738': 'card',
            'RK': '9a3ccWaSsq',
            'ptcz': '27797b98271e767da30b8c2236a56c11fb4016920cc6aa000251f3208277a54e',
            'pac_uid': '0_CkTtR4WS7kMM9',
            '_qimei_uuid42': '18c180a243610026bcbb089858532197e0108f1c64',
            '_qimei_h38': 'e147e01ebcbb0898585321970200000e918c18',
            'suid': 'user_0_CkTtR4WS7kMM9',
            'eas_sid': 'z1w7p3s5r8E0k7E3P2T5S298F0',
            'pgv_pvid': '8551852836',
            'LW_uid': '41G703r5F8T0v7r3w6f2Y427i3',
            'LW_sid': 'B197g3O5x8C0K7m400X1y7y0g1',
            '_qimei_fingerprint': '7f804549d8420704ebf91fb0aaee1411',
            '_qimei_q32': '5d2d4b1e47a89861af1831f687a4d438',
            '_qimei_q36': '48d375e13dd0db01c00c6367300017c18c0e',
            'ua_id': 'pJ3KAhvLCvmYds2OAAAAAC1sWrUusmhrPBnRaofkJug=',
            'wxuin': '37686960468839',
            'mm_lang': 'zh_CN',
            'uuid': '165d7049a964a9c36a9b992d7bb6ab4c',
            '_clck': '3975001738|1|fti|0',
            'rand_info': 'CAESIJ3Isd/awLh+BGz4cZDE45Q6UMqOaLU0B/71wr8Uocxv',
            'slave_bizuin': '3975001738',
            'data_bizuin': '3975001738',
            'bizuin': '3975001738',
            'data_ticket': '46jYlhjyQz24jcrWxwmfkxz3+De9h0YU79dcOelpdvvZzN7vPgTDfoDKFPd54hIl',
            'slave_sid': 'Vllyb3J0RVdJSDdNbGFWZ0swcGdZUkUyaVdNNE5TTjN3NzlkY2FpQjhQR2Z0Z3UxcVo4X3Q3U0FzVHZxNkVGUGgwb3Z4R1NDQmtmOEN5YkpJaTdLTEs4SFZ0am54d1pWVXhjWUxtWVNGb0tnQ3NiUE1pbHVQUk1RaEp3SkxBc2x1UkF4OUt2cEp2Z3l0ZDJq',
            'slave_user': 'gh_c04c432a48d4',
            'xid': '88bff5fb0301c0e5d51f64ac0093e3ce',
            '_clsk': '1xbza6i|1739772758785|2|1|mp.weixin.qq.com/weheat-agent/payload/record',
        }

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://mp.weixin.qq.com/',
        }
        self.client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key=os.getenv("DASHSCOPE_API_KEY"), 
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.timeout = 30
        self.retry_times = 3

    def extract_content(self, url: str) -> str:
        """提取文章内容"""
        for i in range(self.retry_times):
            try:
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                content_div = soup.find('div', class_='rich_media_content')
                
                if content_div:
                    # 移除脚本和样式标签
                    for script in content_div(["script", "style"]):
                        script.decompose()
                    return content_div.get_text(strip=True)
                return ""
            except Exception as e:
                logger.error(f"Attempt {i+1} failed to extract content from {url}: {str(e)}")
                if i == self.retry_times - 1:
                    return ""
                continue

    async def summarize_content(self, content: str) -> str:
        """生成内容摘要"""
        try:
            response = self.client.chat.completions.create(
                model="qwen-max",
                messages=[
                    {"role": "user", "content": f"请对以下内容进行全文总结：{content}，严格按照200字总结，不要超过200字"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error summarizing content: {str(e)}")
            return ""

    async def fetch_news(self, source: str, keyword: str = None) -> List[Dict]:
        """获取新闻数据"""
        try:
            logger.info(f"Fetching news for source: {source}, keyword: {keyword}")
            
            params = {
                'sub': 'search',
                'search_field': '7',
                'begin': '0',
                'count': '2',
                'query': quote(keyword) if keyword else '',
                'fakeid': source,
                'type': '101_1',
                'free_publish_type': '1',
                'sub_action': 'list_ex',
                'token': '2060069689',
                'lang': 'zh_CN',
                'f': 'json',
                'ajax': '1',
            }
            
            # 添加重试机制
            for i in range(self.retry_times):
                try:
                    response = requests.get(
                        'https://mp.weixin.qq.com/cgi-bin/appmsgpublish',
                        params=params,
                        cookies=self.cookies,
                        headers=self.headers,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        break
                    logger.warning(f"Attempt {i+1} failed with status code: {response.status_code}")
                except Exception as e:
                    logger.error(f"Attempt {i+1} failed: {str(e)}")
                    if i == self.retry_times - 1:
                        return []
                    continue
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                return []
            
            if not isinstance(data, dict):
                logger.error(f"Unexpected response format: {type(data)}")
                return []
                
            # 获取文章列表
            publish_page = data.get('publish_page', [])
            if not publish_page:
                logger.warning(f"No articles found for source {source} with keyword {keyword}")
                return []
            
            articleList = json.loads(publish_page)
            informations_list = []
            for item in articleList.get("publish_list"):
                try:
                    publish_info = json.loads(item.get("publish_info"))
                    appmsgex = publish_info.get("appmsgex", [])
                    for appmsg in appmsgex:
                        title_html = appmsg.get("title", "")
                        title = BeautifulSoup(title_html, 'html.parser').get_text()
                        link = appmsg.get("link", "")
                        digest = appmsg.get("digest", "")
                        content = self.extract_content(link)
                        if title and link:
                            summary = await self.summarize_content(content)
                            news_item = {
                                'title': title,
                                'content': content,
                                'source': source,
                                'url': link,
                                'publish_date': datetime.fromtimestamp(item.get('update_time', 0)),
                                'keywords': keyword or '',
                                'summary': summary,
                                'digest': digest
                            }
                            logger.debug(f"Created news item: {news_item}")
                            informations_list.append(news_item)
                        logger.info(f"Successfully processed article: {item.get('title', '')}")
                    
                except Exception as e:
                    logger.error(f"Error processing article: {str(e)}")
                    logger.error(traceback.format_exc())
                    continue
            
            logger.info(f"Returning {len(informations_list)} news items")
            return informations_list
            
        except Exception as e:
            logger.error(f"Error in fetch_news: {str(e)}")
            logger.error(traceback.format_exc())
            return []
            
