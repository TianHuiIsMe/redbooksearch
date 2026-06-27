"""
医美专属合规模块 - 内置医美行业风控规则
自动识别违规内容、脱敏隐私信息、适配医美强监管场景
"""

import re
from typing import Dict, List, Any
from datetime import datetime


class MedicalAestheticsComplianceChecker:
    """医美合规模查器 - 内置医美行业风控规则"""
    
    def __init__(self):
        # 《广告法》违禁医疗宣传关键词
        self.medical_ad_keywords = [
            # 绝对化用语
            "最有效", "根治", "药到病除", "特效", "100%", "第一",
            "唯一", "最佳", "顶级", "极品", "万能",
            
            # 医疗效果承诺
            "治愈", "根治", "永不复发", "一次性解决",
            "无副作用", "绝对安全", "100%有效",
            
            # 医疗术语（非医疗机构禁止使用）
            "治疗", "治愈", "疗效", "药用", "药方",
            "手术", "注射", "植入", "切除",
        ]
        
        # 夸大功效话术
        self.exaggeration_keywords = [
            "瞬间", "立竿见影", "马上见效", "三天变美",
            "一周年轻十岁", "永久", "终身", "不反弹",
        ]
        
        # 机构联系方式正则
        self.contact_patterns = [
            r'\d{11}',  # 手机号
            r'\d{3,4}-\d{7,8}',  # 座机号
            r'[微信|vx|V信]+[：: ]*\w+',  # 微信号
            r'[QQ|qq]+[：: ]*\d+',  # QQ号
            r'添加.*联系方式',  # 引导添加联系方式
        ]
        
        # 医美项目关键词（用于分类）
        self.medical_projects = {
            "祛斑": ["祛斑", "淡斑", "斑点", "雀斑", "黄褐斑", "老年斑"],
            "抗衰": ["抗衰老", "抗衰", "除皱", "祛皱", "年轻化", "紧致"],
            "水光": ["水光针", "水光", "玻尿酸", "保湿", "补水"],
            "隆鼻": ["隆鼻", "垫鼻", "鼻综合", "鼻整形"],
            "双眼皮": ["双眼皮", "重睑", "眼部整形"],
            "瘦脸": ["瘦脸", "削骨", "V脸", "小脸"],
            "丰胸": ["丰胸", "隆胸", "胸部整形"],
            "吸脂": ["吸脂", "抽脂", "减肥", "塑形"],
        }
        
        # 用户痛点关键词
        self.user_pain_points = [
            "疼不疼", "痛不痛", "副作用", "风险", "后遗症",
            "恢复期", "停工", "消肿", "淤青",
            "效果维持", "反弹", "失效",
        ]
        
        # 人群标签
        self.user_tags = {
            "年龄": ["20岁", "30岁", "40岁", "50岁", "年轻", "中年", "中老年"],
            "性别": ["男士", "女士", "男性", "女性"],
            "需求强度": ["想做", "打算", "考虑", "咨询", "预约"],
        }
    
    def check_compliance(self, note: Dict) -> Dict:
        """
        检查笔记合规性
        返回：{
            "is_compliant": bool,  # 是否合规
            "risk_level": str,  # 风险等级：high/medium/low
            "violations": [],  # 违规项
            "suggestions": [],  # 改进建议
        }
        """
        title = note.get("title", "")
        content = note.get("content", "")
        text = title + " " + content
        
        result = {
            "is_compliant": True,
            "risk_level": "low",
            "violations": [],
            "suggestions": []
        }
        
        # 1. 检查《广告法》违禁医疗宣传
        for keyword in self.medical_ad_keywords:
            if keyword in text:
                result["is_compliant"] = False
                result["risk_level"] = "high"
                result["violations"].append(f"包含违禁词：{keyword}")
                result["suggestions"].append(f"建议删除或替换：{keyword}")
        
        # 2. 检查夸大功效话术
        for keyword in self.exaggeration_keywords:
            if keyword in text:
                result["risk_level"] = "medium" if result["risk_level"] == "low" else result["risk_level"]
                result["violations"].append(f"包含夸大功效话术：{keyword}")
                result["suggestions"].append(f"建议修改为更客观的描述")
        
        # 3. 检查机构联系方式（需要脱敏）
        for pattern in self.contact_patterns:
            matches = re.findall(pattern, text)
            if matches:
                result["violations"].append(f"包含联系方式，需要脱敏")
                result["suggestions"].append(f"建议脱敏处理联系方式")
        
        return result
    
    def extract_medical_projects(self, note: Dict) -> List[str]:
        """提取医美项目标签"""
        title = note.get("title", "")
        content = note.get("content", "")
        text = title + " " + content
        
        projects = []
        for project, keywords in self.medical_projects.items():
            for keyword in keywords:
                if keyword in text:
                    projects.append(project)
                    break
        
        return list(set(projects))  # 去重
    
    def extract_user_pain_points(self, note: Dict) -> List[str]:
        """提取用户痛点"""
        content = note.get("content", "")
        
        pain_points = []
        for point in self.user_pain_points:
            if point in content:
                pain_points.append(point)
        
        return pain_points
    
    def extract_user_tags(self, note: Dict) -> Dict:
        """提取用户人群标签"""
        content = note.get("content", "")
        
        tags = {
            "age_group": [],
            "gender": [],
            "intent_level": "low"
        }
        
        # 年龄
        for age in self.user_tags["年龄"]:
            if age in content:
                tags["age_group"].append(age)
        
        # 性别
        for gender in self.user_tags["性别"]:
            if gender in content:
                tags["gender"].append(gender)
        
        # 需求强度
        for intent in self.user_tags["需求强度"]:
            if intent in content:
                if intent in ["想做", "预约"]:
                    tags["intent_level"] = "high"
                elif intent in ["打算", "考虑"]:
                    tags["intent_level"] = "medium"
                else:
                    tags["intent_level"] = "low"
        
        return tags
    
    def desensitize_content(self, note: Dict) -> Dict:
        """
        脱敏处理：隐藏机构联系方式
        """
        content = note.get("content", "")
        
        # 脱敏手机号
        content = re.sub(r'\d{11}', '***手机号已脱敏***', content)
        
        # 脱敏座机号
        content = re.sub(r'\d{3,4}-\d{7,8}', '***电话已脱敏***', content)
        
        # 脱敏微信号
        content = re.sub(r'[微信|vx|V信]+[：: ]*\w+', '***微信已脱敏***', content)
        
        # 脱敏QQ号
        content = re.sub(r'[QQ|qq]+[：: ]*\d+', '***QQ已脱敏***', content)
        
        note["content"] = content
        return note
    
    def generate_compliance_report(self, notes: List[Dict]) -> Dict:
        """生成合规报告"""
        total = len(notes)
        compliant_count = 0
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        
        violations_summary = {}
        
        for note in notes:
            check_result = self.check_compliance(note)
            
            if check_result["is_compliant"]:
                compliant_count += 1
                low_risk_count += 1
            else:
                if check_result["risk_level"] == "high":
                    high_risk_count += 1
                elif check_result["risk_level"] == "medium":
                    medium_risk_count += 1
                
                # 统计违规项
                for violation in check_result["violations"]:
                    violations_summary[violation] = violations_summary.get(violation, 0) + 1
        
        return {
            "total_notes": total,
            "compliant_notes": compliant_count,
            "compliance_rate": compliant_count / total * 100 if total > 0 else 0,
            "risk_distribution": {
                "high": high_risk_count,
                "medium": medium_risk_count,
                "low": low_risk_count
            },
            "common_violations": violations_summary,
            "recommendations": [
                "建议定期审查内容合规性",
                "建议对高风险内容进行人工复核",
                "建议建立合规关键词库并持续更新"
            ]
        }


class MedicalAestheticsAnalyzer:
    """医美行业专属分析器 - 集成合规模查"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.compliance_checker = MedicalAestheticsComplianceChecker()
        
        # 初始化AI分析器
        from ai.content_analyzer import ContentAnalyzer
        self.ai_analyzer = ContentAnalyzer(config)
    
    def analyze_medical_notes(self, notes: List[Dict], memory: Any) -> Dict:
        """
        分析医美笔记（集成合规性检查）
        """
        print(f"[{datetime.now().isoformat()}] [INFO] 开始医美专属分析 {len(notes)} 条笔记")
        
        # 1. 合规性检查
        print(f"[{datetime.now().isoformat()}] [INFO] 步骤1: 合规性检查")
        compliance_results = []
        for note in notes:
            compliance_result = self.compliance_checker.check_compliance(note)
            compliance_results.append(compliance_result)
            
            # 脱敏处理
            note = self.compliance_checker.desensitize_content(note)
        
        # 2. 提取医美项目标签
        print(f"[{datetime.now().isoformat()}] [INFO] 步骤2: 提取医美项目标签")
        for i, note in enumerate(notes):
            projects = self.compliance_checker.extract_medical_projects(note)
            note["medical_projects"] = projects
        
        # 3. 提取用户痛点
        print(f"[{datetime.now().isoformat()}] [INFO] 步骤3: 提取用户痛点")
        for note in notes:
            pain_points = self.compliance_checker.extract_user_pain_points(note)
            note["user_pain_points"] = pain_points
        
        # 4. 提取用户人群标签
        print(f"[{datetime.now().isoformat()}] [INFO] 步骤4: 提取用户人群标签")
        for note in notes:
            user_tags = self.compliance_checker.extract_user_tags(note)
            note["user_tags"] = user_tags
        
        # 5. AI内容分析（调用原有分析器）
        print(f"[{datetime.now().isoformat()}] [INFO] 步骤5: AI内容分析")
        ai_analysis_result = self.ai_analyzer.analyze_content(notes, memory)
        
        # 6. 生成合规报告
        print(f"[{datetime.now().isoformat()}] [INFO] 步骤6: 生成合规报告")
        compliance_report = self.compliance_checker.generate_compliance_report(notes)
        
        # 整合结果
        result = {
            "total_notes": len(notes),
            "compliance_report": compliance_report,
            "ai_analysis": ai_analysis_result,
            "medical_insights": self._generate_medical_insights(notes)
        }
        
        print(f"[{datetime.now().isoformat()}] [INFO] 医美专属分析完成")
        
        return result
    
    def _generate_medical_insights(self, notes: List[Dict]) -> List[str]:
        """生成医美行业洞察"""
        insights = []
        
        # 统计热门医美项目
        project_counts = {}
        for note in notes:
            projects = note.get("medical_projects", [])
            for project in projects:
                project_counts[project] = project_counts.get(project, 0) + 1
        
        if project_counts:
            top_project = max(project_counts.items(), key=lambda x: x[1])
            insights.append(f"最热门的医美项目是：{top_project[0]}，提及{top_project[1]}次")
        
        # 统计用户痛点
        pain_point_counts = {}
        for note in notes:
            pain_points = note.get("user_pain_points", [])
            for point in pain_points:
                pain_point_counts[point] = pain_point_counts.get(point, 0) + 1
        
        if pain_point_counts:
            insights.append(f"用户最关心的痛点是：{list(pain_point_counts.keys())[:3]}")
        
        # 统计人群分布
        age_groups = []
        for note in notes:
            tags = note.get("user_tags", {})
            age_groups.extend(tags.get("age_group", []))
        
        if age_groups:
            from collections import Counter
            top_age = Counter(age_groups).most_common(1)[0]
            insights.append(f"主要受众年龄层：{top_age[0]}")
        
        return insights


if __name__ == "__main__":
    # 测试代码
    config = {
        "model_provider": "dashscope",
        "base_model": "deepseek-v3",
        "validation_model": "qwen-max",
        "api_key": "YOUR_API_KEY_HERE"
    }
    
    checker = MedicalAestheticsComplianceChecker()
    
    test_note = {
        "title": "祛斑最有效的办法，100%根治黄褐斑",
        "content": "大家好，今天分享祛斑心得，联系电话：13812345678，微信号：beauty123"
    }
    
    result = checker.check_compliance(test_note)
    print("合规检查结果：", result)
    
    desensitized = checker.desensitize_content(test_note)
    print("脱敏后内容：", desensitized)
