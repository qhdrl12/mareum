# ConfigParser 사용 예시

이 디렉토리는 `ConfigParser` 클래스의 사용법과 스키마 검증 기능을 보여주는 예시 파일들을 포함합니다.

> **권장 접근법**: 모든 설정 파일을 **YAML 형식**으로 작성하여 개발팀의 일관성과 유지보수성을 향상시킵니다.

## 파일 구조

```
examples/
├── README.md                 # 이 파일 (전체 개요)
# JSON 스키마는 프로젝트 루트의 schema.json 사용
├── configs/                  # 설정 파일 예시들 (YAML 중심)
│   ├── README.md            # 설정 파일 가이드
│   ├── valid_config.yaml    # 유효한 YAML 설정 파일 (권장)
│   └── invalid_config.yaml  # 검증 실패 예시 파일
└── scripts/                  # 데모 및 유틸리티 스크립트
    ├── README.md            # 스크립트 사용법
    └── demo_config_parser.py # ConfigParser 데모 스크립트
```

## YAML 중심 접근법

### 왜 YAML인가?

1. **개발자 친화적**: 주석, 멀티라인 문자열, 직관적 구조
2. **유지보수 용이**: 단일 포맷, 일관성, 높은 가독성
3. **협업 효율성**: 팀 전체가 하나의 형식만 학습
4. **버전 관리**: diff-friendly한 구조로 변경사항 추적 용이

### JSON vs YAML 비교

```yaml
# YAML - 읽기 쉽고 주석 지원
metadata:
  name: "customer-agent"     # 명확한 이름
  description: |
    여러 줄로 된 설명을
    자연스럽게 작성 가능

prompt:
  system: |
    You are a helpful assistant.
    Be polite and professional.
```

```json
// JSON - 구조적이지만 주석 불가, 멀티라인 어려움
{
  "metadata": {
    "name": "customer-agent",
    "description": "Multi-line descriptions require escape characters\nand are harder to read"
  },
  "prompt": {
    "system": "Single line prompts only, or complex escaping needed"
  }
}
```

## 사용법

### 1. 기본 사용법 (YAML 권장)

```python
from src.core.config_parser import ConfigParser

# 프로젝트 루트의 스키마 파일 사용
parser = ConfigParser(schema_path="schema.json")

# YAML 파일에서 설정 로드 (권장)
config = parser.parse_from_file("config.yaml")

# 문자열에서 직접 파싱 (YAML/JSON 모두 지원)
config = parser.parse_from_string(yaml_content)
```

### 2. 스키마 검증

프로젝트 루트의 `schema.json` 파일은 다음과 같은 구조로 설정 파일을 검증합니다:

- **metadata** (필수): 에이전트 메타데이터
- **model** (필수): LLM 모델 설정  
- **prompt** (필수): 프롬프트 설정
- **tools** (선택): 도구 설정 배열
- **memory** (선택): 메모리 설정
- **knowledge** (선택): 지식베이스 설정
- **deployment** (선택): 배포 설정

### 3. 에러 처리

```python
from src.core.config_parser import ConfigParser, ConfigParseError, ConfigValidationError

parser = ConfigParser(schema_path="schema.json")

try:
    config = parser.parse_from_file("config.yaml")
    print("설정 파일 로드 성공!")
    
except ConfigParseError as e:
    print(f"파싱 에러: {e}")
    
except ConfigValidationError as e:
    print(f"검증 에러: {e}")
    for error in e.errors:
        print(f"  - {error}")
```

## 데모 실행

```bash
# 프로젝트 루트에서 실행
python examples/scripts/demo_config_parser.py
```

데모 스크립트는 다음 기능들을 보여줍니다:
1. ✅ **YAML 파일 파싱** (주요 기능)
2. ⚠️ 검증 에러 처리
3. 📝 문자열에서 직접 파싱 (YAML 우선, JSON 호환)
4. 🔍 YAML 고급 기능 시연
5. 🎯 포맷 자동 감지 (YAML 우선 전략)

## 설정 파일 예시

### YAML 설정 (권장)
```yaml
# 고객 지원 에이전트 설정
metadata:
  name: "customer-support-agent"
  version: "1.2.0"
  description: |
    AI agent for handling customer support inquiries.
    Trained to be polite, helpful, and professional.

model:
  provider: "openai"
  name: "gpt-4"
  credentials_key: "OPENAI_API_KEY"
  temperature: 0.7  # 적절한 창의성

prompt:
  system: |
    You are a helpful customer support agent.
    Always be polite and professional.
    
    Guidelines:
    1. Ask clarifying questions when needed
    2. Provide accurate information
    3. Escalate complex issues appropriately

tools:
  - name: "search_knowledge_base"
    type: "search"
    description: "Search company knowledge base"
    config:
      index_name: "support_kb"
      max_results: 5

memory:
  type: "conversation_buffer_window"
  max_messages: 20
```

## 기본값 적용

스키마에 정의된 기본값들이 자동으로 적용됩니다:
- `metadata.version`: "1.0.0"
- `model.temperature`: 0.7
- `model.max_tokens`: 1000
- `deployment.port`: 8000
- `deployment.log_level`: "INFO"

## JSON 지원 정책

ConfigParser는 하위 호환성을 위해 JSON도 지원하지만, **새로운 프로젝트에서는 YAML 사용을 강력히 권장**합니다:

- ✅ **YAML**: 모든 새 설정 파일 (권장)
- ⚠️ **JSON**: 레거시 호환성을 위해서만 지원
- 🔄 **자동 감지**: 두 포맷 모두 투명하게 처리

### 마이그레이션이 필요한 경우

기존 JSON 설정을 YAML로 변환:

```bash
# Python을 이용한 자동 변환
python -c "
import json, yaml
with open('config.json') as f:
    data = json.load(f)
with open('config.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
"
```

## 주요 장점 요약

### YAML 단일 포맷 접근법
1. **개발 효율성** ⬆️
   - 학습 곡선 감소
   - 일관된 개발 경험
   - 더 빠른 온보딩

2. **코드 품질** ⬆️
   - 주석을 통한 자체 문서화
   - 멀티라인 프롬프트 지원
   - 구조화된 가독성

3. **유지보수성** ⬆️
   - 단일 포맷 유지
   - 버전 관리 최적화
   - 팀 협업 향상

4. **확장성** ⬆️
   - 복잡한 설정도 명확하게 표현
   - 환경별 설정 분리 용이
   - 템플릿화 가능

당신의 제안이 완전히 옳습니다. YAML 중심 접근법이 **코드 관리 및 유지보수 용이성** 측면에서 훨씬 효과적입니다! 