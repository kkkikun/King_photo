"""
King_photo - XMP处理模块
处理PNG、WebP、SVG等格式的XMP元信息
"""

import re
import os
import zlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from xml.etree import ElementTree as ET

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from ..utils.constants import XMP_TIME_FIELDS, XMP_FIELDS

# 获取日志记录器
logger = logging.getLogger(__name__)


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

        except Exception as e:
            logger.error(f"读取XMP数据失败: {filepath}, 错误: {str(e)}")

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
        except Exception as e:
            logger.error(f"解码XMP数据失败: {str(e)}")
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
                        except Exception as e:
                            logger.warning(f"解析PNG文本块失败: {str(e)}")
                            continue

        except Exception as e:
            logger.error(f"读取PNG XMP数据失败: {str(e)}")

        return result

    @staticmethod
    def write_xmp(filepath: str, metadata: Dict[str, Any]) -> bool:
        """
        写入XMP元信息到文件

        Args:
            filepath: 文件路径
            metadata: 要写入的元信息字典

        Returns:
            是否写入成功
        """
        try:
            ext = os.path.splitext(filepath)[1].lower()

            # 根据文件格式选择写入方法
            if ext == '.png':
                return XmpHandler.write_xmp_to_png(filepath, metadata)
            elif ext in ['.jpg', '.jpeg']:
                # JPEG文件优先使用EXIF，XMP作为补充
                # 这里返回False让调用者使用EXIF写入
                return False
            elif ext == '.webp':
                # WebP格式支持XMP写入
                return XmpHandler.write_xmp_to_webp(filepath, metadata)
            elif ext in ['.tif', '.tiff']:
                # TIFF格式暂时不支持XMP写入
                return False
            elif ext == '.svg':
                # SVG格式使用属性方式存储XMP
                return XmpHandler.write_xmp_to_svg(filepath, metadata)
            else:
                return False

        except Exception as e:
            logger.error(f"写入XMP元信息失败: {filepath}, 错误: {str(e)}")
            return False

    @staticmethod
    def write_xmp_to_webp(filepath: str, metadata: Dict[str, Any]) -> bool:
        """
        写入XMP元信息到WebP文件

        Args:
            filepath: WebP文件路径
            metadata: 要写入的元信息字典

        Returns:
            是否写入成功
        """
        try:
            # WebP格式通过exiftool写入XMP更可靠
            from ..utils.exiftool_wrapper import get_exiftool
            et = get_exiftool()
            if not et.is_available:
                logger.warning("ExifTool不可用，无法写入WebP XMP信息")
                return False
            
            # 构建XMP字符串
            xmp_str = XmpHandler._build_xmp_string(metadata)
            if not xmp_str:
                return False
            
            # 使用exiftool写入XMP数据
            # exiftool可以处理WebP格式的XMP元数据
            success = et.write_metadata(filepath, {'XMP': xmp_str})
            if success:
                logger.info(f"使用exiftool成功写入WebP XMP信息: {filepath}")
                return True
            else:
                # 尝试使用copy_filetime_to_exif方法
                logger.warning(f"exiftool写入WebP XMP失败，尝试使用copy_filetime_to_exif: {filepath}")
                return et.copy_filetime_to_exif(filepath)
            
        except Exception as e:
            logger.error(f"写入WebP XMP元信息失败: {filepath}, 错误: {str(e)}")
            return False

    @staticmethod
    def write_xmp_to_png(filepath: str, metadata: Dict[str, Any]) -> bool:
        """
        写入XMP元信息到PNG文件

        Args:
            filepath: PNG文件路径
            metadata: 要写入的元信息字典

        Returns:
            是否写入成功
        """
        try:
            # 预检查：验证文件是否存在、非空、且有PNG文件头
            if not os.path.exists(filepath):
                logger.warning(f"写入PNG XMP元信息失败: 文件不存在: {filepath}")
                return False
            
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                logger.warning(f"写入PNG XMP元信息失败: 文件为空: {filepath}")
                return False
            
            # 检查PNG文件头（89 50 4E 47 0D 0A 1A 0A）
            with open(filepath, 'rb') as f:
                header = f.read(8)
            if header != b'\x89PNG\r\n\x1a\n':
                logger.warning(f"写入PNG XMP元信息失败: 文件不是有效的PNG格式: {filepath}")
                return False

            # 读取现有PNG文件
            img = Image.open(filepath)

            # 构建XMP XML字符串
            xmp_str = XmpHandler._build_xmp_string(metadata)
            if not xmp_str:
                return False

            # 创建PngInfo对象
            pnginfo = PngInfo()

            # 保留现有的非XMP文本块，并从img.info中移除旧XMP数据
            xmp_keywords = ['XML:com.adobe.xmp', 'xmp']
            if hasattr(img, 'info') and img.info:
                for key, value in img.info.items():
                    if isinstance(value, str) and key not in xmp_keywords:
                        pnginfo.add_text(key, value)
                # 从img.info中移除旧的XMP数据，防止img.save()保留旧块
                for key in xmp_keywords:
                    if key in img.info:
                        del img.info[key]

            # 添加新的XMP数据
            pnginfo.add_text('XML:com.adobe.xmp', xmp_str)

            # 保存文件
            img.save(filepath, pnginfo=pnginfo)

            return True

        except Exception as e:
            logger.error(f"写入PNG XMP元信息失败: {filepath}, 错误: {str(e)}")
            return False

    @staticmethod
    def write_xmp_to_svg(filepath: str, metadata: Dict[str, Any]) -> bool:
        """
        写入XMP元信息到SVG文件

        Args:
            filepath: SVG文件路径
            metadata: 要写入的元信息字典

        Returns:
            是否写入成功
        """
        try:
            # 读取SVG文件内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 构建XMP XML字符串
            xmp_str = XmpHandler._build_xmp_string(metadata)
            if not xmp_str:
                return False

            # 查找并替换或添加XMP metadata元素
            xmp_pattern = r'<metadata[^>]*>.*?</metadata>'
            xmp_match = re.search(xmp_pattern, content, re.DOTALL)

            # 构建完整的metadata元素
            metadata_element = f'<metadata id="xmp">\n{xmp_str}\n</metadata>'

            if xmp_match:
                # 替换现有的metadata元素
                content = content[:xmp_match.start()] + metadata_element + content[xmp_match.end():]
            else:
                # 在svg元素内添加metadata
                svg_pattern = r'(<svg[^>]*>)'
                svg_match = re.search(svg_pattern, content)
                if svg_match:
                    insert_pos = svg_match.end()
                    content = content[:insert_pos] + '\n' + metadata_element + content[insert_pos:]
                else:
                    return False

            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            return True

        except Exception as e:
            logger.error(f"写入SVG XMP元信息失败: {filepath}, 错误: {str(e)}")
            return False

    @staticmethod
    def _build_xmp_string(metadata: Dict[str, Any]) -> Optional[str]:
        """
        构建XMP XML字符串

        Args:
            metadata: 元信息字典

        Returns:
            XMP XML字符串，失败返回None
        """
        try:
            # 注册命名空间
            for prefix, uri in XmpHandler.NAMESPACES.items():
                ET.register_namespace(prefix, uri)

            # 创建根元素
            xmpmeta = ET.Element('{adobe:ns:meta/}xmpmeta')

            # 创建RDF元素
            rdf = ET.SubElement(xmpmeta, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF')

            # 创建Description元素
            desc = ET.SubElement(rdf, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description')
            desc.set('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about', '')

            # 字段映射：通用名 -> XMP名（不同格式共用）
            # XMP标准命名空间参考: https://www.exiftool.org/TagNames/XMP.html
            field_mapping = {
                # 时间相关（不同命名空间存储不同类型的时间）
                'datetime': 'xmp:ModifyDate',          # 文件修改时间
                'datetime_original': 'photoshop:DateCreated',  # 拍摄时间（PNG等纯XMP格式的标准字段）
                'datetime_digitized': 'xmp:CreateDate',  # 数字化时间/创建时间
                'creation_time': 'xmp:CreateDate',     # 文件创建时间
                # 描述相关（dc命名空间）
                'title': 'dc:title',
                'description': 'dc:description',
                'artist': 'dc:creator',
                'keywords': 'dc:subject',
                'copyright': 'dc:rights',
                # 相机信息（tiff命名空间 - PNG/WebP等纯XMP格式使用）
                'make': 'tiff:Make',
                'model': 'tiff:Model',
                'software': 'tiff:Software',
                'orientation': 'tiff:Orientation',
                # 拍摄参数（exif命名空间 - 在XMP中映射EXIF字段）
                'lens': 'exif:LensModel',
                'exposure_time': 'exif:ExposureTime',
                'fnumber': 'exif:FNumber',
                'iso': 'exif:ISOSpeedRatings',
                'focal_length': 'exif:FocalLength',
            }

            # 写入元信息
            for key, value in metadata.items():
                if value is None:
                    continue

                xmp_key = field_mapping.get(key, key)

                # 解析命名空间和本地名
                if ':' in xmp_key:
                    prefix, local = xmp_key.split(':', 1)
                    if prefix in XmpHandler.NAMESPACES:
                        ns_uri = XmpHandler.NAMESPACES[prefix]
                        full_key = f'{{{ns_uri}}}{local}'

                        # 特殊处理dc:creator和dc:subject（需要rdf:Seq结构）
                        if xmp_key in ['dc:creator', 'dc:subject']:
                            seq = ET.SubElement(desc, full_key)
                            rdf_seq = ET.SubElement(seq, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Seq')
                            li = ET.SubElement(rdf_seq, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li')
                            li.text = str(value)
                        # 特殊处理时间字段
                        elif 'Date' in local or 'Time' in local:
                            if isinstance(value, datetime):
                                value = value.strftime('%Y-%m-%dT%H:%M:%S')
                            elif isinstance(value, str):
                                # 转换EXIF时间格式 (YYYY:MM:DD HH:MM:SS) 到ISO 8601 (YYYY-MM-DDTHH:MM:SS)
                                if re.match(r'\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}', value):
                                    value = value.replace(':', '-', 2).replace(' ', 'T', 1)
                            desc.set(full_key, str(value))
                        else:
                            desc.set(full_key, str(value))

            # 转换为字符串
            ET.indent(xmpmeta, space='  ')
            xmp_bytes = ET.tostring(xmpmeta, encoding='unicode', xml_declaration=False)

            # 添加XMP包头尾
            xmp_packet = '<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
            xmp_packet += xmp_bytes + '\n'
            xmp_packet += '<?xpacket end="w"?>'

            return xmp_packet

        except Exception as e:
            logger.error(f"构建XMP XML字符串失败: {str(e)}")
            return None

    @staticmethod
    def update_xmp(filepath: str, metadata: Dict[str, Any]) -> bool:
        """
        更新现有XMP元信息（保留原有数据）

        Args:
            filepath: 文件路径
            metadata: 要更新的元信息字典

        Returns:
            是否更新成功
        """
        try:
            # 读取现有XMP数据
            existing_data = XmpHandler.read_xmp_from_file(filepath)

            # 合并数据（新数据覆盖旧数据）
            merged_data = {**existing_data, **metadata}

            # 写入合并后的数据
            return XmpHandler.write_xmp(filepath, merged_data)

        except Exception as e:
            logger.error(f"更新XMP元信息失败: {filepath}, 错误: {str(e)}")
            return False
