# -*- coding: utf-8 -*-
"""
会员管理模块 - 对接爱发电(Afdian) API
实现会员方案查询、自动下单、订单轮询自动激活、Webhook处理、会员状态管理

全自动流程（无需手动填订单号）：
1. 用户点击购买 -> create_order_session 生成 custom_order_id 并拼出带 custom_order_id 的爱发电下单链接
2. 用户在新标签页完成支付
3. 前端每 3 秒调用 poll_payment -> 后端用 query-order 接口按 custom_order_id 找到已支付(status=2)的订单
4. 找到后自动激活会员，前端刷新状态
"""

import json
import time
import hashlib
import os
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "afdian_config.json")
MEMBERS_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "members.json")
PENDING_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "pending_orders.json")


class AfdianAPI:
    """爱发电API客户端（开放API：查询订单/赞助者，签名见官方文档）"""

    def __init__(self, config: Dict):
        self.user_id = config.get("user_id", "")
        self.token = config.get("token", "")
        self.api_base = config.get("api_base", "https://ifdian.net/api/open")
        self.slug = config.get("slug", "huihui0420")
        self.profile_url = config.get("profile_url", "https://ifdian.net/a/" + self.slug)

    def _make_sign(self, params: Dict) -> Dict:
        """
        生成签名（爱发电官方算法）：
        sign = md5( token + "params" + params_json + "ts" + ts + "user_id" + user_id )
        params_json 为无空格的紧凑 JSON
        """
        ts = str(int(time.time()))
        params_str = json.dumps(params, ensure_ascii=False, separators=(",", ":"))

        sign_str = "{token}params{params}ts{ts}user_id{user_id}".format(
            token=self.token,
            params=params_str,
            ts=ts,
            user_id=self.user_id
        )

        sign = hashlib.md5(sign_str.encode("utf-8")).hexdigest()
        return {
            "user_id": self.user_id,
            "params": params_str,
            "ts": int(ts),
            "sign": sign
        }

    def _request(self, endpoint: str, params: Dict) -> Dict:
        """发送API请求（form 或 json 均可，官方返回 json）"""
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
        """测试API连通性与签名是否正确"""
        if not self.user_id or not self.token:
            return False
        result = self._request("ping", {"a": 1})
        return result.get("ec") == 200

    def query_order(self, out_trade_no: str = "", page: int = 1, per_page: int = 50) -> Dict:
        """查询订单（按创建时间倒序）"""
        params = {"page": page, "per_page": per_page}
        if out_trade_no:
            params["out_trade_no"] = out_trade_no
        return self._request("query-order", params)

    def query_sponsor(self, user_id: str = "", page: int = 1, per_page: int = 20) -> Dict:
        """查询赞助者"""
        params = {"page": page, "per_page": per_page}
        if user_id:
            params["user_id"] = user_id
        return self._request("query-sponsor", params)

    def find_order_by_custom_id(self, custom_order_id: str, max_pages: int = 5) -> Optional[Dict]:
        """
        在所有订单中按 custom_order_id 查找（最多翻 max_pages 页）
        返回匹配的已支付订单对象或 None
        """
        for page in range(1, max_pages + 1):
            result = self.query_order(page=page)
            if result.get("ec") != 200:
                break
            order_list = result.get("data", {}).get("list", [])
            if not order_list:
                break
            for order in order_list:
                if order.get("custom_order_id") == custom_order_id:
                    return order
            # 翻页到底
            total_page = result.get("data", {}).get("total_page", 1)
            if page >= total_page:
                break
        return None

    def verify_webhook_sign(self, sign_str: str, sign: str) -> bool:
        """
        验证Webhook签名（RSA公钥，SHA256）
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
        self.pending = self._load_pending()

    # ============ 数据加载/保存 ============
    def _load_config(self) -> Dict:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"afdian": {}, "plans": [], "free_limits": {}}

    def _load_members(self) -> Dict:
        if os.path.exists(MEMBERS_DATA_PATH):
            try:
                with open(MEMBERS_DATA_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_members(self):
        os.makedirs(os.path.dirname(MEMBERS_DATA_PATH), exist_ok=True)
        with open(MEMBERS_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(self.members, f, ensure_ascii=False, indent=2)

    def _load_pending(self) -> Dict:
        if os.path.exists(PENDING_DATA_PATH):
            try:
                with open(PENDING_DATA_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_pending(self):
        os.makedirs(os.path.dirname(PENDING_DATA_PATH), exist_ok=True)
        with open(PENDING_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(self.pending, f, ensure_ascii=False, indent=2)

    # ============ 方案/限制 ============
    def get_plans(self) -> List[Dict]:
        return self.plans

    def get_free_limits(self) -> Dict:
        return self.free_limits

    def _get_plan_by_id(self, plan_id: str) -> Optional[Dict]:
        for plan in self.plans:
            if plan["id"] == plan_id:
                return plan
        return None

    def _plan_limits(self, plan_id: str) -> (int, int):
        """返回 (daily_search_limit, max_keywords)"""
        if plan_id == "enterprise":
            return 9999, 999
        elif plan_id == "pro":
            return 100, 5
        elif plan_id == "basic":
            return 30, 1
        return self.free_limits.get("daily_search_limit", 3), self.free_limits.get("max_keywords", 1)

    # ============ 会员信息 ============
    def get_member_info(self, session_id: str) -> Dict:
        # 每次从磁盘加载，保证多进程/重启后状态一致
        self.members = self._load_members()
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

        # 过期检查
        expire_time = member.get("expire_time")
        if expire_time:
            try:
                expire_dt = datetime.fromisoformat(expire_time)
                if datetime.now() > expire_dt:
                    member["level"] = "free"
                    member["plan_name"] = "免费用户(已过期)"
                    member["is_member"] = False
            except:
                pass

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
            "verified_at": member.get("verified_at", ""),
            "auto_activated": member.get("auto_activated", False)
        }

    # ============ 自动下单（核心） ============
    def create_order_session(self, session_id: str, plan_id: str) -> Dict:
        """
        为指定方案创建一笔待支付订单会话
        生成 custom_order_id（绑定到本次 session），拼出爱发电下单链接
        返回 {success, custom_order_id, url, plan}
        """
        plan = self._get_plan_by_id(plan_id)
        if not plan:
            return {"success": False, "message": "方案不存在: " + str(plan_id)}

        afdian_plan_id = plan.get("afdian_plan_id", "")
        if not afdian_plan_id:
            return {"success": False, "message": "该方案未配置爱发电 plan_id"}

        # 生成唯一 custom_order_id（爱发电会把此值原样写回订单数据）
        rand = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        custom_order_id = "{}_{}".format(session_id, rand)

        # 保存待支付记录
        self.pending[session_id] = {
            "custom_order_id": custom_order_id,
            "plan_id": plan_id,
            "created_at": datetime.now().isoformat()
        }
        self._save_pending()

        # 拼爱发电下单链接（带 custom_order_id，支付后可在 query-order 中匹配）
        url = "https://ifdian.net/order/create?plan_id={}&product_type=0&month=1&custom_order_id={}".format(
            afdian_plan_id, custom_order_id
        )

        return {
            "success": True,
            "custom_order_id": custom_order_id,
            "url": url,
            "plan": {
                "id": plan["id"],
                "name": plan["name"],
                "price": plan["price"],
                "period": plan["period"]
            }
        }

    # ============ 轮询支付结果（核心，全自动） ============
    def poll_payment(self, session_id: str) -> Dict:
        """
        轮询爱发电订单，按 session 绑定的 custom_order_id 查找已支付订单
        找到且 status==2 -> 自动激活会员
        返回:
          {status: 'success', member_info, message}
          {status: 'pending'}            尚未支付/未检测到
          {status: 'none'}               该 session 没有待支付记录
          {status: 'error', message}
        """
        pending = self.pending.get(session_id)
        if not pending:
            # 重新从磁盘加载（兼容多进程/重启场景）
            self.pending = self._load_pending()
            pending = self.pending.get(session_id)
        if not pending:
            return {"status": "none"}

        custom_order_id = pending.get("custom_order_id")
        plan_id = pending.get("plan_id")

        # 如果未配置 API 凭证，无法轮询，提示使用本地模式
        if not self.afdian.user_id or not self.afdian.token:
            return {"status": "error", "message": "未配置爱发电 API 凭证，无法自动核验，请在 config 中填写 user_id/token"}

        try:
            order = self.afdian.find_order_by_custom_id(custom_order_id)
        except Exception as e:
            return {"status": "error", "message": "查询爱发电订单失败: " + str(e)}

        if not order:
            return {"status": "pending"}

        # 校验支付状态：2 = 交易成功
        if order.get("status") != 2:
            return {"status": "pending"}

        # 找到已支付订单 -> 激活
        plan = self._get_plan_by_id(plan_id) or self._match_plan_by_amount(float(order.get("total_amount", "0")))
        if not plan:
            return {"status": "error", "message": "支付金额未匹配到会员方案"}

        member_info = self._activate_membership(
            session_id=session_id,
            plan=plan,
            total_amount=float(order.get("total_amount", "0")),
            month=int(order.get("month", 1)),
            order_no=order.get("out_trade_no", ""),
            afdian_user_id=order.get("user_id", ""),
            auto=True
        )

        # 清除待支付记录
        self.pending.pop(session_id, None)
        self._save_pending()

        return {
            "status": "success",
            "message": "支付成功，已自动激活 {}！".format(plan["name"]),
            "member_info": member_info
        }

    # ============ 测试模式：模拟支付成功（仅供本地自测，生产请关闭 test_mode） ============
    def simulate_payment(self, session_id: str) -> Dict:
        """
        模拟爱发电支付成功：直接激活本次会话 pending 订单对应的会员方案。
        用于开发者本机自测「自动激活 + 状态刷新」流程，无需真实付款。
        """
        # 优先从磁盘重新加载，兼容多进程
        self.pending = self._load_pending()
        pending = self.pending.get(session_id)
        if not pending:
            return {"status": "none", "message": "没有待支付订单，请先点击任意会员方案"}

        plan_id = pending.get("plan_id")
        plan = self._get_plan_by_id(plan_id)
        if not plan:
            return {"status": "error", "message": "方案不存在: " + str(plan_id)}

        member_info = self._activate_membership(
            session_id=session_id,
            plan=plan,
            total_amount=float(plan["price"]),
            month=1,
            order_no="SIM_" + "".join(random.choices(string.digits, k=12)),
            afdian_user_id="test_user",
            auto=True
        )
        self.pending.pop(session_id, None)
        self._save_pending()

        return {
            "status": "success",
            "message": "【测试模式】支付成功，已自动激活 {}！".format(plan["name"]),
            "member_info": member_info
        }

    # ============ 激活会员 ============
    def _activate_membership(self, session_id: str, plan: Dict, total_amount: float,
                             month: int, order_no: str, afdian_user_id: str, auto: bool = False) -> Dict:
        """写入会员数据并返回会员信息"""
        month = max(1, int(month))
        expire_time = datetime.now() + timedelta(days=30 * month)
        daily_limit, max_kw = self._plan_limits(plan["id"])

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
            "afdian_user_id": afdian_user_id,
            "daily_search_limit": daily_limit,
            "max_keywords": max_kw,
            "auto_activated": auto
        }

        self.members[session_id] = member_data
        self._save_members()

        logger.info("会员激活成功 - session=%s plan=%s auto=%s", session_id, plan["name"], auto)
        return self.get_member_info(session_id)

    # ============ 手动验证（订单号，保留作为兜底） ============
    def verify_order(self, session_id: str, order_no: str) -> Dict:
        if not self.afdian.user_id or not self.afdian.token:
            return self._local_verify_order(session_id, order_no)

        result = self.afdian.query_order(out_trade_no=order_no)
        if result.get("ec") != 200:
            return {"success": False, "message": "爱发电API查询失败: " + result.get("em", "未知错误")}

        order_list = result.get("data", {}).get("list", [])
        if not order_list:
            return {"success": False, "message": "未找到该订单号，请确认订单号是否正确"}

        order = order_list[0]
        if order.get("status") != 2:
            return {"success": False, "message": "订单未完成支付，请先完成付款"}

        total_amount = float(order.get("total_amount", "0"))
        plan = self._match_plan_by_amount(total_amount)
        if not plan:
            return {"success": False, "message": "支付金额未匹配到任何会员方案（金额: {}元）".format(total_amount)}

        member_info = self._activate_membership(
            session_id=session_id,
            plan=plan,
            total_amount=total_amount,
            month=int(order.get("month", 1)),
            order_no=order_no,
            afdian_user_id=order.get("user_id", ""),
            auto=False
        )
        return {"success": True, "message": "会员验证成功！欢迎 {} 会员".format(plan["name"]), "member_info": member_info}

    def _local_verify_order(self, session_id: str, order_no: str) -> Dict:
        if len(order_no) < 15 or not order_no.replace(",", "").isdigit():
            return {"success": False, "message": "订单号格式不正确，请输入完整的爱发电订单号"}
        expire_time = datetime.now() + timedelta(days=30)
        member_data = {
            "is_member": True, "level": "basic", "plan_name": "基础会员(本地验证)",
            "plan_id": "basic", "order_no": order_no, "amount": 29.0, "month": 1,
            "expire_time": expire_time.isoformat(), "verified_at": datetime.now().isoformat(),
            "afdian_user_id": "", "daily_search_limit": 30, "max_keywords": 1, "local_verified": True
        }
        self.members[session_id] = member_data
        self._save_members()
        return {"success": True, "message": "会员验证成功（本地模式）！已激活基础会员", "member_info": self.get_member_info(session_id)}

    def _match_plan_by_amount(self, amount: float) -> Optional[Dict]:
        for plan in self.plans:
            if abs(plan["price"] - amount) < 0.01:
                return plan
        closest, min_diff = None, float("inf")
        for plan in self.plans:
            diff = abs(plan["price"] - amount)
            if diff < min_diff:
                min_diff, closest = diff, plan
        if closest and min_diff < 5:
            return closest
        return None

    # ============ Webhook ============
    def handle_webhook(self, data: Dict) -> Dict:
        try:
            order = data.get("order", {})
            out_trade_no = order.get("out_trade_no", "")
            custom_order_id = order.get("custom_order_id", "")
            total_amount = float(order.get("total_amount", "0"))
            status = order.get("status", 0)
            month = order.get("month", 1)

            if status != 2:
                return {"ec": 200, "em": "ok"}

            # 优先用 custom_order_id 反查 session
            session_id = None
            for sid, p in self.pending.items():
                if p.get("custom_order_id") == custom_order_id:
                    session_id = sid
                    break
            if not session_id:
                session_id = "afdian_" + out_trade_no

            plan = self._match_plan_by_amount(total_amount)
            if not plan:
                logger.warning("Webhook: 金额未匹配到方案: {}".format(total_amount))
                return {"ec": 200, "em": "ok"}

            self._activate_membership(
                session_id=session_id, plan=plan, total_amount=total_amount,
                month=month, order_no=out_trade_no, afdian_user_id=order.get("user_id", ""), auto=True
            )
            self.pending.pop(session_id, None)
            self._save_pending()
            logger.info("Webhook: 会员激活成功 - {} - {}".format(session_id, plan["name"]))
            return {"ec": 200, "em": "ok"}
        except Exception as e:
            logger.error("Webhook处理失败: {}".format(str(e)))
            return {"ec": 500, "em": str(e)}

    # ============ 权限 ============
    def check_search_permission(self, session_id: str) -> Dict:
        self.members = self._load_members()
        member_info = self.get_member_info(session_id)
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
        """兜底：直接拼下单链接（不带 custom_order_id 也能用，只是无法自动匹配）"""
        plan = self._get_plan_by_id(plan_id)
        if not plan:
            return self.afdian.profile_url
        afdian_plan_id = plan.get("afdian_plan_id", "")
        if afdian_plan_id:
            return "https://ifdian.net/order/create?plan_id={}&product_type=0&month=1".format(afdian_plan_id)
        return self.afdian.profile_url

    def get_leaflet_iframe(self) -> str:
        return '<iframe src="https://ifdian.net/leaflet?slug={}" width="100%" scrolling="no" height="200" frameborder="0"></iframe>'.format(self.afdian.slug)
