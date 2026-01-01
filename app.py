import streamlit as st
import pandas as pd
import json
import yaml
from datetime import datetime
from io import BytesIO
import plotly.express as px
import os
import glob

# --- [경로 자동 찾기] ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIGS_DIR = os.path.join(BASE_DIR, "configs")

# configs 폴더가 없으면 자동 생성
if not os.path.exists(CONFIGS_DIR):
    os.makedirs(CONFIGS_DIR)

# --- [Edwards Korea 공식 툴 설정] ---
st.set_page_config(
    page_title="Edwards Equipment Management System",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- [Edwards Vacuum 공식 브랜딩 스타일] ---
st.markdown("""
    <style>
    /* Edwards Vacuum 공식 색상 (웹사이트 참고) */
    :root {
        --edwards-primary: #1E3A5F;      /* 진한 네이비 블루 */
        --edwards-secondary: #2C5F8D;     /* 중간 블루 */
        --edwards-accent: #4A90A4;        /* 청록색 액센트 */
        --edwards-light: #E8F0F5;         /* 연한 블루 그레이 */
        --edwards-gray: #6B7280;          /* 중립 회색 */
        --edwards-dark: #111827;          /* 진한 텍스트 */
    }
    
    .edwards-header {
        background: linear-gradient(135deg, #1E3A5F 0%, #2C5F8D 50%, #4A90A4 100%);
        color: white;
        padding: 2.5rem 2rem;
        border-radius: 0;
        margin: -1rem -1rem 2rem -1rem;
        box-shadow: 0 4px 12px rgba(30, 58, 95, 0.3);
        border-bottom: 4px solid #4A90A4;
    }
    
    .edwards-header h1 {
        color: white;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        font-family: 'Segoe UI', 'Malgun Gothic', Arial, sans-serif;
        letter-spacing: -0.5px;
    }
    
    .edwards-header p {
        color: rgba(255,255,255,0.95);
        font-size: 1rem;
        margin: 0.8rem 0 0 0;
        font-weight: 400;
    }
    
    .edwards-badge {
        display: inline-block;
        background: rgba(255,255,255,0.25);
        padding: 0.4rem 1rem;
        border-radius: 4px;
        font-size: 0.8rem;
        margin-top: 1rem;
        font-weight: 500;
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 6px;
        border-left: 4px solid #2C5F8D;
        box-shadow: 0 2px 8px rgba(30, 58, 95, 0.1);
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 58, 95, 0.15);
    }
    
    .stDataFrame {
        border: 1px solid #E8F0F5;
        border-radius: 6px;
        overflow: hidden;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(135deg, #2C5F8D 0%, #4A90A4 100%);
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1E3A5F 0%, #2C5F8D 100%);
        box-shadow: 0 4px 12px rgba(30, 58, 95, 0.3);
    }
    
    /* 사이드바 스타일 */
    .css-1d391kg {
        background-color: #F8FAFC;
    }
    
    /* 메인 컨텐츠 배경 */
    .main .block-container {
        background-color: #FFFFFF;
    }
    </style>
""", unsafe_allow_html=True)

# --- [표준 컬럼 매핑 - Edwards 표준] ---
COLUMN_MAPPER = {
    "LineTag": ["lineTag", "id", "Line Tag", "tag", "line_tag"],
    "장비명": ["name", "applicationName", "장비명", "Device_Name", "deviceName", "equipmentName"],
    "IP": ["ipAddress", "IP Address", "address", "IP", "ip", "ip_address"],
    "보고명": ["reportName", "name", "보고명", "description", "report_name"],
    "System Serial Number": ["systemSerialNumber", "Controller Serial Number", "System Serial Number", "Serial", "serial", "system_serial"],
    "Pump Type": ["Pump Type", "applicationName", "model", "Application Version", "pumpType", "pump_type"],
    "Pump Node Module": ["Pump Node Module", "Project Version", "version", "module", "pumpNodeModule", "name"],
    "SliceType": ["SliceType", "id", "type", "slice", "sliceType"],
    "FeedEngine": ["feedEngine", "FeedEngine", "engine", "feed_engine"],
    "ToolType": ["ToolType", "toolType", "tool_type"],
    "Version": ["version", "Version", "projectVersion", "Project Version"]
}

# --- [지능형 데이터 추출 함수] ---
def extract_all_kv(obj, pool=None):
    """중첩된 구조에서 모든 키-값 쌍을 재귀적으로 추출"""
    if pool is None:
        pool = {}
    
    if isinstance(obj, dict):
        # name-version 쌍 특수 처리
        n, v = obj.get('name'), obj.get('version') or obj.get('value')
        if n and v is not None:
            pool[str(n)] = v
        
        for k, v_ in obj.items():
            if isinstance(v_, (dict, list)):
                extract_all_kv(v_, pool)
            else:
                pool[k] = v_
    elif isinstance(obj, list):
        for item in obj:
            extract_all_kv(item, pool)
    
    return pool

# --- [경로 자동 찾기] ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIGS_DIR = os.path.join(BASE_DIR, "configs")

# configs 폴더가 없으면 자동 생성
if not os.path.exists(CONFIGS_DIR):
    os.makedirs(CONFIGS_DIR)

# --- [configs 폴더 스캔] ---
def scan_configs_folder():
    """configs 폴더에서 YAML/JSON 파일 스캔"""
    config_files = []
    if os.path.exists(CONFIGS_DIR):
        all_files = os.listdir(CONFIGS_DIR)
        config_files = [f for f in all_files if f.endswith(('.yml', '.yaml', '.json'))]
        config_files.sort()
    return config_files

# --- [파일 형식 자동 감지 및 파싱] ---
def detect_and_parse(file_content, file_name):
    """파일 형식을 자동 감지하여 JSON 또는 YAML로 파싱"""
    try:
        # YAML 시도
        file_content.seek(0)
        data = yaml.safe_load(file_content)
        if data is not None:
            return data, 'yaml'
    except:
        pass
    
    try:
        # JSON 시도
        file_content.seek(0)
        data = json.load(file_content)
        return data, 'json'
    except json.JSONDecodeError as e:
        st.error(f"파일 '{file_name}' 파싱 실패: JSON 형식 오류")
        return None, None
    except Exception as e:
        st.error(f"파일 '{file_name}' 파싱 실패: {str(e)}")
        return None, None

def scan_configs_folder():
    """configs 폴더에서 YAML/JSON 파일 스캔"""
    config_files = []
    if os.path.exists(CONFIGS_DIR):
        all_files = os.listdir(CONFIGS_DIR)
        config_files = [f for f in all_files if f.endswith(('.yml', '.yaml', '.json'))]
        config_files.sort()
    return config_files

# --- [IP 기준 데이터 통합 함수] ---
def parse_with_ip_merge(uploaded_files):
    """여러 파일을 IP 기준으로 통합하여 데이터프레임 생성"""
    all_rows = []
    processed_files = 0
    error_files = []
    
    for file in uploaded_files:
        try:
            file.seek(0)
            raw, file_type = detect_and_parse(file, file.name)
            
            if raw is None:
                error_files.append(file.name)
                continue
            
            file_name = file.name
            processed_files += 1
            
            # 파일 전체의 공통 정보 추출
            global_pool = extract_all_kv(raw)
            
            # equipment 배열 처리 (새로운 형식: equipment -> applications -> versionInformation)
            if 'equipment' in raw and isinstance(raw['equipment'], list):
                for equipment in raw['equipment']:
                    equip_ip = equipment.get('ipAddress', '-')
                    equip_name = equipment.get('name', '-')
                    
                    # applications 배열 처리
                    if 'applications' in equipment and isinstance(equipment['applications'], list):
                        for app in equipment['applications']:
                            app_name = app.get('applicationName', '-')
                            
                            # versionInformation 배열 처리
                            if 'versionInformation' in app and isinstance(app['versionInformation'], list):
                                for version_info in app['versionInformation']:
                                    version_name = version_info.get('name', '-')
                                    version_value = version_info.get('version', '-')
                                    
                                    row = {
                                        "Source_File": file_name,
                                        "IP": equip_ip,
                                        "장비명": equip_name,
                                        "applicationName": app_name,
                                        "name": version_name,
                                        "Version": version_value
                                    }
                                    
                                    # 각 표준 컬럼별로 값 채우기
                                    for std_name, candidates in COLUMN_MAPPER.items():
                                        if std_name in ["IP", "장비명", "Version"]:
                                            continue
                                        
                                        # 특수 처리: name 필드가 표준 컬럼명과 일치하는 경우
                                        if std_name == "Pump Type" and version_name == "Pump Type":
                                            row[std_name] = version_value
                                        elif std_name == "Pump Node Module" and version_name == "Pump Node Module":
                                            row[std_name] = version_value
                                        elif std_name == "보고명" and version_name:
                                            row[std_name] = version_name
                                        else:
                                            # 일반 매핑
                                            for c in candidates:
                                                val = None
                                                if c == "applicationName":
                                                    val = app_name
                                                elif c == "name":
                                                    # name 필드가 특정 컬럼과 매칭되는지 확인
                                                    if std_name == "Pump Type" and version_name == "Pump Type":
                                                        val = version_value
                                                    elif std_name == "Pump Node Module" and version_name == "Pump Node Module":
                                                        val = version_value
                                                    else:
                                                        val = version_name
                                                elif c in version_info:
                                                    val = version_info.get(c)
                                                elif c in app:
                                                    val = app.get(c)
                                                elif c in equipment:
                                                    val = equipment.get(c)
                                                elif c in global_pool:
                                                    val = global_pool.get(c)
                                                
                                                if val:
                                                    row[std_name] = val
                                                    break
                                        
                                        if std_name not in row:
                                            row[std_name] = "-"
                                    
                                    all_rows.append(row)
            
            # summaryVersionInformation 처리 (기존 형식)
            elif 'summaryVersionInformation' in raw and isinstance(raw['summaryVersionInformation'], list):
                items = raw['summaryVersionInformation']
                # 각 항목을 개별 행으로 추가
                for item in items:
                    item_pool = extract_all_kv(item)
                    combined = {**global_pool, **item_pool}
                    
                    # IP 찾기
                    ip = "-"
                    for ip_key in COLUMN_MAPPER["IP"]:
                        if combined.get(ip_key):
                            ip = str(combined.get(ip_key))
                            break
                    
                    # 각 항목을 개별 행으로 추가
                    row = {"Source_File": file_name, "IP": ip}
                    
                    # 각 표준 컬럼별로 값 채우기
                    for std_name, candidates in COLUMN_MAPPER.items():
                        if std_name == "IP":
                            continue
                        for c in candidates:
                            val = combined.get(c)
                            if val:
                                row[std_name] = val
                                break
                        # 값이 없으면 "-"로 설정
                        if std_name not in row:
                            row[std_name] = "-"
                    
                    all_rows.append(row)
            else:
                # 기존 로직: IP 기준 통합
                ip_groups = {}
                
                for item in items:
                    item_pool = extract_all_kv(item)
                    # 항목 정보와 전역 정보를 합침
                    combined = {**global_pool, **item_pool}
                    
                    # IP 찾기
                    ip = "-"
                    for ip_key in COLUMN_MAPPER["IP"]:
                        if combined.get(ip_key):
                            ip = str(combined.get(ip_key))
                            break
                    
                    # 동일 IP가 있으면 기존 데이터와 병합, 없으면 새로 생성
                    if ip not in ip_groups:
                        ip_groups[ip] = {"Source_File": file_name, "IP": ip}
                    
                    # 각 표준 컬럼별로 값 채우기
                    for std_name, candidates in COLUMN_MAPPER.items():
                        if std_name == "IP":
                            continue
                        # 기존에 값이 없을 때만 새로 찾아서 채움
                        if ip_groups[ip].get(std_name) in [None, "-", ""]:
                            for c in candidates:
                                val = combined.get(c)
                                if val:
                                    ip_groups[ip][std_name] = val
                                    break
                
                all_rows.extend(list(ip_groups.values()))
            
        except Exception as e:
            error_files.append(f"{file.name}: {str(e)}")
            continue
    
    if error_files:
        st.warning(f"⚠️ {len(error_files)}개 파일 처리 중 오류 발생")
        for err in error_files[:5]:  # 최대 5개만 표시
            st.caption(f"  • {err}")
    
    if not all_rows:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_rows)
    # 최종 보정: 빈칸 처리
    df = df.fillna("-")
    
    # 표준 컬럼 순서로 정렬
    standard_cols = list(COLUMN_MAPPER.keys())
    existing_cols = [col for col in standard_cols if col in df.columns]
    other_cols = [col for col in df.columns if col not in standard_cols]
    df = df[existing_cols + other_cols]
    
    return df

# --- [펌프별 그룹핑 및 통계] ---
def analyze_pump_data(df):
    """펌프 데이터 분석 및 통계 생성"""
    if df is None or df.empty:
        return None
    
    result = {
        'total_records': len(df),
        'unique_ips': 0,
        'unique_pumps': 0,
        'pump_breakdown': {},
        'tooltype_info': {}
    }
    
    if 'IP' in df.columns:
        result['unique_ips'] = df['IP'].nunique()
    
    pump_col = None
    for col in ['장비명', 'Pump Type', 'applicationName']:
        if col in df.columns:
            pump_col = col
            break
    
    if pump_col:
        # 펌프만 필터링 (Pump가 포함된 항목)
        pump_mask = df[pump_col].astype(str).str.contains('Pump', case=False, na=False)
        pump_df = df[pump_mask]
        result['unique_pumps'] = pump_df[pump_col].nunique() if not pump_df.empty else 0
        result['pump_breakdown'] = pump_df[pump_col].value_counts().to_dict() if not pump_df.empty else {}
    
    # ToolType 정보 추출
    if 'applicationName' in df.columns:
        tooltype_mask = df['applicationName'].astype(str).str.contains('ToolType', case=False, na=False)
        tooltype_df = df[tooltype_mask]
        if not tooltype_df.empty and 'name' in tooltype_df.columns and 'version' in tooltype_df.columns:
            tooltype_info = {}
            for _, row in tooltype_df.iterrows():
                name = str(row.get('name', ''))
                version = str(row.get('version', ''))
                if name and version:
                    tooltype_info[name] = version
            result['tooltype_info'] = tooltype_info
    
    return result

# --- [엑셀 리포트 생성] ---
def generate_excel_report(df, analysis_data):
    """Edwards 표준 형식의 엑셀 리포트 생성"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 요약 시트
        summary_data = {
            '항목': ['총 레코드 수', '고유 IP 수', '고유 펌프 수', '생성 일시'],
            '값': [
                analysis_data.get('total_records', 0),
                analysis_data.get('unique_ips', 0),
                analysis_data.get('unique_pumps', 0),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # 펌프별 집계
        pump_col = None
        for col in ['장비명', 'Pump Type', 'applicationName']:
            if col in df.columns:
                pump_col = col
                break
        
        if pump_col:
            pump_summary = df.groupby(pump_col).size().reset_index(name='Count')
            pump_summary.columns = ['Pump Name', 'Count']
            pump_summary.to_excel(writer, sheet_name='Pump Summary', index=False)
        
        # 원본 데이터
        df.to_excel(writer, sheet_name='Equipment Data', index=False)
    
    output.seek(0)
    return output

# --- [메인 대시보드] ---
def main():
    # Edwards Vacuum 헤더
    st.markdown("""
        <div class="edwards-header">
            <h1>Edwards Equipment Management System</h1>
            <p>Edwards Vacuum 공식 장비 관리 시스템</p>
            <span class="edwards-badge">Version 2.0 | 대한민국</span>
        </div>
    """, unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        # Edwards 로고 영역 (실제 로고 이미지로 교체 가능)
        st.markdown("""
        <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #1E3A5F 0%, #2C5F8D 100%); border-radius: 8px; margin-bottom: 1rem;'>
            <h3 style='color: white; margin: 0; font-size: 1.3rem;'>Edwards Vacuum</h3>
            <p style='color: rgba(255,255,255,0.9); margin: 0.3rem 0 0 0; font-size: 0.85rem;'>Equipment Management</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        st.header("사용 가이드")
        st.markdown("""
        **1단계:** JSON 또는 YAML 파일 업로드
        
        **2단계:** IP 기준으로 자동 통합
        
        **3단계:** 장비 정보 확인 및 리포트 다운로드
        
        ---
        
        **지원 형식:**
        - JSON 파일
        - YAML 파일
        - 다중 파일 업로드 가능
        
        **통합 기준:**
        - IP 주소 기준 자동 통합
        - 중복 데이터 병합
        """)
        
        st.markdown("---")
        st.caption("© 2024 Edwards Vacuum. All rights reserved.")
        st.caption("Edwards Vacuum은 Atlas Copco Group의 일원입니다.")
    
    # 파일 업로드 - 탭으로 구분
    tab1, tab2, tab3 = st.tabs(["📤 파일 업로드", "📁 configs 폴더", "🔍 경로 진단"])
    
    uploaded_files = None
    
    with tab1:
        st.subheader("📤 파일 업로드")
        uploaded_files = st.file_uploader(
            "JSON 또는 YAML 파일을 선택하세요 (다중 선택 가능)",
            type=['json', 'yaml', 'yml'],
            accept_multiple_files=True,
            help="Edwards EST에서 내보낸 장비 정보 파일"
        )
    
    with tab2:
        st.subheader("📁 configs 폴더에서 불러오기")
        st.info(f"📂 configs 폴더 위치: `{CONFIGS_DIR}`")
        
        config_files = scan_configs_folder()
        
        if config_files:
            st.success(f"✅ {len(config_files)}개의 설정 파일을 찾았습니다.")
            selected_config = st.selectbox("설정 파일 선택", config_files)
            
            if st.button("📊 파일 불러오기", type="primary"):
                config_path = os.path.join(CONFIGS_DIR, selected_config)
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        if selected_config.endswith(('.yml', '.yaml')):
                            data = yaml.safe_load(f)
                        else:
                            data = json.load(f)
                    
                    # 파일 객체처럼 만들기 (기존 로직과 호환)
                    class FileWrapper:
                        def __init__(self, name, data):
                            self.name = name
                            self.data = data
                            self._content = None
                        
                        def seek(self, pos):
                            pass
                        
                        def read(self):
                            if self._content is None:
                                if isinstance(self.data, dict):
                                    self._content = json.dumps(self.data, ensure_ascii=False).encode('utf-8')
                                else:
                                    self._content = str(self.data).encode('utf-8')
                            return self._content
                    
                    uploaded_files = [FileWrapper(selected_config, data)]
                    st.success(f"✅ {selected_config} 로드 성공!")
                    st.rerun()  # 페이지 새로고침하여 데이터 표시
                except Exception as e:
                    st.error(f"❌ 파일 읽기 오류: {str(e)}")
        else:
            st.warning(f"⚠️ configs 폴더에 YAML/JSON 파일이 없습니다.")
            st.info(f"💡 `{CONFIGS_DIR}` 폴더에 파일을 넣어주세요.")
    
    with tab3:
        st.subheader("🔍 경로 진단 도구")
        st.info(f"현재 툴의 위치: `{BASE_DIR}`")
        st.info(f"configs 폴더 위치: `{CONFIGS_DIR}`")
        
        if os.path.exists(CONFIGS_DIR):
            all_files = os.listdir(CONFIGS_DIR)
            st.write(f"📁 configs 폴더 내 전체 파일: {all_files}")
            
            config_files = [f for f in all_files if f.endswith(('.yml', '.yaml', '.json'))]
            if config_files:
                st.success(f"✅ 인식 가능한 파일: {config_files}")
            else:
                st.error("❌ 인식 가능한 .yml/.yaml/.json 파일이 없습니다!")
        else:
            st.warning(f"⚠️ {CONFIGS_DIR} 폴더가 없어서 새로 만들었습니다.")
    
    if uploaded_files:
        with st.spinner("파일을 분석하고 IP 기준으로 통합 중입니다..."):
            df = parse_with_ip_merge(uploaded_files)
        
        if not df.empty:
            st.success(f"✅ {len(uploaded_files)}개 파일에서 {len(df)}개 레코드를 성공적으로 통합했습니다.")
            
            # 데이터 분석
            analysis_data = analyze_pump_data(df)
            
            # 상단 요약 메트릭
            st.markdown("---")
            st.subheader("📊 시스템 요약")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if "System Serial Number" in df.columns:
                    serial = df["System Serial Number"].iloc[0] if df["System Serial Number"].iloc[0] != "-" else "N/A"
                    st.metric("System Serial Number", serial)
                else:
                    st.metric("System Serial Number", "N/A")
            
            with col2:
                if "LineTag" in df.columns:
                    tag = df["LineTag"].iloc[0] if df["LineTag"].iloc[0] != "-" else "N/A"
                    st.metric("Line Tag", tag)
                else:
                    st.metric("Line Tag", "N/A")
            
            with col3:
                if "장비명" in df.columns:
                    equipment = df["장비명"].iloc[0] if df["장비명"].iloc[0] != "-" else "N/A"
                    st.metric("장비명", equipment)
                else:
                    st.metric("장비명", "N/A")
            
            with col4:
                if "IP" in df.columns:
                    ip = df["IP"].iloc[0] if df["IP"].iloc[0] != "-" else "N/A"
                    st.metric("IP Address", ip)
                else:
                    st.metric("IP Address", "N/A")
            
            # ToolType 정보 표시 (장비 툴타입)
            if analysis_data and analysis_data.get('tooltype_info'):
                st.markdown("---")
                st.subheader("🔧 장비 ToolType 정보")
                tooltype_info = analysis_data['tooltype_info']
                
                col1, col2 = st.columns(2)
                for idx, (name, value) in enumerate(tooltype_info.items()):
                    with col1 if idx % 2 == 0 else col2:
                        st.markdown(f"""
                        <div style='background: #F8FAFC; padding: 1rem; border-radius: 6px; border-left: 4px solid #2C5F8D; margin-bottom: 0.5rem;'>
                            <strong style='color: #1E3A5F;'>{name}</strong><br>
                            <span style='color: #6B7280; font-size: 1.1rem;'>{value}</span>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.subheader("📋 장비 리스트 (IP 기준 통합)")
            
            # 필터링 옵션
            if "IP" in df.columns:
                unique_ips = ['전체'] + sorted([ip for ip in df['IP'].unique() if ip != "-"])
                selected_ip = st.selectbox("IP 주소로 필터링", unique_ips)
                
                if selected_ip != '전체':
                    filtered_df = df[df['IP'] == selected_ip].copy()
                else:
                    filtered_df = df.copy()
            else:
                filtered_df = df.copy()
                selected_ip = '전체'
            
            # 데이터 테이블
            display_cols = [col for col in list(COLUMN_MAPPER.keys()) + ["Source_File"] if col in filtered_df.columns]
            st.dataframe(
                filtered_df[display_cols],
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            # 펌프별 통계
            if analysis_data and analysis_data.get('pump_breakdown'):
                st.markdown("---")
                st.subheader("📈 펌프별 통계")
                
                pump_df = pd.DataFrame({
                    '펌프명': list(analysis_data['pump_breakdown'].keys()),
                    '수량': list(analysis_data['pump_breakdown'].values())
                })
                
                col1, col2 = st.columns(2)
                with col1:
                    fig_pie = px.pie(pump_df, values='수량', names='펌프명', 
                                   title='펌프별 분포',
                                   color_discrete_sequence=px.colors.qualitative.Set3)
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    fig_bar = px.bar(pump_df, x='펌프명', y='수량', 
                                   title='펌프별 수량',
                                   color='수량',
                                   color_continuous_scale='Blues')
                    st.plotly_chart(fig_bar, use_container_width=True)
            
            # 펌프 필터링 옵션 추가
            if 'applicationName' in df.columns:
                # 펌프만 필터링
                pump_mask = df['applicationName'].astype(str).str.contains('Pump', case=False, na=False)
                pump_df_filtered = df[pump_mask] if pump_mask.any() else pd.DataFrame()
                
                if not pump_df_filtered.empty:
                    st.markdown("---")
                    st.subheader("🔍 펌프 정보 상세 보기")
                    
                    unique_pumps = ['전체'] + sorted(pump_df_filtered['applicationName'].unique().tolist())
                    selected_pump_detail = st.selectbox("펌프 선택 (상세 정보)", unique_pumps)
                    
                    if selected_pump_detail != '전체':
                        pump_detail_df = pump_df_filtered[pump_df_filtered['applicationName'] == selected_pump_detail]
                        st.dataframe(pump_detail_df, use_container_width=True, hide_index=True)
            
            # 리포트 다운로드
            st.markdown("---")
            st.subheader("📥 리포트 다운로드")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # CSV 다운로드
                csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    "📄 CSV 리포트 다운로드",
                    data=csv,
                    file_name=f"Edwards_Equipment_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Excel 다운로드
                excel_buffer = generate_excel_report(filtered_df, analysis_data)
                st.download_button(
                    "📊 Excel 리포트 다운로드",
                    data=excel_buffer.getvalue(),
                    file_name=f"Edwards_Equipment_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openpyxl-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.error("❌ 데이터를 추출할 수 없습니다. 파일 형식을 확인해주세요.")
    else:
        st.info("💡 **시작하기**: 위에서 JSON 또는 YAML 파일을 업로드하세요.")
        
        with st.expander("📝 지원 파일 형식 예시"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**JSON 예시:**")
                st.json({
                    "applicationName": "EXP1 Pump",
                    "name": "Pump Node Module",
                    "version": "D37486834_V5",
                    "ipAddress": "192.168.1.100"
                })
            
            with col2:
                st.markdown("**YAML 예시:**")
                st.code("""
applicationName: EXP1 Pump
name: Pump Node Module
version: D37486834_V5
ipAddress: 192.168.1.100
                """, language='yaml')
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background: #F8FAFC; border-radius: 8px; margin-top: 2rem;'>
        <p style='color: #1E3A5F; font-weight: 600; margin-bottom: 0.5rem;'><strong>Edwards Equipment Management System</strong></p>
        <p style='font-size: 0.85rem; color: #6B7280; margin: 0.3rem 0;'>© 2024 Edwards Vacuum. All rights reserved.</p>
        <p style='font-size: 0.8rem; color: #6B7280; margin-top: 0.5rem;'>Edwards Vacuum은 Atlas Copco Group의 일원입니다.</p>
        <p style='font-size: 0.75rem; color: #9CA3AF; margin-top: 0.8rem;'>For technical support, please contact Edwards Vacuum Korea support team.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
