"""PDF Knowledge."""
import json
import os
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Union
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract-OCR\tesseract.exe'

from dbgpt.component import logger
from dbgpt.core import Document
from dbgpt.rag.knowledge.base import (
    ChunkStrategy,
    DocumentType,
    Knowledge,
    KnowledgeType,
)

# PDF 知识处理类
class PDFKnowledge(Knowledge):
    """PDF Knowledge."""

    def __init__(
        self,
        file_path: Optional[str] = None,
        knowledge_type: KnowledgeType = KnowledgeType.DOCUMENT,
        loader: Optional[Any] = None,
        language: Optional[str] = "zh",
        metadata: Optional[Dict[str, Union[str, List[str]]]] = None,
        **kwargs: Any,
    ) -> None:
        """Create PDF Knowledge with Knowledge arguments.

        Args:
            file_path(str,  optional): file path
            knowledge_type(KnowledgeType, optional): knowledge type
            loader(Any, optional): loader
            language(str, optional): language
        """
        super().__init__(
            path=file_path,
            knowledge_type=knowledge_type,
            data_loader=loader,
            metadata=metadata,
            **kwargs,
        )
        self._language = language
        self._pdf_processor = PDFProcessor(filepath=self._path)
        self.all_title: List[dict] = []
        self.all_text: List[dict] = []
    # 处理文本数据，提取一级和二级标题
    def process_text_data(self):
        """Text data processing to level 1 and level 2 titles."""
        for i, data in enumerate(self.all_text):
            # data = self.all_text[i]
            inside_content = data.get("inside") # 获取文本内容
            content_type = data.get("type") # 获取文本类型      
            if content_type == "text":
                # use regex to match the first level title
                # 使用正则表达式匹配一级标题
                first_level_match = re.match(
                    r"§(\d+)+([\u4e00-\u9fa5]+)", inside_content.strip()
                )
                # 使用正则表达式匹配二级标题
                second_level_match = re.match(
                    r"(\d+\.\d+)([\u4e00-\u9fa5]+)", inside_content.strip()
                )
                # 使用正则表达式匹配纯数字标题
                first_num_match = re.match(r"^§(\d+)$", inside_content.strip())
                # get all level 1 titles
                title_name = [
                    dictionary["first_title"]
                    for dictionary in self.all_title
                    if "first_title" in dictionary
                ]
                if first_level_match:
                    first_title_text = first_level_match.group(2)
                    first_title_num = first_level_match.group(1)
                    first_title = first_title_num + first_title_text
                    # the title does not contain "..." and is not in the title list
                    # , add it to the title list
                    if first_title not in title_name and (
                        int(first_title_num) == 1
                        or int(first_title_num) - int(self.all_title[-1]["id"]) == 1
                    ):
                        current_entry = {
                            "id": first_title_num,
                            "first_title": first_title,
                            "second_title": [],
                            "table": [],
                        }
                        self.all_title.append(current_entry)

                elif second_level_match:
                    second_title_name = second_level_match.group(0)
                    second_title = second_level_match.group(1)
                    first_title = second_title.split(".")[0]
                    if (int(first_title) - 1 >= len(self.all_title)) or int(
                        first_title
                    ) - 1 < 0:
                        continue
                    else:
                        titles = [
                            sub_item["title"]
                            for sub_item in self.all_title[int(first_title) - 1][
                                "second_title"
                            ]
                        ]
                        if second_title_name not in titles:
                            self.all_title[int(first_title) - 1]["second_title"].append(
                                {"title": second_title_name, "table": []}
                            )
                elif first_num_match:
                    first_num = first_num_match.group(1)
                    first_text = self.all_text[i + 1].get("inside")
                    first_title = first_num_match.group(1) + first_text
                    # if the title does not contain "..." and is not in the title list
                    if (
                        "..." not in first_text
                        and first_title not in title_name
                        and (
                            int(first_num) == 1
                            or int(first_num) - int(self.all_title[-1]["id"]) == 1
                        )
                    ):
                        current_entry = {
                            "id": first_num,
                            "first_title": first_title,
                            "second_title": [],
                            "table": [],
                        }
                        self.all_title.append(current_entry)
    # 加载PDF文档
    def _load(self) -> List[Document]:
        """Load pdf document from loader."""
        if self._loader:
            # 使用自定义加载器
            documents = self._loader.load()
        else:
            # 使用默认处理流程
            self._pdf_processor.pdf_to_json()   # 将PDF文档转换为JSON格式   
            file_title = self.file_path.rsplit("/", 1)[-1].replace(".pdf", "")  # 获取文件名
            self.all_text = list(self._pdf_processor.all_text.values())  # 获取所有文本
            self.process_text_data()  # 处理文本数据
            temp_table = []  # 临时表格
            temp_title = None  # 临时标题
            page_documents = []  # 页面文档
            merged_data = {}  # type: ignore # noqa
            for i, data in enumerate(self.all_text):
                content_type = data.get("type")
                inside_content = data.get("inside")
                page = data.get("page")
                # 处理表格数据
                if content_type == "excel":
                    temp_table.append(inside_content)
                    if temp_title is None:
                        # 查找表格标题
                        for j in range(i - 1, -1, -1):
                            if self.all_text[j]["type"] == "excel":
                                break
                            if self.all_text[j]["type"] == "text":
                                content = self.all_text[j]["inside"]
                                if re.match(
                                    r"^\d+\.\d+", content
                                ) or content.startswith("§"):
                                    temp_title = content.strip()
                                    break
                                else:
                                    temp_title = content.strip()
                                    break
                elif content_type == "text":
                    # 合并表格数据
                    if page in merged_data:
                        # page merge
                        # 合并同一页的文本
                        merged_data[page]["inside_content"] += " " + inside_content
                    else:
                        # 创建新的页面数据
                        merged_data[page] = {
                            "inside_content": inside_content,
                            "type": "text",
                        }

                    # merge excel table
                    if temp_table:
                        table_meta = {
                            "title": temp_title or temp_table[0],
                            "type": "excel",
                        }
                        self.all_title.append(table_meta)
                        # 转换表格为markdown格式
                        # markdown format
                        markdown_tables = []
                        if temp_table:
                            header = eval(temp_table[0])
                            markdown_tables.append(header)
                            for entry in temp_table[1:]:
                                row = eval(entry)
                                markdown_tables.append(row)
                            markdown_output = "| " + " | ".join(header) + " |\n"
                            markdown_output += (
                                "| " + " | ".join(["---"] * len(header)) + " |\n"
                            )
                            for row in markdown_tables[1:]:
                                markdown_output += "| " + " | ".join(row) + " |\n"

                            #  merged content
                            merged_data[page]["excel_content"] = temp_table
                            merged_data[page]["markdown_output"] = markdown_output

                        temp_title = None
                        temp_table = []

            # deal last excel
            if temp_table:
                table_meta = {
                    "title": temp_title or temp_table[0],
                    "table": temp_table,
                    "type": "excel",
                }
                self.all_title.append(table_meta)
                # markdown format
                markdown_tables = []
                if temp_table:
                    header = eval(temp_table[0])
                    markdown_tables.append(header)
                    for entry in temp_table[1:]:
                        row = eval(entry)
                        markdown_tables.append(row)
                    markdown_output = "| " + " | ".join(header) + " |\n"
                    markdown_output += "| " + " | ".join(["---"] * len(header)) + " |\n"
                    for row in markdown_tables[1:]:
                        markdown_output += "| " + " | ".join(row) + " |\n"
                    #  merged content
                    merged_data[page]["excel_content"] = temp_table
                    merged_data[page]["markdown_output"] = markdown_output

            for page, content in merged_data.items():
                inside_content = content["inside_content"]
                if "markdown_output" in content:
                    markdown_content = content["markdown_output"]
                    content_metadata = {
                        "page": page,
                        "type": "excel",
                        "title": file_title,
                        "source": self.file_path,
                    }
                    page_documents.append(
                        Document(
                            content=inside_content + "\n" + markdown_content,
                            metadata=content_metadata,
                        )
                    )
                else:
                    content_metadata = {
                        "page": page,
                        "type": "text",
                        "title": file_title,
                        "source": self.file_path,
                    }
                    page_documents.append(
                        Document(content=inside_content, metadata=content_metadata)
                    )

            return page_documents
        return [Document.langchain2doc(lc_document) for lc_document in documents]

    # 返回支持的分割策略
    @classmethod
    def support_chunk_strategy(cls) -> List[ChunkStrategy]:
        """Return support chunk strategy."""
        return [
            ChunkStrategy.CHUNK_BY_SIZE,
            ChunkStrategy.CHUNK_BY_PAGE,
            ChunkStrategy.CHUNK_BY_SEPARATOR,
        ]
    # 返回默认的分割策略
    @classmethod
    def default_chunk_strategy(cls) -> ChunkStrategy:
        """Return default chunk strategy."""
        return ChunkStrategy.CHUNK_BY_SIZE
    # 返回知识类型
    @classmethod
    def type(cls) -> KnowledgeType:
        """Return knowledge type."""
        return KnowledgeType.DOCUMENT
    # 返回文档类型
    @classmethod
    def document_type(cls) -> DocumentType:
        """Document type of PDF."""
        return DocumentType.PDF

# PDF 处理器
class PDFProcessor:
    """PDFProcessor class."""
    # 初始化PDF处理器
    def __init__(self, filepath):
        """Initialize PDFProcessor class."""
        self.filepath = filepath
        try:
            import pdfplumber  # type: ignore
        except ImportError:
            raise ImportError("Please install pdfplumber first.")
        self.pdf = pdfplumber.open(filepath)
        self.all_text = defaultdict(dict)
        self.allrow = 0
        self.last_num = 0

        # 添加OCR配置
        self.tesseract_cmd = r'D:\Tesseract-OCR\tesseract.exe'
        self.is_scanned_pdf = None  # Tesseract路径
        
    def is_scanned_document(self, page) -> bool:
        """判断是否为扫描件PDF
        
        通过检查页面是否包含可提取的文本来判断是否为扫描件
        """
        try:
            text = page.extract_text()
            words = page.extract_words()
            # 如果提取不到文本或文本极少，认为是扫描件
            if not text or not words or len(words) < 5:
                return True
            return False
        except Exception as e:
            logger.warning(f"判断PDF类型时发生错误: {str(e)}")
            return True  # 发生错误时默认作为扫描件处理

    def clean_text(self, text):
        """清理和格式化文本"""
        # 移除不必要的字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,，。:：()（）\-]', '', text)
        # 移除多余的空格
        text = re.sub(r'\s+', ' ', text.strip())
        # 进一步清理可能的乱码
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s.,，。:：()（）\-]', '', text)
        # 尝试修复常见的OCR错误
        text = text.replace('虱', '是').replace('振', '数').replace('探', '文')
        return text

    def process_image_ocr(self, image) -> str:
        """处理图片OCR."""
        try:
            # 设置Tesseract路径
            if not os.path.exists(self.tesseract_cmd):
                logger.warning(f"Tesseract路径不存在: {self.tesseract_cmd}")
                return ""
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            # 使用更严格的OCR配置
            custom_config = r'--oem 3 --psm 4'  # 使用LSTM OCR引擎，假设是稀疏文本
            text = pytesseract.image_to_string(image, lang='chi_sim+eng', config=custom_config)
            return self.clean_text(text.strip())
        except Exception as e:
            logger.warning(f"OCR处理失败: {str(e)}")
            return ""
    
    def process_scanned_page(self, page, page_number):
        """处理扫描页面."""
        try:
            # 将页面转换为图片
            images = convert_from_path(self.filepath, dpi=300, poppler_path=r'E:\poppler-23.07.0\Library\bin')
            for i, image in enumerate(images):
                # OCR处理
                ocr_text = self.process_image_ocr(image)
                if ocr_text:
                    # 按行分割OCR结果
                    text_lines = ocr_text.split('\n')
                    for line in text_lines:
                        if line.strip():  # 只添加非空行
                            self.all_text[self.allrow] = {
                                "page": page_number,
                                "allrow": self.allrow,
                                "type": "text",  # 使用统一的text类型
                                "inside": line.strip(),
                            }
                            self.allrow += 1
        except Exception as e:
            logger.error(f"扫描页面处理失败: {str(e)}")
            # 记录更详细的错误信息
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")

    # 检查并处理页面中的文本行
    def check_lines(self, page, top, buttom):
        """Check lines."""
        lines = page.extract_words()[::]    # 提取页面中的所有单词
        text = ""
        last_top = 0    # 上一行顶部位置
        last_check = 0  # 上一行检查位置
        for line in range(len(lines)):
            each_line = lines[line]
            # 使用正则表达式检查行尾是否符合特定格式
            check_re = (
                "(?:。|；|单位：人民币元|金额单位：人民币元|单位：万元|币种：人民币|\d|"
                "报告(?:全文)?(?:（修订版）|（修订稿）|（更正后）)?)$"
            )
            if top == "" and buttom == "":
                if abs(last_top - each_line["top"]) <= 2 or (
                    last_check > 0
                    and (page.height * 0.9 - each_line["top"]) > 0
                    and not re.search(check_re, text)
                ):
                    text = text + each_line["text"]
                else:
                    text = text + "\n" + each_line["text"]
            elif top == "":
                if each_line["top"] > buttom:
                    if abs(last_top - each_line["top"]) <= 2 or (
                        last_check > 0
                        and (page.height * 0.85 - each_line["top"]) > 0
                        and not re.search(check_re, text)
                    ):
                        text = text + each_line["text"]
                    else:
                        text = text + "\n" + each_line["text"]
            else:
                if each_line["top"] < top and each_line["top"] > buttom:
                    if abs(last_top - each_line["top"]) <= 2 or (
                        last_check > 0
                        and (page.height * 0.85 - each_line["top"]) > 0
                        and not re.search(check_re, text)
                    ):
                        text = text + each_line["text"]
                    else:
                        text = text + "\n" + each_line["text"]
            last_top = each_line["top"]
            last_check = each_line["x1"] - page.width * 0.85

        return text
    # 删除空列
    def drop_empty_cols(self, data):
        """Delete empty column."""
        transposed_data = list(map(list, zip(*data)))
        filtered_data = [
            col for col in transposed_data if not all(cell == "" for cell in col)
        ]
        result = list(map(list, zip(*filtered_data)))
        return result
    # 提取文本和表格
    def extract_text_and_tables(self, page):
        """Extract text and tables."""
         # 首先判断是否为扫描件
        if self.is_scanned_pdf is None:
            self.is_scanned_pdf = self.is_scanned_document(page)

        if self.is_scanned_pdf:
            # 扫描件使用OCR处理
            self.process_scanned_page(page, page.page_number)
        else:
            # 原有的文本和表格提取逻辑
            buttom = 0
            tables = page.find_tables()
            buttom = 0
            # 查找页面中所有表格
            tables = page.find_tables()
            if len(tables) >= 1:
                count = len(tables)
                for table in tables:
                    # process text before table
                    if table.bbox[3] < buttom:
                        pass
                    else:
                        count -= 1
                        # process text before table
                        top = table.bbox[1]
                        text = self.check_lines(page, top, buttom)
                        text_list = text.split("\n")
                        for _t in range(len(text_list)):
                            self.all_text[self.allrow] = {
                                "page": page.page_number,
                                "allrow": self.allrow,
                                "type": "text",
                                "inside": text_list[_t],
                            }
                            self.allrow += 1
                        

                        # process table
                        buttom = table.bbox[3]
                        new_table = table.extract()
                        r_count = 0
                        for r in range(len(new_table)):
                            row = new_table[r]
                            if row[0] is None:
                                r_count += 1
                                for c in range(len(row)):
                                    if row[c] is not None and row[c] not in ["", " "]:
                                        if new_table[r - r_count][c] is None:
                                            new_table[r - r_count][c] = row[c]
                                        else:
                                            new_table[r - r_count][c] += row[c]
                                        new_table[r][c] = None
                            else:
                                r_count = 0

                        end_table = []
                        for row in new_table:
                            if row[0] is not None:
                                cell_list = []
                                cell_check = False
                                for cell in row:
                                    if cell is not None:
                                        cell = cell.replace("\n", "")
                                    else:
                                        cell = ""
                                    if cell != "":
                                        cell_check = True
                                    cell_list.append(cell)
                                if cell_check:
                                    end_table.append(cell_list)

                        end_table = self.drop_empty_cols(end_table)

                        # process when column name is empty
                        if len(end_table) > 0:
                            for i in range(len(end_table[0])):
                                if end_table[0][i] == "":
                                    if 0 < i < len(end_table[0]) - 1:
                                        # left column name
                                        left_column = end_table[0][i - 1]
                                        # right column name
                                        right_column = end_table[0][i + 1]
                                        # current name = left name + right name
                                        end_table[0][i] = left_column + right_column
                                    else:
                                        # if current column is empty and is the first
                                        # column, assign the right column name.
                                        # if current column is empty and is the
                                        # last column, assign the left column name.
                                        end_table[0][i] = (
                                            end_table[0][i - 1]
                                            if i == len(end_table[0]) - 1
                                            else end_table[0][i + 1]
                                        )

                        # if the first row is empty, assign the value of the previous row
                        for i in range(1, len(end_table)):
                            for j in range(len(end_table[i])):
                                if end_table[i][j] == "":
                                    end_table[i][j] = end_table[i][j - 1]

                        for row in end_table:
                            self.all_text[self.allrow] = {
                                "page": page.page_number,
                                "allrow": self.allrow,
                                "type": "excel",
                                "inside": str(row),
                            }
                            self.allrow += 1

                        if count == 0:
                            text = self.check_lines(page, "", buttom)
                            text_list = text.split("\n")
                            for _t in range(len(text_list)):
                                self.all_text[self.allrow] = {
                                    "page": page.page_number,
                                    "allrow": self.allrow,
                                    "type": "text",
                                    "inside": text_list[_t],
                                }
                                self.allrow += 1

            else:
                text = self.check_lines(page, "", "")
                text_list = text.split("\n")
                for _t in range(len(text_list)):
                    self.all_text[self.allrow] = {
                        "page": page.page_number,
                        "allrow": self.allrow,
                        "type": "text",
                        "inside": text_list[_t],
                    }
                    self.allrow += 1

        # # 在提取完常规文本和表格后，检查是否需要OCR处理
        # if self.use_ocr:
        #     try:
        #         # 将页面转换为图片
        #         image = page.to_image()
        #         # 获取图片对象
        #         img = Image.open(image.original)
        #         # OCR处理
        #         ocr_text = self.process_image_ocr(img)
        #         if ocr_text:
        #             # 将OCR结果添加到文本中
        #             self.all_text[self.allrow] = {
        #                 "page": page.page_number,
        #                 "allrow": self.allrow,
        #                 "type": "ocr_text",
        #                 "inside": ocr_text,
        #             }
        #             self.allrow += 1
        #     except Exception as e:
        #         logger.warning(f"页面OCR处理失败: {str(e)}")

        # 处理页眉和页脚
        first_re = "[^计](?:报告(?:全文)?(?:（修订版）|（修订稿）|（更正后）)?)$"
        end_re = "^(?:\d|\\|\/|第|共|页|-|_| ){1,}"
        if self.last_num == 0:
            try:
                first_text = str(self.all_text[1]["inside"])
                end_text = str(self.all_text[len(self.all_text) - 1]["inside"])
                if re.search(first_re, first_text) and "[" not in end_text:
                    self.all_text[1]["type"] = "页眉"
                    if re.search(end_re, end_text) and "[" not in end_text:
                        self.all_text[len(self.all_text) - 1]["type"] = "页脚"
            except Exception:
                print(page.page_number)
        else:
            try:
                first_text = str(self.all_text[self.last_num + 2]["inside"])
                end_text = str(self.all_text[len(self.all_text) - 1]["inside"])
                if re.search(first_re, first_text) and "[" not in end_text:
                    self.all_text[self.last_num + 2]["type"] = "页眉"
                if re.search(end_re, end_text) and "[" not in end_text:
                    self.all_text[len(self.all_text) - 1]["type"] = "页脚"
            except Exception:
                print(page.page_number)

        self.last_num = len(self.all_text) - 1
                
    # 将PDF转换为JSON格式
    def pdf_to_json(self):
        """Process pdf."""
        for i in range(len(self.pdf.pages)):
            self.extract_text_and_tables(self.pdf.pages[i])
            logger.info(f"{self.filepath} page {i} extract text success")

    # 保存所有文本  
    def save_all_text(self, path):
        """Save all text."""
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        for key in self.all_text.keys():
            with open(path, "a+", encoding="utf-8") as file:
                file.write(json.dumps(self.all_text[key], ensure_ascii=False) + "\n")
