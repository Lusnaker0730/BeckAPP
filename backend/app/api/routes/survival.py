"""
Survival Analysis API Endpoints

提供存活分析功能的 API 端點
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np
from io import BytesIO
import base64
import logging

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.core.cache import cache_result
from app.models.fhir_resources import Patient, Condition, Encounter
from app.models.survival_analysis import SurvivalCohort, SurvivalEvent

# Survival analysis libraries
try:
    from lifelines import KaplanMeierFitter, CoxPHFitter
    from lifelines.statistics import logrank_test, multivariate_logrank_test
    import matplotlib
    matplotlib.use('Agg')  # 使用非交互式後端
    import matplotlib.pyplot as plt
    plt.style.use('seaborn-v0_8-darkgrid')
    SURVIVAL_AVAILABLE = True
except ImportError:
    SURVIVAL_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger(__name__)


def convert_numpy_types(obj):
    """將 numpy 類型轉換為 Python 原生類型，以便 JSON 序列化"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        val = float(obj)
        # 處理無限大和NaN值
        if np.isnan(val) or np.isinf(val):
            return None
        return val
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, float):
        # 也處理普通的Python float
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    return obj


# ============================================================================
# Kaplan-Meier 存活分析
# ============================================================================

@router.get("/kaplan-meier")
@cache_result(expire_seconds=1800, key_prefix="survival_km")
async def kaplan_meier_analysis(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    diagnosis_code: Optional[str] = Query(None, description="診斷代碼或文字"),
    start_date: Optional[str] = Query(None, description="開始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="結束日期 YYYY-MM-DD"),
    max_follow_up_days: int = Query(1825, description="最大追蹤天數（預設5年）"),
    stratify_by: Optional[str] = Query(None, description="分層變數: gender, age_group")
):
    """
    Kaplan-Meier 存活分析
    
    計算並返回 Kaplan-Meier 存活曲線數據
    """
    if not SURVIVAL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Survival analysis libraries not available. Please install lifelines."
        )
    
    try:
        # 構建查詢
        query = db.query(
            Condition.patient_id,
            Condition.onset_datetime,
            Patient.gender,
            Patient.birth_date
        ).join(
            Patient, Condition.patient_id == Patient.fhir_id
        )
        
        # 應用過濾條件
        if diagnosis_code:
            query = query.filter(Condition.code_text.ilike(f'%{diagnosis_code}%'))
        
        if start_date:
            query = query.filter(Condition.onset_datetime >= start_date)
        
        if end_date:
            query = query.filter(Condition.onset_datetime <= end_date)
        
        # 獲取數據
        results = query.all()
        
        if not results:
            # 查詢該診斷的實際數據範圍
            if diagnosis_code:
                date_range_query = db.query(
                    func.min(Condition.onset_datetime).label('min_date'),
                    func.max(Condition.onset_datetime).label('max_date'),
                    func.count(Condition.id).label('total_records')
                ).filter(Condition.code_text.ilike(f'%{diagnosis_code}%'))
                
                date_range = date_range_query.first()
                
                if date_range and date_range.total_records > 0:
                    return {
                        "error": "no_data_in_range",
                        "message": f"在所選時間範圍內找不到數據。該診斷共有 {date_range.total_records} 筆記錄，時間範圍為 {date_range.min_date.strftime('%Y-%m-%d')} 至 {date_range.max_date.strftime('%Y-%m-%d')}。",
                        "suggestion": f"請調整開始日期為 {date_range.min_date.strftime('%Y-%m-%d')} 或更早，結束日期為 {date_range.max_date.strftime('%Y-%m-%d')} 或更晚。",
                        "actual_date_range": {
                            "start": date_range.min_date.isoformat(),
                            "end": date_range.max_date.isoformat(),
                            "total_records": date_range.total_records
                        }
                    }
            
            return {
                "error": "no_data_found",
                "message": "找不到符合條件的數據。",
                "suggestion": "請嘗試：1) 更改診斷條件 2) 擴大時間範圍 3) 檢查診斷代碼是否正確"
            }
        
        # 準備數據
        data = []
        current_time = datetime.now(timezone.utc)
        
        for record in results:
            if record.onset_datetime:
                # 計算存活時間（天數）
                duration = (current_time - record.onset_datetime).days
                duration = min(duration, max_follow_up_days)
                
                # 計算年齡組
                age_group = "Unknown"
                if record.birth_date:
                    # 將 date 轉換為 datetime 以進行計算
                    birth_datetime = datetime.combine(record.birth_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                    age = (current_time - birth_datetime).days / 365.25
                    if age < 18:
                        age_group = "<18"
                    elif age < 40:
                        age_group = "18-39"
                    elif age < 60:
                        age_group = "40-59"
                    else:
                        age_group = "60+"
                
                data.append({
                    'patient_id': record.patient_id,
                    'duration': duration,
                    'event': 0,  # 預設為審查（censored），因為我們沒有死亡數據
                    'gender': record.gender or "Unknown",
                    'age_group': age_group
                })
        
        df = pd.DataFrame(data)
        
        # Kaplan-Meier 分析
        if stratify_by and stratify_by in df.columns:
            # 分層分析
            groups = df[stratify_by].unique()
            results_by_group = {}
            
            for group in groups:
                group_df = df[df[stratify_by] == group]
                kmf = KaplanMeierFitter()
                kmf.fit(
                    durations=group_df['duration'],
                    event_observed=group_df['event'],
                    label=str(group)
                )
                
                # 安全地提取中位存活时间
                median_survival = kmf.median_survival_time_
                if median_survival is not None and not (np.isnan(median_survival) or np.isinf(median_survival)):
                    median_survival = float(median_survival)
                else:
                    median_survival = None
                
                results_by_group[str(group)] = {
                    'timeline': [float(x) if not (np.isnan(x) or np.isinf(x)) else None for x in kmf.survival_function_.index.tolist()],
                    'survival_probability': [float(x) if not (np.isnan(x) or np.isinf(x)) else None for x in kmf.survival_function_[str(group)].tolist()],
                    'confidence_interval_lower': [float(x) if not (np.isnan(x) or np.isinf(x)) else None for x in kmf.confidence_interval_[f'{group}_lower_0.95'].tolist()],
                    'confidence_interval_upper': [float(x) if not (np.isnan(x) or np.isinf(x)) else None for x in kmf.confidence_interval_[f'{group}_upper_0.95'].tolist()],
                    'median_survival': median_survival,
                    'sample_size': int(len(group_df))
                }
            
            # 進行 Log-rank 檢驗
            if len(groups) == 2:
                group1 = df[df[stratify_by] == groups[0]]
                group2 = df[df[stratify_by] == groups[1]]
                
                logrank_result = logrank_test(
                    durations_A=group1['duration'],
                    durations_B=group2['duration'],
                    event_observed_A=group1['event'],
                    event_observed_B=group2['event']
                )
                
                # 安全地提取统计值
                test_stat = logrank_result.test_statistic
                p_val = logrank_result.p_value
                
                statistical_test = {
                    'test': 'Log-rank test',
                    'statistic': float(test_stat) if not (np.isnan(test_stat) or np.isinf(test_stat)) else None,
                    'p_value': float(p_val) if not (np.isnan(p_val) or np.isinf(p_val)) else None,
                    'significant': bool(p_val < 0.05) if not (np.isnan(p_val) or np.isinf(p_val)) else False
                }
            else:
                statistical_test = None
            
            return convert_numpy_types({
                'analysis_type': 'kaplan_meier_stratified',
                'stratified_by': stratify_by,
                'groups': results_by_group,
                'statistical_test': statistical_test,
                'total_patients': len(df),
                'max_follow_up_days': max_follow_up_days
            })
        
        else:
            # 整體分析
            kmf = KaplanMeierFitter()
            kmf.fit(
                durations=df['duration'],
                event_observed=df['event'],
                label='Overall'
            )
            
            # 安全地提取中位存活时间
            median_survival = kmf.median_survival_time_
            if median_survival is not None and not (np.isnan(median_survival) or np.isinf(median_survival)):
                median_survival = float(median_survival)
            else:
                median_survival = None
            
            return convert_numpy_types({
                'analysis_type': 'kaplan_meier_overall',
                'timeline': [float(x) if not (np.isnan(x) or np.isinf(x)) else None for x in kmf.survival_function_.index.tolist()],
                'survival_probability': [float(x) if not (np.isnan(x) or np.isinf(x)) else None for x in kmf.survival_function_['Overall'].tolist()],
                'confidence_interval_lower': [float(x) if not (np.isnan(x) or np.isinf(x)) else None for x in kmf.confidence_interval_['Overall_lower_0.95'].tolist()],
                'confidence_interval_upper': [float(x) if not (np.isnan(x) or np.isinf(x)) else None for x in kmf.confidence_interval_['Overall_upper_0.95'].tolist()],
                'median_survival_days': median_survival,
                'total_patients': int(len(df)),
                'events_observed': int(df['event'].sum()),
                'censored': int((df['event'] == 0).sum()),
                'max_follow_up_days': int(max_follow_up_days)
            })
    
    except HTTPException:
        raise  # 重新抛出 HTTPException
    except Exception as e:
        logger.error(f"Error in Kaplan-Meier analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


# ============================================================================
# Kaplan-Meier 可視化
# ============================================================================

@router.get("/kaplan-meier/plot")
async def kaplan_meier_plot(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    diagnosis_code: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    max_follow_up_days: int = Query(1825),
    stratify_by: Optional[str] = Query(None)
):
    """
    生成 Kaplan-Meier 存活曲線圖
    
    返回 base64 編碼的圖片
    """
    if not SURVIVAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="Survival analysis not available")
    
    try:
        # 獲取數據（與上面相同的邏輯）
        query = db.query(
            Condition.patient_id,
            Condition.onset_datetime,
            Patient.gender,
            Patient.birth_date
        ).join(Patient, Condition.patient_id == Patient.fhir_id)
        
        if diagnosis_code:
            query = query.filter(Condition.code_text.ilike(f'%{diagnosis_code}%'))
        if start_date:
            query = query.filter(Condition.onset_datetime >= start_date)
        if end_date:
            query = query.filter(Condition.onset_datetime <= end_date)
        
        results = query.all()
        
        if not results:
            # 查詢該診斷的實際數據範圍
            error_detail = "No data found for the specified criteria"
            if diagnosis_code:
                date_range_query = db.query(
                    func.min(Condition.onset_datetime).label('min_date'),
                    func.max(Condition.onset_datetime).label('max_date'),
                    func.count(Condition.id).label('total_records')
                ).filter(Condition.code_text.ilike(f'%{diagnosis_code}%'))
                
                date_range = date_range_query.first()
                
                if date_range and date_range.total_records > 0:
                    error_detail = f"在所選時間範圍內找不到數據。該診斷共有 {date_range.total_records} 筆記錄，時間範圍為 {date_range.min_date.strftime('%Y-%m-%d')} 至 {date_range.max_date.strftime('%Y-%m-%d')}。請調整時間範圍。"
            
            raise HTTPException(status_code=404, detail=error_detail)
        
        # 準備數據
        data = []
        current_time = datetime.now(timezone.utc)
        
        for record in results:
            if record.onset_datetime:
                duration = min((current_time - record.onset_datetime).days, max_follow_up_days)
                
                age_group = "Unknown"
                if record.birth_date:
                    # 將 date 轉換為 datetime 以進行計算
                    birth_datetime = datetime.combine(record.birth_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                    age = (current_time - birth_datetime).days / 365.25
                    if age < 18:
                        age_group = "<18"
                    elif age < 40:
                        age_group = "18-39"
                    elif age < 60:
                        age_group = "40-59"
                    else:
                        age_group = "60+"
                
                data.append({
                    'duration': duration,
                    'event': 0,
                    'gender': record.gender or "Unknown",
                    'age_group': age_group
                })
        
        df = pd.DataFrame(data)
        
        # 創建圖表，使用白色背景以提高可讀性
        fig, ax = plt.subplots(figsize=(12, 7), facecolor='white')
        ax.set_facecolor('white')
        
        # 設置中文字體（嘗試多種常見字體）
        try:
            import matplotlib.font_manager as fm
            # 嘗試使用系統中的中文字體
            chinese_fonts = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'WenQuanYi Micro Hei']
            for font_name in chinese_fonts:
                try:
                    plt.rcParams['font.sans-serif'] = [font_name]
                    break
                except:
                    continue
            plt.rcParams['axes.unicode_minus'] = False  # 解決負號顯示問題
        except:
            pass
        
        # 定義顏色方案（更鮮明的顏色）
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#06A77D', '#D90368']
        
        if stratify_by and stratify_by in df.columns:
            # 分層繪圖
            for idx, group in enumerate(df[stratify_by].unique()):
                group_df = df[df[stratify_by] == group]
                kmf = KaplanMeierFitter()
                kmf.fit(
                    durations=group_df['duration'],
                    event_observed=group_df['event'],
                    label=str(group)
                )
                kmf.plot_survival_function(
                    ax=ax, 
                    ci_show=True, 
                    color=colors[idx % len(colors)],
                    linewidth=2.5,
                    alpha=0.8
                )
        else:
            # 整體繪圖
            kmf = KaplanMeierFitter()
            kmf.fit(durations=df['duration'], event_observed=df['event'], label='Overall Survival')
            kmf.plot_survival_function(
                ax=ax, 
                ci_show=True, 
                color='#2E86AB',
                linewidth=2.5,
                alpha=0.8
            )
        
        # 設置標籤和標題（使用英文避免字體問題）
        ax.set_xlabel('Follow-up Time (Days)', fontsize=14, fontweight='bold', color='#2c3e50')
        ax.set_ylabel('Survival Probability', fontsize=14, fontweight='bold', color='#2c3e50')
        ax.set_title('Kaplan-Meier Survival Curve', fontsize=16, fontweight='bold', color='#2c3e50', pad=20)
        
        # 改善網格和圖例
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
        ax.legend(loc='best', frameon=True, shadow=True, fontsize=11, fancybox=True)
        
        # 設置坐標軸範圍和刻度
        ax.set_ylim([-0.05, 1.05])
        ax.tick_params(labelsize=11, colors='#2c3e50')
        
        # 添加邊框
        for spine in ax.spines.values():
            spine.set_edgecolor('#2c3e50')
            spine.set_linewidth(1.2)
        
        # 轉換為 base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return {
            'image': f'data:image/png;base64,{image_base64}',
            'format': 'png',
            'total_patients': len(df)
        }
    
    except HTTPException:
        raise  # 重新抛出 HTTPException，不要捕获它
    except Exception as e:
        logger.error(f"Error generating KM plot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Cox 比例風險模型
# ============================================================================

@router.get("/cox-regression")
async def cox_proportional_hazards(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    diagnosis_code: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    max_follow_up_days: int = Query(1825)
):
    """
    Cox 比例風險模型分析
    
    評估不同變數對存活的影響（風險比 Hazard Ratio）
    """
    if not SURVIVAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="Survival analysis not available")
    
    try:
        # 獲取數據
        query = db.query(
            Condition.patient_id,
            Condition.onset_datetime,
            Patient.gender,
            Patient.birth_date
        ).join(Patient, Condition.patient_id == Patient.fhir_id)
        
        if diagnosis_code:
            query = query.filter(Condition.code_text.ilike(f'%{diagnosis_code}%'))
        if start_date:
            query = query.filter(Condition.onset_datetime >= start_date)
        if end_date:
            query = query.filter(Condition.onset_datetime <= end_date)
        
        results = query.all()
        
        if len(results) < 10:
            return {
                'error': 'insufficient_data',
                'message': f'數據不足：找到 {len(results)} 位患者，Cox 回歸分析至少需要 10 位患者。',
                'suggestion': '請嘗試：1) 擴大時間範圍 2) 移除或更改診斷條件 3) 使用 Kaplan-Meier 分析（對樣本量要求較低）',
                'total_patients': len(results),
                'min_required': 10
            }
        
        # 準備數據
        data = []
        current_time = datetime.now(timezone.utc)
        
        for record in results:
            if record.onset_datetime and record.birth_date:
                duration = min((current_time - record.onset_datetime).days, max_follow_up_days)
                # 將 date 轉換為 datetime 以進行計算
                birth_datetime = datetime.combine(record.birth_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                age = (record.onset_datetime - birth_datetime).days / 365.25
                
                data.append({
                    'duration': duration,
                    'event': 0,
                    'age': age,
                    'gender_male': 1 if record.gender == 'male' else 0
                })
        
        if len(data) < 10:
            return {
                'error': 'insufficient_complete_data',
                'message': f'完整數據不足：{len(results)} 位患者中只有 {len(data)} 位有完整的出生日期資料，Cox 回歸分析至少需要 10 位。',
                'suggestion': '請嘗試：1) 擴大時間範圍 2) 移除或更改診斷條件 3) 使用統計摘要查看數據情況',
                'total_patients': len(results),
                'patients_with_complete_data': len(data),
                'min_required': 10
            }
        
        df = pd.DataFrame(data)
        
        # 檢查是否有足夠的事件
        event_count = df['event'].sum()
        if event_count == 0:
            return {
                'error': 'no_events',
                'message': f'無法進行 Cox 回歸分析：數據中沒有觀察到任何事件（如死亡、疾病進展等）。',
                'explanation': f'Cox 比例風險模型需要至少有一些患者發生事件才能估計風險比。當前所有 {len(df)} 位患者都被視為"刪失"（censored），表示在追蹤期間未觀察到事件。',
                'suggestion': '這可能是因為：1) 追蹤時間過短 2) 該疾病預後良好，很少有嚴重結果 3) 數據中缺少結束事件的記錄。建議使用 Kaplan-Meier 分析來查看存活曲線，或增加追蹤時間。',
                'total_patients': len(df),
                'events_observed': int(event_count),
                'censored': len(df)
            }
        
        if event_count < 5:
            return {
                'error': 'insufficient_events',
                'message': f'事件數量不足：只觀察到 {int(event_count)} 個事件，Cox 回歸分析建議至少需要 5 個事件。',
                'suggestion': '請嘗試：1) 擴大時間範圍 2) 增加樣本量 3) 使用 Kaplan-Meier 分析作為替代方案',
                'total_patients': len(df),
                'events_observed': int(event_count),
                'min_events_required': 5
            }
        
        # Cox 回歸分析
        cph = CoxPHFitter()
        try:
            cph.fit(df, duration_col='duration', event_col='event')
        except Exception as fit_error:
            logger.error(f"Cox model fitting failed: {fit_error}")
            return {
                'error': 'model_convergence_failed',
                'message': 'Cox 回歸模型無法收斂。',
                'explanation': '這通常是由於數據中的協變量之間存在高度共線性，或事件數量相對於協變量數量太少。',
                'suggestion': '請嘗試：1) 減少協變量數量 2) 增加樣本量 3) 使用 Kaplan-Meier 分層分析作為替代',
                'total_patients': len(df),
                'events_observed': int(event_count)
            }
        
        # 提取結果
        summary = cph.summary
        
        results_dict = {}
        for covariate in summary.index:
            results_dict[covariate] = {
                'hazard_ratio': float(np.exp(summary.loc[covariate, 'coef'])),
                'confidence_interval_lower': float(np.exp(summary.loc[covariate, 'coef lower 95%'])),
                'confidence_interval_upper': float(np.exp(summary.loc[covariate, 'coef upper 95%'])),
                'p_value': float(summary.loc[covariate, 'p']),
                'significant': summary.loc[covariate, 'p'] < 0.05
            }
        
        return convert_numpy_types({
            'analysis_type': 'cox_proportional_hazards',
            'covariates': results_dict,
            'concordance_index': float(cph.concordance_index_),
            'log_likelihood': float(cph.log_likelihood_),
            'total_patients': len(df),
            'interpretation': {
                'hazard_ratio_greater_than_1': '增加風險（更差的預後）',
                'hazard_ratio_less_than_1': '降低風險（更好的預後）',
                'hazard_ratio_equals_1': '無影響'
            }
        })
    
    except HTTPException:
        raise  # 重新抛出 HTTPException
    except Exception as e:
        logger.error(f"Error in Cox regression: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 存活統計摘要
# ============================================================================

@router.get("/survival-summary")
@cache_result(expire_seconds=900, key_prefix="survival_summary")
async def survival_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    diagnosis_code: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    存活分析摘要統計
    
    提供基本的存活統計信息
    """
    try:
        # 獲取數據
        query = db.query(
            Condition.patient_id,
            Condition.onset_datetime,
            Patient.gender,
            Patient.birth_date
        ).join(Patient, Condition.patient_id == Patient.fhir_id)
        
        if diagnosis_code:
            query = query.filter(Condition.code_text.ilike(f'%{diagnosis_code}%'))
        if start_date:
            query = query.filter(Condition.onset_datetime >= start_date)
        if end_date:
            query = query.filter(Condition.onset_datetime <= end_date)
        
        results = query.all()
        
        if not results:
            return {
                'total_patients': 0,
                'message': 'No data found'
            }
        
        # 計算統計
        durations = []
        current_time = datetime.now(timezone.utc)
        
        for record in results:
            if record.onset_datetime:
                duration = (current_time - record.onset_datetime).days
                durations.append(duration)
        
        durations = np.array(durations)
        
        return convert_numpy_types({
            'total_patients': len(results),
            'follow_up_statistics': {
                'mean_days': float(np.mean(durations)),
                'median_days': float(np.median(durations)),
                'min_days': int(np.min(durations)),
                'max_days': int(np.max(durations)),
                'std_days': float(np.std(durations))
            },
            'gender_distribution': {
                'male': sum(1 for r in results if r.gender == 'male'),
                'female': sum(1 for r in results if r.gender == 'female'),
                'unknown': sum(1 for r in results if not r.gender or r.gender not in ['male', 'female'])
            },
            'age_groups': {
                '<18': sum(1 for r in results if r.birth_date and (current_time - datetime.combine(r.birth_date, datetime.min.time()).replace(tzinfo=timezone.utc)).days / 365.25 < 18),
                '18-39': sum(1 for r in results if r.birth_date and 18 <= (current_time - datetime.combine(r.birth_date, datetime.min.time()).replace(tzinfo=timezone.utc)).days / 365.25 < 40),
                '40-59': sum(1 for r in results if r.birth_date and 40 <= (current_time - datetime.combine(r.birth_date, datetime.min.time()).replace(tzinfo=timezone.utc)).days / 365.25 < 60),
                '60+': sum(1 for r in results if r.birth_date and (current_time - datetime.combine(r.birth_date, datetime.min.time()).replace(tzinfo=timezone.utc)).days / 365.25 >= 60)
            }
        })
    
    except HTTPException:
        raise  # 重新抛出 HTTPException
    except Exception as e:
        logger.error(f"Error in survival summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

