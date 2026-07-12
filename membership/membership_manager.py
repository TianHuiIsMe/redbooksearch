# -*- coding: utf-8 -*-
"""
会员管理模块 - 对接爱发电(Afdian) API
实现会员方案查询、订单验证、Webhook处理、会员状态管理
"""

import json
import time
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "afdian_config.json")
MEMBERS_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "members.json")


class AfdianAPI:
    """爱发电API客户端"""

    def __init__(self, config: Dict):
        self.user_id = config.get("user_id", "")
        self.token = config.get("token", "")
        self.api_base = config.get("api_base", "https://ifdian.net/api/open")
        self.slug = config.get("slug", "huihui0420")
        self.profile_url = config.get("profile_url", "https://ifdian.net/a/" + self.slug)

    def _make_sign(self, params: Dict) -> str:
        """
        生成签名
        sign = md5(token + params{json} + ts{ts} + user_id{user_id})
        """
        ts = str(int(time.time()))
        params_str = json.dumps(params, ensure_ascii=False, separators=(",", ":"))

        # 拼接签名串
        sign_str = "{}params{}ts{}user_id{}".format(
            self.token, params_str, ts, self.user_id
        )

        sign = hashlib.md5(sign_str.encode("utf-8")).hexdigest()
        return {
            "user_id": self.user_id,
            "params": params_str,
            "ts": int(ts),
            "sign": sign
        }

    def _request(self, endpoint: str, params: Dict) -> Dict:
        """发送API请求"""
        import requests

        url = "{}/{}".format(self.api_base, endpoint)
        payload = self._make_sign(params)

        try:
            resp = requests.post(url, json=payload, timeout=15)
            return resp.json()
        except Exception as e:
            logger.error("Afdian API请求失败: {} - {}".format(endpoint, str(e)))
            return {"ec": 500, "em": str(e), "data": None}

    def ping(self) -> bool:
        """测试API连通性"""
        if not self.user_id or not self.token:
            return False
        result = self._request("ping", {"a": 1})
        return result.get("ec") == 200

    def query_order(self, out_trade_no: str = "", page: int = 1, per_page: int = 50) -> Dict:
        """查询订单"""
        params = {"page": page}
        if out_trade_no:
            params["out_trade_no"] = out_trade_no
        if per_page:
            params["per_page"] = per_page
        return self._request("query-order", params)

    def query_sponsor(self, user_id: str = "", page: int = 1, per_page: int = 20) -> Dict:
        """查询赞助者"""
        params = {"page": page}
        if user_id:
            params["user_id"] = user_id
        if per_page:
            params["per_page"] = per_page
        return self._request("query-sponsor", params)

    def query_plan(self, plan_id: str) -> Dict:
        """查询方案详情"""
        return self._request("query-plan", {"plan_id": plan_id})

    def verify_webhook_sign(self, sign_str: str, sign: str) -> bool:
        """
        验证Webhook签名
        使用RSA公钥验证
        """
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            import base64

            public_key_pem = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwwdaCg1Bt+UKZKs0R54y
lYnuANma49IpgoOwNmk3a0rhg/PQuhUJ0EOZSowIC44l0K3+fqGns3Ygi4AfmEfS
4EKbdk1ahSxu7Zkp2rHMt+R9GarQFQkwSS/5x1dYiHNVMiR8oIXDgjmvxuNes2Cr
8fw9dEF0xNBKdkKgG2qAawcN1nZrdyaKWtPVT9m2Hl0ddOO9thZmVLFOb9NVzgYf
jEgI+KWX6aY19Ka/ghv/L4t1IXmz9pctablN5S0CRWpJW3Cn0k6zSXgjVdKm4uN7
jRlgSRaf/Ind46vMCm3N2sgwxu/g3bnooW+db0iLo13zzuvyn727Q3UDQ0MmZcEW
MQIDAQAB
-----END PUBLIC KEY-----"""

            public_key = serialization.load_pem_public_key(public_key_pem.encode())
            sign_bytes = base64.b64decode(sign)

            public_key.verify(
                sign_bytes,
                sign_str.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            logger.warning("Webhook签名验证失败: {}".format(str(e)))
            return False


class MembershipManager:
    """会员管理器"""

    def __init__(self):
        self.config = self._load_config()
        self.afdian = AfdianAPI(self.config.get("afdian", {}))
        self.plans = self.config.get("plans", [])
        self.free_limits = self.config.get("free_limits", {})
        self.members = self._load_members()

    def _load_config(self) -> Dict:
        """加载配置"""
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"afdian": {}, "plans": [], "free_limits": {}}

    def _load_members(self) -> Dict:
        """加载会员数据"""
        if os.path.exists(MEMBERS_DATA_PATH):
            try:
                with open(MEMBERS_DATA_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_members(self):
        """保存会员数据"""
        os.makedirs(os.path.dirname(MEMBERS_DATA_PATH), exist_ok=True)
        with open(MEMBERS_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(self.members, f, ensure_ascii=False, indent=2)

    def get_plans(self) -> List[Dict]:
        """获取会员方案列表"""
        return self.plans

    def get_free_limits(self) -> Dict:
        """获取免费用户限制"""
        return self.free_limits

    def get_member_info(self, session_id: str) -> Dict:
        """获取会员信息"""
        member = self.members.get(session_id)

        if not member:
            return {
                "is_member": False,
                "level": "free",
                "plan_name": "免费用户",
                "features": [],
                "daily_search_limit": self.free_limits.get("daily_search_limit", 3),
                "max_keywords": self.free_limits.get("max_keywords", 1),
                "expire_time": None,
                "afdian_profile": self.afdian.profile_url
            }

        # 检查是否过期
        expire_time = member.get("expire_time")
        if expire_time:
            expire_dt = datetime.fromisoformat(expire_time)
            if datetime.now() > expire_dt:
                # 会员已过期
                member["level"] = "free"
                member["plan_name"] = "免费用户(已过期)"
                member["is_member"] = False

        # 补充方案信息
        plan_id = member.get("plan_id", "free")
        plan_info = self._get_plan_by_id(plan_id)

        return {
            "is_member": member.get("is_member", False),
            "level": member.get("level", "free"),
            "plan_name": member.get("plan_name", "免费用户"),
            "features": plan_info.get("features", []) if plan_info else [],
            "daily_search_limit": member.get("daily_search_limit", self.free_limits.get("daily_search_limit", 3)),
            "max_keywords": member.get("max_keywords", self.free_limits.get("max_keywords", 1)),
            "expire_time": member.get("expire_time"),
            "afdian_profile": self.afdian.profile_url,
            "order_no": member.get("order_no", ""),
            "verified_at": member.get("verified_at", "")
        }

    def _get_plan_by_id(self, plan_id: str) -> Optional[Dict]:
        """根据ID获取方案"""
        for plan in self.plans:
            if plan["id"] == plan_id:
                return plan
        return None

    def verify_order(self, session_id: str, order_no: str) -> Dict:
        """
        通过订单号验证会员
        调用爱发电API查询订单，验证通过后激活会员
        """
        # 如果没有配置API凭证，使用本地验证模式
        if not self.afdian.user_id or not self.afdian.token:
            return self._local_verify_order(session_id, order_no)

        # 调用API查询订单
        result = self.afdian.query_order(out_trade_no=order_no)

        if result.get("ec") != 200:
            return {
                "success": False,
                "message": "爱发电API查询失败: " + result.get("em", "未知错误")
            }

        order_list = result.get("data", {}).get("list", [])

        if not order_list:
            return {
                "success": False,
                "message": "未找到该订单号，请确认订单号是否正确"
            }

        order = order_list[0]

        # 检查订单状态 (2 = 交易成功)
        if order.get("status") != 2:
            return {
                "success": False,
                "message": "订单未完成支付，请先完成付款"
            }

        # 根据金额判断会员等级
        total_amount = float(order.get("total_amount", "0"))
        plan = self._match_plan_by_amount(total_amount)

        if not plan:
            return {
                "success": False,
                "message": "支付金额未匹配到任何会员方案（金额: {}元）".format(total_amount)
            }

        # 激活会员
        month = order.get("month", 1)
        expire_time = datetime.now() + timedelta(days=30 * month)

        member_data = {
            "is_member": True,
            "level": plan["id"],
            "plan_name": plan["name"],
            "plan_id": plan["id"],
            "order_no": order_no,
            "amount": total_amount,
            "month": month,
            "expire_time": expire_time.isoformat(),
            "verified_at": datetime.now().isoformat(),
            "afdian_user_id": order.get("user_id", ""),
            "daily_search_limit": 999 if plan["id"] == "enterprise" else (100 if plan["id"] == "pro" else 30),
            "max_keywords": 999 if plan["id"] == "enterprise" else (5 if plan["id"] == "pro" else 1)
        }

        self.members[session_id] = member_data
        self._save_members()

        return {
            "success": True,
            "message": "会员验证成功！欢迎 {} 会员".format(plan["name"]),
            "member_info": self.get_member_info(session_id)
        }

    def _local_verify_order(self, session_id: str, order_no: str) -> Dict:
        """
        本地验证模式（未配置API凭证时使用）
        通过订单号格式简单验证
        """
        # 爱发电订单号格式: 21位数字
        if len(order_no) < 15 or not order_no.replace(",", "").isdigit():
            return {
                "success": False,
                "message": "订单号格式不正确，请输入完整的爱发电订单号"
            }

        # 本地模式：直接激活基础会员（仅用于演示）
        # 实际使用时请在 config/afdian_config.json 中配置 user_id 和 token
        expire_time = datetime.now() + timedelta(days=30)

        member_data = {
            "is_member": True,
            "level": "basic",
            "plan_name": "基础会员(本地验证)",
            "plan_id": "basic",
            "order_no": order_no,
            "amount": 29.0,
            "month": 1,
            "expire_time": expire_time.isoformat(),
            "verified_at": datetime.now().isoformat(),
            "afdian_user_id": "",
            "daily_search_limit": 30,
            "max_keywords": 1,
            "local_verified": True
        }

        self.members[session_id] = member_data
        self._save_members()

        return {
            "success": True,
            "message": "会员验证成功（本地模式）！已激活基础会员，有效期30天",
            "member_info": self.get_member_info(session_id)
        }

    def _match_plan_by_amount(self, amount: float) -> Optional[Dict]:
        """根据支付金额匹配会员方案"""
        for plan in self.plans:
            if abs(plan["price"] - amount) < 0.01:
                return plan
        # 如果没有精确匹配，找最接近的
        closest = None
        min_diff = float("inf")
        for plan in self.plans:
            diff = abs(plan["price"] - amount)
            if diff < min_diff:
                min_diff = diff
                closest = plan
        # 如果差距在5元以内，也算匹配
        if closest and min_diff < 5:
            return closest
        return None

    def handle_webhook(self, data: Dict) -> Dict:
        """
        处理爱发电Webhook回调
        """
        try:
            order = data.get("order", {})

            out_trade_no = order.get("out_trade_no", "")
            custom_order_id = order.get("custom_order_id", "")
            total_amount = float(order.get("total_amount", "0"))
            status = order.get("status", 0)
            month = order.get("month", 1)

            if status != 2:
                return {"ec": 200, "em": "ok"}

            # 匹配会员方案
            plan = self._match_plan_by_amount(total_amount)
            if not plan:
                logger.warning("Webhook: 金额未匹配到方案: {}".format(total_amount))
                return {"ec": 200, "em": "ok"}

            # 如果有custom_order_id，用作session_id
            session_id = custom_order_id if custom_order_id else "afdian_" + out_trade_no

            expire_time = datetime.now() + timedelta(days=30 * month)

            member_data = {
                "is_member": True,
                "level": plan["id"],
                "plan_name": plan["name"],
                "plan_id": plan["id"],
                "order_no": out_trade_no,
                "amount": total_amount,
                "month": month,
                "expire_time": expire_time.isoformat(),
                "verified_at": datetime.now().isoformat(),
                "afdian_user_id": order.get("user_id", ""),
                "daily_search_limit": 999 if plan["id"] == "enterprise" else (100 if plan["id"] == "pro" else 30),
                "max_keywords": 999 if plan["id"] == "enterprise" else (5 if plan["id"] == "pro" else 1)
            }

            self.members[session_id] = member_data
            self._save_members()

            logger.info("Webhook: 会员激活成功 - {} - {}".format(session_id, plan["name"]))

            return {"ec": 200, "em": "ok"}

        except Exception as e:
            logger.error("Webhook处理失败: {}".format(str(e)))
            return {"ec": 500, "em": str(e)}

    def check_search_permission(self, session_id: str) -> Dict:
        """检查搜索权限"""
        member_info = self.get_member_info(session_id)

        # 检查每日搜索次数
        today = datetime.now().strftime("%Y-%m-%d")
        member = self.members.get(session_id, {})
        search_history = member.get("search_history", {})
        today_count = search_history.get(today, 0)

        daily_limit = member_info.get("daily_search_limit", 3)

        if today_count >= daily_limit:
            return {
                "allowed": False,
                "reason": "今日搜索次数已达上限({}/{})".format(today_count, daily_limit),
                "member_info": member_info
            }

        # 增加搜索计数
        if session_id not in self.members:
            self.members[session_id] = {}
        if "search_history" not in self.members[session_id]:
            self.members[session_id]["search_history"] = {}
        self.members[session_id]["search_history"][today] = today_count + 1
        self._save_members()

        return {
            "allowed": True,
            "remaining": daily_limit - today_count - 1,
            "member_info": member_info
        }

    def get_purchase_url(self, plan_id: str, session_id: str = "") -> str:
        """获取购买链接"""
        plan = self._get_plan_by_id(plan_id)
        if not plan:
            return self.afdian.profile_url

        afdian_plan_id = plan.get("afdian_plan_id", "")

        if afdian_plan_id:
            # 直接跳转到指定方案的购买页
            url = "https://ifdian.net/order/create?plan_id={}&product_type=0".format(afdian_plan_id)
            if session_id:
                url += "&custom_order_id={}".format(session_id)
            return url
        else:
            # 跳转到爱发电主页
            return self.afdian.profile_url

    def get_leaflet_iframe(self) -> str:
        """获取嵌入iframe代码"""
        return '<iframe src="https://ifdian.net/leaflet?slug={}" width="100%" scrolling="no" height="200" frameborder="0"></iframe>'.format(self.afdian.slug)
