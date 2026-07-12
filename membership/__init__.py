# -*- coding: utf-8 -*-
"""
membership package - 会员管理系统
对接爱发电(Afdian)实现会员支付、验证、权限管理
"""

from .membership_manager import MembershipManager, AfdianAPI

__all__ = ["MembershipManager", "AfdianAPI"]
