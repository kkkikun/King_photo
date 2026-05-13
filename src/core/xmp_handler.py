"""
King_photo - XMP处理模块
处理PNG、WebP、SVG等格式的XMP元信息
"""

import re
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from xml.etree import ElementTree as ET

from ..utils.constants import XMP_TIME_FIELDS, XMP_FIELDS


class XmpHandler:
    """XMP元信息处理器"""

    # XMP命名空间
    NAMESPACES = {
        'xmp': 'http://ns.adobe.com/xap/1.0/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'photoshop': 'http://ns.adobe.com/photoshop/1.0/',
        'tiff': 'http://ns.adobe.com/tiff/1.0/',
        'exif': 'http://ns.adobe.com/exif/1.0/',
        'x': 'adobe:ns:meta/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    }

    @staticmethod
    def read_xmp_from_file(filepath: str) -> Dict[str, Any]:
        """从文件中读取XMP信息"""
        result = {}

        try:
            # 读取文件内容
            with open(filepath, 'rb') as f:
                content = f.read()

            # 提取XMP数据
            xmp_data = XmpHandler._extract_xmp_data(content, filepath)
            if xmp_data:
                result = XmpHandler.parse_xmp(xmp_data)

        except Exception:
            pass

        return result

    @staticmethod
    def _extract_xmp_data(content: bytes, filepath: str) -> Optional[str]:
        """从文件内容中提取XMP数据"""
        ext = os.path.splitext(filepath)[1].lower()

        # XMP包标记
        xmp_start = b'<x:xmpmeta'
        xmp_end = b'</x:xmpmeta>'

        start_idx = content.find(xmp_start)
        if start_idx == -1:
            # 尝试其他标记
            xmp_start = b'<?xpacket begin='
            start_idx = content.find(xmp_start)
            if start_idx == -1:
                return None

        end_idx = content.find(xmp_end, start_idx)
        if end_idx == -1:
            # 尝试查找结束标记
            end_idx = content.find(b'<?xpacket end=', start_idx)
            if end_idx == -1:
                return None
            end_idx = content.find(b'?>', end_idx) + 2
        else:
            end_idx += len(xmp_end)

        try:
            return content[start_idx:end_idx].decode('utf-8', errors='ignore')
        except Exception:
            return None

    @staticmethod
    def parse_xmp(xmp_str: str) -> Dict[str, Any]:
        """解析XMP XML数据"""
        result = {}

        try:
            # 注册命名空间
            for prefix, uri in XmpHandler.NAMESPACES.items():
                ET.register_namespace(prefix, uri)

            # 解析XML
            root = ET.fromstring(xmp_str)

            # 查找RDF元素
            rdf = root.find('.//{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF')
            if rdf is None:
                return result

            # 遍历Description元素
            for desc in rdf.iter('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description'):
                for attr_name, attr_value in desc.attrib.items():
                    # 去掉命名空间前缀
                    clean_name = XmpHandler._clean_attr_name(attr_name)
                    if clean_name:
                        result[clean_name] = attr_value

                # 处理子元素
                for child in desc:
                    clean_name = XmpHandler._clean_attr_name(child.tag)
                    if clean_name:
                        text = child.text or ''
                        # 处理rdf:Alt, rdf:Seq, rdf:Bag
                        if not text:
                            alt = child.find('.//{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li')
                            if alt is not None:
                                text = alt.text or ''
                        if text:
                            result[clean_name] = text

        except ET.ParseError:
            pass

        return result

    @staticmethod
    def _clean_attr_name(name: str) -> Optional[str]:
        """清理属性名，转换为标准格式"""
        # 去掉命名空间URI
        if '{' in name and '}' in name:
            uri, local = name[1:].split('}', 1)
            # 查找对应的前缀
            for prefix, ns_uri in XmpHandler.NAMESPACES.items():
                if uri == ns_uri:
                    return f"{prefix}:{local}"
        return None

    @staticmethod
    def get_datetime(xmp_data: Dict[str, Any]) -> Optional[datetime]:
        """从XMP数据获取时间"""
        for field in XMP_TIME_FIELDS:
            if field in xmp_data:
                dt_str = xmp_data[field]
                dt = XmpHandler._parse_datetime(dt_str)
                if dt:
                    return dt
        return None

    @staticmethod
    def _parse_datetime(dt_str: str) -> Optional[datetime]:
        """解析XMP时间格式"""
        if not dt_str:
            return None

        # XMP标准时间格式
        formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y:%m:%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(dt_str.strip(), fmt)
            except ValueError:
                continue

        return None

    @staticmethod
    def get_basic_info(xmp_data: Dict[str, Any]) -> Dict[str, Any]:
        """从XMP获取基本信息"""
        result = {}

        # 标题
        if 'dc:title' in xmp_data:
            result['title'] = xmp_data['dc:title']

        # 描述
        if 'dc:description' in xmp_data:
            result['description'] = xmp_data['dc:description']

        # 创建者
        if 'dc:creator' in xmp_data:
            result['artist'] = xmp_data['dc:creator']

        # 关键词
        if 'dc:subject' in xmp_data:
            result['keywords'] = xmp_data['dc:subject']

        # 相机信息
        if 'tiff:Make' in xmp_data:
            result['make'] = xmp_data['tiff:Make']

        if 'tiff:Model' in xmp_data:
            result['model'] = xmp_data['tiff:Model']

        # 拍摄参数
        if 'exif:FNumber' in xmp_data:
            result['fnumber'] = xmp_data['exif:FNumber']

        if 'exif:ExposureTime' in xmp_data:
            result['exposure_time'] = xmp_data['exif:ExposureTime']

        if 'exif:ISOSpeedRatings' in xmp_data:
            result['iso'] = xmp_data['exif:ISOSpeedRatings']

        if 'exif:FocalLength' in xmp_data:
            result['focal_length'] = xmp_data['exif:FocalLength']

        return result

    @staticmethod
    def read_xmp_from_png(filepath: str) -> Dict[str, Any]:
        """从PNG文件读取XMP（tEXt/iTXt块）"""
        result = {}

        try:
            with open(filepath, 'rb') as f:
                # 检查PNG签名
                signature = f.read(8)
                if signature != b'\x89PNG\r\n\x1a\n':
                    return result

                while True:
                    # 读取块长度和类型
                    header = f.read(8)
                    if len(header) < 8:
                        break

                    length = int.from_bytes(header[:4], 'big')
                    chunk_type = header[4:8]

                    # 读取块数据
                    chunk_data = f.read(length)

                    # 跳过CRC
                    f.read(4)

                    # 检查是否为文本块
                    if chunk_type in [b'tEXt', b'iTXt']:
                        try:
                            if chunk_type == b'tEXt':
                                # tEXt: keyword\0text
                                parts = chunk_data.split(b'\x00', 1)
                                if len(parts) == 2:
                                    keyword = parts[0].decode('latin-1')
                                    value = parts[1].decode('latin-1')
                                    if keyword == 'XML:com.adobe.xmp':
                                        xmp_data = XmpHandler.parse_xmp(value)
                                        result.update(xmp_data)
                            else:
                                # iTXt: keyword\0compression_flag\0compression_method\0language\0translated_keyword\0text
                                parts = chunk_data.split(b'\x00', 5)
                                if len(parts) >= 6:
                                    keyword = parts[0].decode('latin-1')
                                    if keyword == 'XML:com.adobe.xmp':
                                        text = parts[5].decode('utf-8')
                                        xmp_data = XmpHandler.parse_xmp(text)
                                        result.update(xmp_data)
                        except Exception:
                            continue

        except Exception:
            pass

        return result
