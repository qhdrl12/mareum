# 데모 및 유틸리티 스크립트들

이 폴더는 ConfigParser의 기능을 시연하고 테스트하는 Python 스크립트들을 포함합니다.

## 파일 목록

### `demo_config_parser.py`
ConfigParser의 모든 주요 기능을 보여주는 종합 데모 스크립트입니다.

#### 기능 시연
1. **유효한 설정 파일 파싱**
   - YAML 형식 설정 파일 파싱
   - JSON 형식 설정 파일 파싱
   - 기본값 자동 적용 확인

2. **잘못된 설정 파일 처리**
   - 검증 오류 감지 및 표시
   - 상세한 오류 메시지 출력

3. **문자열 직접 파싱**
   - YAML 문자열 파싱
   - JSON 문자열 파싱
   - 메모리에서 설정 처리

4. **포맷 자동 감지**
   - JSON/YAML 포맷 자동 구분
   - 다양한 입력 형태 테스트

#### 실행 방법
```bash
# 프로젝트 루트에서 실행
python examples/scripts/demo_config_parser.py

# 또는 스크립트 디렉토리에서 실행
cd examples/scripts
python demo_config_parser.py
```

#### 예상 출력
```
ConfigParser Demo Script
This script demonstrates the ConfigParser functionality.

============================================================
DEMO: Parsing Valid Configuration Files
============================================================

1. Parsing valid YAML configuration:
✅ Successfully parsed YAML config!
   Agent name: customer-support-agent
   Model: openai - gpt-4
   Tools: 2 tools configured

2. Parsing valid JSON configuration:
✅ Successfully parsed JSON config!
   Agent name: research-assistant
   Model: anthropic - claude-3-5-sonnet-20241022
   Tools: 2 tools configured

... (계속)
```

## 스크립트 사용법

### 기본 실행
```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config_parser import ConfigParser
```

### 스키마 및 설정 파일 경로
```python
# 상대 경로를 사용한 파일 참조
schema_path = Path(__file__).parent.parent / "schemas" / "example_schema.json"
config_path = Path(__file__).parent.parent / "configs" / "valid_config.yaml"

parser = ConfigParser(schema_path=schema_path)
config = parser.parse_from_file(config_path)
```

## 커스텀 스크립트 작성

새로운 테스트나 데모 스크립트를 작성할 때 참고할 템플릿:

```python
#!/usr/bin/env python3
"""
Custom ConfigParser demo script.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config_parser import ConfigParser, ConfigParseError, ConfigValidationError


def main():
    """Main demo function."""
    print("Custom ConfigParser Demo")
    
    # 스키마 파일 경로
    schema_path = Path(__file__).parent.parent / "schemas" / "example_schema.json"
    parser = ConfigParser(schema_path=schema_path)
    
    try:
        # 설정 파일 파싱
        config_path = Path(__file__).parent.parent / "configs" / "valid_config.yaml"
        config = parser.parse_from_file(config_path)
        
        # 결과 출력
        print(f"Successfully loaded config: {config['metadata']['name']}")
        
    except ConfigValidationError as e:
        print("Validation errors:")
        for error in e.errors:
            print(f"  - {error}")
            
    except ConfigParseError as e:
        print(f"Parse error: {e}")
        

if __name__ == "__main__":
    main()
```

## 테스트 케이스 추가

새로운 기능이나 엣지 케이스를 테스트하려면:

1. **새 설정 파일 생성**: `../configs/` 폴더에 테스트용 설정 파일 추가
2. **스키마 수정**: 필요시 `../schemas/` 폴더의 스키마 파일 업데이트
3. **테스트 함수 추가**: 데모 스크립트에 새로운 테스트 함수 추가

## 디버깅 팁

### 상세한 오류 정보 출력
```python
try:
    config = parser.parse_from_file(config_path)
except ConfigValidationError as e:
    print(f"Validation failed: {e}")
    print("Detailed errors:")
    for i, error in enumerate(e.errors, 1):
        print(f"{i:2d}. {error}")
except ConfigParseError as e:
    print(f"Parse error: {e}")
    if e.details:
        print(f"Details: {e.details}")
```

### 설정 내용 확인
```python
import json
print("Parsed configuration:")
print(json.dumps(config, indent=2, ensure_ascii=False))
```

### 스키마 검증 단계별 실행
```python
# 1. 파싱만 (검증 없이)
content = parser._parse_content(file_content)
print("Parsing successful")

# 2. 검증 수행
parser.validate_configuration(content)
print("Validation successful")

# 3. 기본값 적용
final_config = parser.normalize_configuration(content)
print("Normalization successful")
```

## 성능 테스트

대용량 설정 파일이나 복잡한 스키마의 성능을 테스트하려면:

```python
import time

start_time = time.time()
config = parser.parse_from_file(large_config_path)
end_time = time.time()

print(f"Parsing took {end_time - start_time:.3f} seconds")
``` 