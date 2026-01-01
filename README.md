# ⚡ Edwards Pump Manager

Edwards EST 데이터를 활용한 펌프 정보 관리 도구입니다. EST에서 받은 펌프 정보를 체계적으로 관리하고 리포트를 생성합니다.

> ⚠️ 이 프로젝트는 개인 프로젝트이며, Edwards Vacuum의 공식 제품이 아닙니다.

## 🚀 주요 기능

- **JSON/YAML 파일 업로드**: EST에서 내보낸 장비 정보 파일 업로드
- **IP 기준 자동 통합**: 여러 파일을 IP 주소 기준으로 자동 통합
- **지능형 필드 매핑**: 다양한 필드명을 자동으로 인식
- **펌프별 통계**: 펌프별 그룹핑 및 통계 차트
- **ToolType 정보**: 장비 ToolType 정보 표시
- **엑셀/CSV 리포트**: 통합 리포트 다운로드

## 📋 요구사항

- Python 3.8 이상
- 필요한 패키지들은 `requirements.txt`에 명시되어 있습니다.

## 🛠️ 설치 방법

### 로컬 설치

1. 저장소 클론 또는 다운로드
2. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

3. 앱 실행:
```bash
streamlit run app.py
```

### Streamlit Cloud 배포

1. 이 저장소를 GitHub에 업로드
2. [Streamlit Cloud](https://streamlit.io/cloud)에 연결
3. 자동 배포 완료!

## 🎯 사용 방법

1. **파일 업로드**
   - JSON 또는 YAML 파일 업로드
   - 다중 파일 선택 가능

2. **자동 통합**
   - IP 기준으로 자동 통합
   - 중복 데이터 병합

3. **정보 확인**
   - 시스템 요약 확인
   - ToolType 정보 확인
   - 펌프별 통계 확인

4. **리포트 다운로드**
   - CSV 또는 Excel 형식으로 다운로드

## 📊 지원 형식

### JSON 형식
```json
{
  "name": "Summary",
  "ipAddress": "192.168.2.1",
  "summaryVersionInformation": [
    {
      "applicationName": "EXP1 Pump",
      "name": "Pump Node Module",
      "version": "D37486834_V5"
    }
  ]
}
```

### YAML 형식
```yaml
name: Summary
ipAddress: 192.168.2.1
summaryVersionInformation:
  - applicationName: EXP1 Pump
    name: Pump Node Module
    version: D37486834_V5
```

## 🔍 필드 매핑

시스템은 다음 필드명을 자동으로 인식합니다:

- **IP**: `ipAddress`, `IP Address`, `IP`, `ip`
- **장비명**: `applicationName`, `name`, `장비명`
- **버전**: `version`, `Version`, `projectVersion`
- **ToolType**: `ToolType`, `toolType`
- 기타 Edwards 표준 필드

## 💡 활용 사례

- 펌프 정보 체계적 관리
- 수기 작업 자동화
- 장비 정보 통합 리포트 생성
- 여러 시스템 정보 통합

## 📞 지원

Edwards Vacuum Korea 기술 지원팀에 문의하세요.

## 📝 라이선스

© 2024 Edwards Vacuum. All rights reserved.
Edwards Vacuum은 Atlas Copco Group의 일원입니다.
