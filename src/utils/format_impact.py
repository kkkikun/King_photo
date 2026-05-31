"""
格式影响查询工具模块
"""
import json
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# 缓存已加载的规则
_rules_cache: Optional[List[dict]] = None
_levels_cache: Optional[Dict[str, dict]] = None


def _get_config_path() -> str:
    """获取配置文件路径"""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'config', 'format_impact.json'
    )


def _load_rules() -> None:
    """加载格式影响规则配置（缓存在全局变量中）"""
    global _rules_cache, _levels_cache
    if _rules_cache is not None:
        return

    config_path = _get_config_path()
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            _levels_cache = data.get('impact_levels', {})
            _rules_cache = data.get('rules', [])
            logger.info(f"格式影响规则已加载: {config_path} ({len(_rules_cache)} 条规则)")
        else:
            logger.warning(f"格式影响配置文件不存在: {config_path}")
            _rules_cache = []
            _levels_cache = {}
    except Exception as e:
        logger.error(f"加载格式影响规则失败: {e}")
        _rules_cache = []
        _levels_cache = {}


def reload_rules() -> None:
    """重新加载规则"""
    global _rules_cache, _levels_cache
    _rules_cache = None
    _levels_cache = None
    _load_rules()


def get_impact(real_format: str, disguised_as: str) -> dict:
    """
    获取格式影响信息
    
    Args:
        real_format: 真实格式 (如 'HEIF')
        disguised_as: 伪装成的格式 (如 'PNG')
    
    Returns:
        {
            'level': 'CRITICAL'|'HIGH'|'MEDIUM'|'LOW'|'NONE',
            'reason': '影响原因描述',
            'recommend_fix': bool
        }
    """
    _load_rules()
    
    for rule in _rules_cache:
        if rule['real'].upper() == real_format.upper():
            if rule['disguised'] == '*' or rule['disguised'].upper() == disguised_as.upper():
                level = rule['impact']
                recommend = _levels_cache.get(level, {}).get('recommend_fix', False)
                return {
                    'level': level,
                    'reason': rule['reason'],
                    'recommend_fix': recommend
                }
    
    # 默认：无法判断
    return {
        'level': 'MEDIUM',
        'reason': '格式不匹配，影响程度未知',
        'recommend_fix': False
    }


def should_prompt_user(real_format: str, disguised_as: str) -> bool:
    """
    判断是否需要弹窗询问用户
    影响级别 >= HIGH 时弹窗
    """
    impact = get_impact(real_format, disguised_as)
    return impact['level'] in ('CRITICAL', 'HIGH')


def get_default_action(real_format: str, disguised_as: str) -> str:
    """
    获取默认处理建议
    Returns: 'fix' | 'skip'
    """
    impact = get_impact(real_format, disguised_as)
    return 'fix' if impact['recommend_fix'] else 'skip'


def get_impact_level_info(level: str) -> dict:
    """获取影响级别描述"""
    _load_rules()
    return _levels_cache.get(level, {})
