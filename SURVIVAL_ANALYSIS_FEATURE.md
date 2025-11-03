# 存活分析功能（Survival Analysis）

## 📋 概述

已成功為 FHIR Analytics Platform 添加完整的存活分析（Survival Analysis）功能，支持醫療數據的生存分析、Kaplan-Meier 生存曲線和 Cox 比例風險模型。

---

## ✨ 功能特點

### 1. Kaplan-Meier 生存分析 📈
- **生存曲線繪製**：可視化隨時間變化的生存機率
- **信賴區間**：95% 信賴區間顯示
- **中位生存時間**：自動計算並顯示
- **分層分析**：支持按性別、年齡組等變數分層
- **統計檢定**：自動進行 Log-rank 檢定比較組間差異

### 2. Cox 比例風險模型 🎯
- **風險比計算**：評估不同變數對生存的影響
- **多變量分析**：同時分析年齡、性別等多個因素
- **統計顯著性**：自動標註統計顯著的變數
- **模型評估**：提供一致性指數（C-index）評估模型性能

### 3. 生存統計摘要 📊
- **基本統計**：樣本數、追蹤時間統計
- **人口統計**：性別分佈、年齡組分佈
- **視覺化圖表**：直觀的分佈圖表展示

---

## 🏗️ 技術架構

### 後端（Python/FastAPI）

#### 新增 Python 庫
```python
# requirements.txt
lifelines==0.27.8      # 生存分析核心庫
matplotlib==3.8.2      # 圖表生成
scipy==1.11.4          # 統計計算
```

#### 數據模型
- **`SurvivalCohort`**：生存分析群組管理
  - 定義納入/排除條件
  - 追蹤起始和結束事件
  - 儲存分析結果

- **`SurvivalEvent`**：生存事件記錄
  - 患者級別的生存數據
  - 支持協變量（covariates）
  - 事件發生或審查（censored）狀態

#### API 端點

| 端點 | 方法 | 功能 |
|------|------|------|
| `/api/survival/kaplan-meier` | GET | Kaplan-Meier 分析 |
| `/api/survival/kaplan-meier/plot` | GET | 生成 KM 曲線圖 |
| `/api/survival/cox-regression` | GET | Cox 比例風險模型 |
| `/api/survival/survival-summary` | GET | 生存統計摘要 |

### 前端（React）

#### 組件結構
```
frontend/src/components/Survival/
├── SurvivalAnalysis.js      # 主組件
└── SurvivalAnalysis.css     # 樣式
```

#### 功能模組
1. **參數設定面板**
   - 診斷條件選擇
   - 時間範圍設定
   - 追蹤期間配置
   - 分層變數選擇

2. **結果展示**
   - 統計卡片
   - 交互式圖表
   - 數據表格
   - 統計檢定結果

3. **視覺化**
   - 生存曲線圖
   - 風險比森林圖（Forest Plot）
   - 分佈圖表

---

## 🚀 使用指南

### 1. 安裝依賴

#### 後端
```bash
# 進入後端目錄
cd backend

# 安裝新的 Python 庫
pip install lifelines==0.27.8 matplotlib==3.8.2 scipy==1.11.4

# 或重新安裝所有依賴
pip install -r requirements.txt
```

#### 前端
前端無需額外安裝，已使用現有的 React 和 Chart.js。

### 2. 數據庫遷移

執行數據庫遷移以創建新表：

```bash
# Docker 環境
docker-compose exec backend python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

# 本地環境
cd backend
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### 3. 重啟服務

```bash
# Docker 環境
docker-compose restart backend frontend

# 本地環境 - 重啟 backend 和 frontend
```

### 4. 訪問功能

打開瀏覽器訪問 `http://localhost:3000`，在導航欄中點擊「存活分析 🔬」。

---

## 📖 使用示例

### 示例 1：基本 Kaplan-Meier 分析

**操作步驟**：
1. 選擇分析類型：「Kaplan-Meier 存活分析」
2. （可選）輸入診斷條件：例如 "Influenza"
3. 設定追蹤期間：365 天（1年）或 1825 天（5年）
4. 點擊「開始分析」

**結果**：
- 總病患數統計
- 生存曲線圖
- 中位生存時間
- 95% 信賴區間
- 生存機率表

### 示例 2：性別分層分析

**操作步驟**：
1. 選擇分析類型：「Kaplan-Meier 存活分析」
2. 輸入診斷條件：例如 "Myocardial infarction"（心肌梗塞）
3. 分層變數：選擇「性別」
4. 點擊「開始分析」

**結果**：
- 男性和女性分別的生存曲線
- 各組的中位生存時間
- Log-rank 檢定結果
- P 值和統計顯著性

### 示例 3：Cox 比例風險模型

**操作步驟**：
1. 選擇分析類型：「Cox 比例風險模型」
2. 輸入診斷條件
3. 點擊「開始分析」

**結果**：
- 年齡的風險比（HR）
- 性別的風險比
- 95% 信賴區間
- P 值
- 一致性指數（C-index）

**解釋**：
- HR > 1：增加風險（更差的預後）
- HR < 1：降低風險（更好的預後）
- HR = 1：無影響

---

## 🎯 實際應用場景

### 1. 疾病預後評估
分析不同疾病患者的生存情況，評估疾病嚴重程度和預後。

**示例**：
- 流感患者的追蹤分析
- 心肌梗塞患者的長期預後
- 慢性疾病患者的生存曲線

### 2. 治療效果比較
比較不同治療方案的效果差異。

**示例**：
- 藥物 A vs 藥物 B
- 手術治療 vs 保守治療

### 3. 風險因素識別
識別影響患者生存的重要因素。

**示例**：
- 年齡對生存的影響
- 性別差異分析
- 合併症的影響評估

### 4. 公共衛生研究
進行人群級別的生存分析。

**示例**：
- 不同年齡組的健康狀況
- 地區性疾病監測
- 流行病學研究

---

## 📊 數據要求

### 必需字段
- **患者 ID**：唯一識別患者
- **起始時間**：診斷日期或治療開始日期（`onset_datetime`）
- **追蹤時間**：當前時間或最後追蹤時間

### 可選字段
- **性別**：用於分層分析
- **出生日期**：計算年齡組
- **事件狀態**：是否發生目標事件（當前預設為審查）
- **協變量**：其他影響因素

### 數據來源
系統從以下 FHIR 資源獲取數據：
- **Patients**：患者基本資訊
- **Conditions**：診斷記錄
- **Encounters**：就診記錄
- **Observations**：觀察數據

---

## ⚠️ 注意事項與限制

### 1. 當前限制
- **事件數據**：目前系統沒有真實的死亡或事件數據，所有記錄預設為「審查」（censored）
- **追蹤時間**：使用診斷日期到當前日期作為追蹤時間
- **樣本大小**：Cox 回歸分析至少需要 10 個患者

### 2. 數據解釋
由於缺乏真實事件數據：
- 生存曲線會保持在高水平（接近 100%）
- 中位生存時間可能無法計算
- 統計檢定可能不顯著

### 3. 未來改進
要獲得更有意義的結果，需要：
- 添加真實的事件數據（死亡、復發等）
- 整合電子病歷系統的隨訪數據
- 添加治療和干預數據
- 支持競爭風險分析

---

## 🔧 技術細節

### 生存分析算法

#### Kaplan-Meier 估計器
```python
from lifelines import KaplanMeierFitter

kmf = KaplanMeierFitter()
kmf.fit(durations=df['duration'], event_observed=df['event'])

# 生存函數
survival_function = kmf.survival_function_

# 中位生存時間
median_survival = kmf.median_survival_time_

# 信賴區間
confidence_interval = kmf.confidence_interval_
```

#### Cox 比例風險模型
```python
from lifelines import CoxPHFitter

cph = CoxPHFitter()
cph.fit(df, duration_col='duration', event_col='event')

# 風險比
hazard_ratios = np.exp(cph.params_)

# 統計顯著性
p_values = cph.summary['p']

# 模型評估
c_index = cph.concordance_index_
```

#### Log-rank 檢定
```python
from lifelines.statistics import logrank_test

results = logrank_test(
    durations_A=group1['duration'],
    durations_B=group2['duration'],
    event_observed_A=group1['event'],
    event_observed_B=group2['event']
)

p_value = results.p_value
test_statistic = results.test_statistic
```

### 圖表生成

使用 Matplotlib 生成高質量的生存曲線圖：

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 6))
kmf.plot_survival_function(ax=ax, ci_show=True)
ax.set_xlabel('追蹤時間（天）')
ax.set_ylabel('生存機率')
ax.set_title('Kaplan-Meier 生存曲線')
ax.grid(True, alpha=0.3)
```

### 緩存策略

使用 Redis 緩存分析結果：

```python
@cache_result(expire_seconds=1800, key_prefix="survival_km")
async def kaplan_meier_analysis(...):
    # 分析邏輯
    pass
```

緩存時間：
- Kaplan-Meier 分析：30 分鐘
- 統計摘要：15 分鐘

---

## 📈 性能優化

### 1. 數據預處理
- 使用 Pandas DataFrame 批量處理數據
- 預先計算常用統計指標

### 2. 異步處理
- 圖表生成使用異步處理
- 大數據集分批處理

### 3. 緩存機制
- Redis 緩存分析結果
- 減少重複計算

### 4. 索引優化
建議在數據庫中添加索引：

```sql
CREATE INDEX idx_conditions_patient_onset 
ON conditions(patient_id, onset_datetime);

CREATE INDEX idx_patients_gender_birth 
ON patients(gender, birth_date);
```

---

## 🧪 測試

### 單元測試

創建測試文件 `backend/tests/test_survival.py`：

```python
import pytest
from app.api.routes.survival import kaplan_meier_analysis

@pytest.mark.asyncio
async def test_kaplan_meier_basic():
    # 測試基本 KM 分析
    pass

@pytest.mark.asyncio
async def test_cox_regression():
    # 測試 Cox 回歸
    pass
```

### 集成測試

```bash
# 執行測試
cd backend
pytest tests/test_survival.py -v
```

---

## 📚 參考資料

### 學術資源
- [Kaplan-Meier Estimator](https://en.wikipedia.org/wiki/Kaplan%E2%80%93Meier_estimator)
- [Cox Proportional Hazards Model](https://en.wikipedia.org/wiki/Proportional_hazards_model)
- [Log-rank Test](https://en.wikipedia.org/wiki/Logrank_test)

### 技術文檔
- [lifelines Documentation](https://lifelines.readthedocs.io/)
- [Survival Analysis in Python](https://lifelines.readthedocs.io/en/latest/Survival%20analysis%20intro.html)

### FHIR 資源
- [FHIR Condition Resource](https://www.hl7.org/fhir/condition.html)
- [FHIR Observation Resource](https://www.hl7.org/fhir/observation.html)

---

## 🔄 未來功能計劃

### 短期（1-3 個月）
- [ ] 添加更多協變量支持
- [ ] 實現競爭風險分析
- [ ] 添加更多視覺化選項
- [ ] 支持自定義時間段

### 中期（3-6 個月）
- [ ] 整合真實事件數據
- [ ] 實現生存分析報告生成
- [ ] 添加敏感性分析
- [ ] 支持傾向分數匹配（PSM）

### 長期（6-12 個月）
- [ ] 機器學習生存預測模型
- [ ] 多狀態生存分析
- [ ] 貝葉斯生存分析
- [ ] 時變協變量支持

---

## 💡 最佳實踐

### 1. 數據準備
- 確保數據完整性和準確性
- 處理缺失值
- 驗證時間字段的正確性

### 2. 分析選擇
- 小樣本（< 30）：使用摘要統計
- 中等樣本（30-100）：Kaplan-Meier 分析
- 大樣本（> 100）：可以使用 Cox 回歸

### 3. 結果解釋
- 檢查信賴區間寬度
- 評估統計顯著性（P < 0.05）
- 考慮臨床意義

### 4. 報告撰寫
- 描述樣本特徵
- 說明分析方法
- 展示主要結果
- 討論局限性

---

## 🆘 疑難排解

### 問題 1：`lifelines` 未安裝
**錯誤**：`ImportError: No module named 'lifelines'`

**解決方案**：
```bash
pip install lifelines==0.27.8
```

### 問題 2：數據不足
**錯誤**：`Insufficient data for analysis`

**解決方案**：
- 擴大時間範圍
- 減少過濾條件
- 檢查數據庫是否有數據

### 問題 3：圖表無法顯示
**錯誤**：圖片為空或顯示錯誤

**解決方案**：
- 檢查 matplotlib 是否正確安裝
- 確認使用 'Agg' 後端
- 檢查瀏覽器控制台錯誤

### 問題 4：分析緩慢
**解決方案**：
- 使用緩存功能
- 限制數據範圍
- 優化數據庫索引

---

## 📞 獲取幫助

- **文檔**：查看本文檔和 API 文檔
- **GitHub Issues**：報告 bug 或提出功能請求
- **Email**：聯繫開發團隊

---

## ✅ 功能檢查清單

- [x] 後端 API 實現
- [x] 數據模型創建
- [x] Kaplan-Meier 分析
- [x] Cox 比例風險模型
- [x] 生存統計摘要
- [x] 圖表生成
- [x] 前端組件
- [x] 路由配置
- [x] 導航欄更新
- [x] 樣式設計
- [x] 文檔撰寫
- [ ] 單元測試（待完成）
- [ ] 集成測試（待完成）

---

**更新日期**：2024-11-03
**版本**：1.0.0
**狀態**：✅ 已完成並可使用

🎉 **恭喜！存活分析功能已成功添加到 FHIR Analytics Platform！**

