"""
CRM集成模块 - 将调研数据自动同步至医美CRM系统
支持Webhook回调、线索标签自动打标、话术库更新
"""

import json
import requests
from typing import Dict, List, Any
from datetime import datetime
from enum import Enum


class CRMIntegrationType(Enum):
    """CRM集成类型"""
    WEBHOOK = "webhook"  # Webhook回调
    API = "api"  # REST API
    FILE = "file"  # 文件导出


class MedicalCRMIntegrator:
    """医美CRM集成器 - 将调研数据同步至CRM系统"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.integration_type = config.get("crm_integration_type", "webhook")
        self.webhook_url = config.get("crm_webhook_url", "")
        self.api_endpoint = config.get("crm_api_endpoint", "")
        self.api_key = config.get("crm_api_key", "")
        
    def sync_to_crm(self, analysis_result: Dict, notes: List[Dict]) -> Dict:
        """
        将调研数据同步至CRM系统
        返回同步结果
        """
        print(f"[{datetime.now().isoformat()}] [INFO] 开始同步数据至CRM系统")
        
        sync_result = {
            "success": False,
            "synced_leads": 0,
            "synced_tags": 0,
            "synced_insights": 0,
            "errors": []
        }
        
        try:
            # 1. 提取线索数据
            leads = self._extract_leads(notes)
            
            # 2. 提取标签数据
            tags = self._extract_tags(analysis_result)
            
            # 3. 提取洞察数据
            insights = self._extract_insights(analysis_result)
            
            # 4. 根据集成类型同步
            if self.integration_type == CRMIntegrationType.WEBHOOK.value:
                sync_result = self._sync_via_webhook(leads, tags, insights)
            elif self.integration_type == CRMIntegrationType.API.value:
                sync_result = self._sync_via_api(leads, tags, insights)
            elif self.integration_type == CRMIntegrationType.FILE.value:
                sync_result = self._sync_via_file(leads, tags, insights)
            else:
                raise Exception(f"不支持的集成类型: {self.integration_type}")
            
            print(f"[{datetime.now().isoformat()}] [INFO] CRM同步完成")
            print(f"  同步线索数: {sync_result['synced_leads']}")
            print(f"  同步标签数: {sync_result['synced_tags']}")
            print(f"  同步洞察数: {sync_result['synced_insights']}")
            
            return sync_result
            
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] [ERROR] CRM同步失败: {str(e)}")
            sync_result["errors"].append(str(e))
            return sync_result
    
    def _extract_leads(self, notes: List[Dict]) -> List[Dict]:
        """
        从笔记中提取线索数据
        线索定义：有潜在医美需求的用户
        """
        leads = []
        
        for note in notes:
            # 判断是否为潜在线索
            is_lead = self._is_potential_lead(note)
            
            if is_lead:
                lead = {
                    "source": "小红书",
                    "note_id": note.get("note_id", ""),
                    "note_url": note.get("url", ""),
                    "author": note.get("author", ""),
                    "title": note.get("title", ""),
                    "content": note.get("content", ""),
                    "tags": note.get("medical_projects", []),  # 医美项目标签
                    "user_tags": note.get("user_tags", {}),  # 用户人群标签
                    "pain_points": note.get("user_pain_points", []),  # 用户痛点
                    "intent_level": self._calculate_intent_level(note),  # 意向度
                    "engagement": {
                        "likes": note.get("likes", 0),
                        "comments": note.get("comments", 0),
                        "collects": note.get("collects", 0)
                    },
                    "collected_at": datetime.now().isoformat()
                }
                leads.append(lead)
        
        return leads
    
    def _is_potential_lead(self, note: Dict) -> bool:
        """判断是否为潜在线索"""
        # 规则1：包含医美项目关键词
        if note.get("medical_projects", []):
            return True
        
        # 规则2：包含咨询类关键词
        content = note.get("content", "")
        consult_keywords = ["怎么", "多少钱", "哪里", "推荐", "有没有", "建议"]
        for keyword in consult_keywords:
            if keyword in content:
                return True
        
        # 规则3：高互动数（说明关注度高）
        likes = note.get("likes", 0)
        comments = note.get("comments", 0)
        if likes > 100 or comments > 20:
            return True
        
        return False
    
    def _calculate_intent_level(self, note: Dict) -> str:
        """计算用户意向度"""
        content = note.get("content", "")
        
        # 高意向关键词
        high_intent = ["想做", "预约", "咨询", "多少钱", "哪里可以做"]
        for keyword in high_intent:
            if keyword in content:
                return "high"
        
        # 中意向关键词
        medium_intent = ["考虑", "打算", "了解", "怎么样"]
        for keyword in medium_intent:
            if keyword in content:
                return "medium"
        
        return "low"
    
    def _extract_tags(self, analysis_result: Dict) -> List[Dict]:
        """提取标签数据（用于自动打标）"""
        tags = []
        
        # 从分析结果中提取热门项目标签
        medical_insights = analysis_result.get("medical_insights", [])
        for insight in medical_insights:
            if "最热门的医美项目" in insight:
                # 解析项目名称
                project = insight.split("：")[1].split("，")[0]
                tags.append({
                    "tag_name": project,
                    "tag_type": "medical_project",
                    "priority": "high"
                })
        
        # 添加人群标签
        tags.append({
            "tag_name": "小红书用户",
            "tag_type": "source",
            "priority": "medium"
        })
        
        return tags
    
    def _extract_insights(self, analysis_result: Dict) -> List[Dict]:
        """提取洞察数据（用于更新话术库）"""
        insights = []
        
        # 用户痛点洞察
        pain_points = analysis_result.get("medical_insights", [])
        for point in pain_points:
            if "痛点" in point:
                insights.append({
                    "type": "user_pain_point",
                    "content": point,
                    "action": "update_script"  # 更新话术库
                })
        
        # 热门项目洞察
        hot_projects = analysis_result.get("medical_insights", [])
        for project in hot_projects:
            if "最热门" in project:
                insights.append({
                    "type": "hot_project",
                    "content": project,
                    "action": "create_campaign"  # 创建营销活动
                })
        
        return insights
    
    def _sync_via_webhook(self, leads: List[Dict], tags: List[Dict], insights: List[Dict]) -> Dict:
        """通过Webhook同步数据"""
        if not self.webhook_url:
            raise Exception("未配置Webhook URL")
        
        sync_result = {
            "success": False,
            "synced_leads": 0,
            "synced_tags": 0,
            "synced_insights": 0,
            "errors": []
        }
        
        try:
            # 构造Webhook payload
            payload = {
                "event_type": "xiaohongshu_research_complete",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "leads": leads,
                    "tags": tags,
                    "insights": insights
                }
            }
            
            # 发送Webhook请求
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                sync_result["success"] = True
                sync_result["synced_leads"] = len(leads)
                sync_result["synced_tags"] = len(tags)
                sync_result["synced_insights"] = len(insights)
            else:
                sync_result["errors"].append(f"Webhook请求失败: {response.status_code}")
            
            return sync_result
            
        except Exception as e:
            sync_result["errors"].append(str(e))
            return sync_result
    
    def _sync_via_api(self, leads: List[Dict], tags: List[Dict], insights: List[Dict]) -> Dict:
        """通过REST API同步数据"""
        # 类似Webhook实现
        pass
    
    def _sync_via_file(self, leads: List[Dict], tags: List[Dict], insights: List[Dict]) -> Dict:
        """通过文件导出同步数据"""
        sync_result = {
            "success": True,
            "synced_leads": len(leads),
            "synced_tags": len(tags),
            "synced_insights": len(insights),
            "errors": [],
            "export_files": []
        }
        
        # 导出线索数据
        leads_file = f"data/outputs/crm_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(leads_file, "w", encoding="utf-8") as f:
            json.dump(leads, f, ensure_ascii=False, indent=2)
        sync_result["export_files"].append(leads_file)
        
        # 导出标签数据
        tags_file = f"data/outputs/crm_tags_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(tags_file, "w", encoding="utf-8") as f:
            json.dump(tags, f, ensure_ascii=False, indent=2)
        sync_result["export_files"].append(tags_file)
        
        # 导出洞察数据
        insights_file = f"data/outputs/crm_insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(insights_file, "w", encoding="utf-8") as f:
            json.dump(insights, f, ensure_ascii=False, indent=2)
        sync_result["export_files"].append(insights_file)
        
        return sync_result


class ScriptLibraryUpdater:
    """话术库更新器 - 根据调研洞察自动更新咨询师话术库"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.script_library = []
    
    def update_script_library(self, insights: List[Dict]) -> Dict:
        """
        根据洞察更新话术库
        """
        print(f"[{datetime.now().isoformat()}] [INFO] 开始更新话术库")
        
        update_result = {
            "updated_scripts": 0,
            "new_scripts": 0,
            "scripts": []
        }
        
        for insight in insights:
            if insight["type"] == "user_pain_point":
                # 根据用户痛点生成话术
                script = self._generate_script_from_pain_point(insight["content"])
                self.script_library.append(script)
                update_result["new_scripts"] += 1
                update_result["scripts"].append(script)
        
        print(f"[{datetime.now().isoformat()}] [INFO] 话术库更新完成，新增{update_result['new_scripts']}条话术")
        
        return update_result
    
    def _generate_script_from_pain_point(self, pain_point: str) -> Dict:
        """根据用户痛点生成话术"""
        # 简单的话术生成逻辑（实际应调用AI生成）
        script = {
            "script_id": f"SCRIPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "pain_point": pain_point,
            "response_script": f"针对{pain_point}，建议话术：...",  # 这里应调用AI生成
            "created_at": datetime.now().isoformat(),
            "usage_count": 0
        }
        
        return script
    
    def export_script_library(self, output_file: str):
        """导出话术库"""
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.script_library, f, ensure_ascii=False, indent=2)
        
        print(f"[{datetime.now().isoformat()}] [INFO] 话术库已导出至: {output_file}")


if __name__ == "__main__":
    # 测试代码
    config = {
        "crm_integration_type": "webhook",
        "crm_webhook_url": "https://your-crm-system.com/webhook",
        "crm_api_endpoint": "",
        "crm_api_key": ""
    }
    
    integrator = MedicalCRMIntegrator(config)
    
    # 测试数据
    test_notes = [
        {
            "note_id": "123",
            "title": "祛斑分享",
            "content": "想做祛斑，哪里好？",
            "medical_projects": ["祛斑"],
            "user_pain_points": ["疼不疼"],
            "likes": 150,
            "comments": 30
        }
    ]
    
    # 测试同步
    result = integrator.sync_to_crm({"medical_insights": []}, test_notes)
    print("同步结果：", result)
