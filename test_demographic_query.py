import pandas as pd
from sqlalchemy import create_engine

# Test demographic filtering
DATABASE_URL = "postgresql://fhir_user:fhir_password@localhost:5432/fhir_analytics"

try:
    engine = create_engine(DATABASE_URL)
    
    print("=" * 60)
    print("測試 1: 全部患者的前10大診斷")
    print("=" * 60)
    query1 = """
        SELECT c.code_text as diagnosis, COUNT(*) as count
        FROM conditions c
        WHERE c.code_text IS NOT NULL
        GROUP BY c.code_text
        ORDER BY count DESC
        LIMIT 10
    """
    df1 = pd.read_sql(query1, engine)
    print(df1.to_string(index=False))
    print(f"\n總計: {df1['count'].sum()} 筆診斷記錄\n")
    
    print("=" * 60)
    print("測試 2: 僅男性患者的前10大診斷 (demographic filter)")
    print("=" * 60)
    query2 = """
        SELECT c.code_text as diagnosis, COUNT(*) as count
        FROM conditions c
        JOIN patients p ON c.patient_id = p.fhir_id
        WHERE c.code_text IS NOT NULL
        AND p.gender = 'male'
        GROUP BY c.code_text
        ORDER BY count DESC
        LIMIT 10
    """
    df2 = pd.read_sql(query2, engine)
    print(df2.to_string(index=False))
    print(f"\n總計: {df2['count'].sum()} 筆診斷記錄\n")
    
    print("=" * 60)
    print("測試 3: 僅女性患者的前10大診斷 (demographic filter)")
    print("=" * 60)
    query3 = """
        SELECT c.code_text as diagnosis, COUNT(*) as count
        FROM conditions c
        JOIN patients p ON c.patient_id = p.fhir_id
        WHERE c.code_text IS NOT NULL
        AND p.gender = 'female'
        GROUP BY c.code_text
        ORDER BY count DESC
        LIMIT 10
    """
    df3 = pd.read_sql(query3, engine)
    print(df3.to_string(index=False))
    print(f"\n總計: {df3['count'].sum()} 筆診斷記錄\n")
    
    print("=" * 60)
    print("測試 4: 驗證男女診斷數據是否不同")
    print("=" * 60)
    if not df2.empty and not df3.empty:
        male_top = df2.iloc[0]['diagnosis']
        female_top = df3.iloc[0]['diagnosis']
        print(f"男性最多診斷: {male_top} ({df2.iloc[0]['count']} 筆)")
        print(f"女性最多診斷: {female_top} ({df3.iloc[0]['count']} 筆)")
        if male_top != female_top or df2.iloc[0]['count'] != df3.iloc[0]['count']:
            print("✅ 確認: 男女數據確實不同，demographic filter 正常工作!")
        else:
            print("⚠️  警告: 男女數據相同，可能有問題")
    else:
        print("⚠️  警告: 沒有足夠的數據進行比較")
    
    engine.dispose()
    print("\n✅ 測試完成!")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()

