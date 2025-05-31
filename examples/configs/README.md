# 설정 파일 예시들

이 폴더는 ConfigParser로 파싱할 수 있는 YAML 설정 파일 예시들을 포함합니다.

> **ConfigParser는 이제 YAML 전용입니다**: 단순성과 개발 효율성을 위해 YAML 형식만 지원합니다.

## 파일 목록

### 표준 설정 파일들

#### `valid_agent.yaml`
- **형식**: YAML (유일한 지원 형식)
- **에이전트 타입**: 고객 지원 에이전트 (Customer Support Agent)
- **주요 특징**:
  - OpenAI GPT-4 모델 사용
  - 멀티라인 시스템 프롬프트 (YAML `|` 구문 활용)
  - 2개의 도구 (지식베이스 검색, 티켓 생성)
  - Pinecone 벡터 데이터베이스 연동
  - Conversation buffer window 메모리

#### `default_agent.yaml`
- **기본 ReAct 에이전트**: 가장 간단한 설정 예시
- **OpenAI GPT-4**: 웹 검색 도구 포함

#### `example_agent.yaml`
- **고급 고객 지원 에이전트**: API 기반 도구들
- **API 통합**: 지식베이스, 티켓 시스템, CRM 연동

#### `bedrock_agent.yaml`
- **AWS Bedrock Claude**: 엔터프라이즈 AI 에이전트
- **AWS 서비스 통합**: RDS, Lambda 연동

#### `openai_agent.yaml`
- **OpenAI API 배포**: 클라우드 기반 GPT-4o-mini 사용
- **문서 검색**: OpenAI 임베딩 모델 활용

### 검증 테스트 파일

#### `invalid_agent.yaml`
- **목적**: 검증 오류 시연용
- **포함된 오류들**:
  - 필수 필드 누락 (`metadata.name`, `model.credentials_key`, `prompt.system`)
  - 잘못된 타입 (문자열 대신 배열)
  - enum 값 위반 (`model.provider`, `memory.type`)
  - 범위 초과 (`model.temperature`, `deployment.port`)
  - 최소값 미만 (`model.max_tokens`, `memory.max_messages`)

## 표준 설정 구조

모든 설정 파일은 다음과 같은 **통일된 구조**를 따릅니다:

### 필수 섹션

```yaml
metadata:
  name: "agent-name"           # 필수
  description: "설명"          # 권장
  version: "1.0.0"            # 권장

model:
  provider: "openai"          # 필수: openai, anthropic, aws_bedrock, etc.
  name: "gpt-4"              # 필수
  credentials_key: "API_KEY"  # 필수
  temperature: 0.7            # 선택적 (플랫 구조)
  max_tokens: 1500           # 선택적 (플랫 구조)

prompt:
  system: |                  # 필수 (멀티라인 권장)
    You are a helpful assistant.
```

### 선택적 섹션

```yaml
tools:
  - name: "tool_name"
    type: "function"          # function, api, search 중 하나
    description: "설명"
    config:                   # 통일된 config 구조
      module: "src.tools.module"      # function 타입용
      function: "function_name"       # function 타입용
      endpoint: "https://api.com"     # api 타입용
      method: "POST"                  # api 타입용
      required_params: ["param1"]     # 필수 매개변수들
      optional_params: ["param2"]     # 선택적 매개변수들

memory:
  type: "conversation_buffer_window"  # 통일된 타입명
  max_messages: 20                   # k 대신 max_messages 사용

knowledge:
  provider: "pinecone"        # pinecone, chroma, faiss, etc.
  collection_name: "kb-name"
  embedding_model: "text-embedding-ada-002"
  search_config:
    top_k: 5
    score_threshold: 0.7

deployment:
  port: 8080
  host: "0.0.0.0"
  enable_cors: true
  log_level: "INFO"
```

## 통일된 용어 가이드

### 🔧 **Model 섹션**
- ✅ **플랫 구조**: `temperature`, `max_tokens` 직접 배치
- ❌ **중첩 구조**: `parameters.temperature` 방식 사용 금지

### 💬 **Prompt 섹션**
- ✅ **표준 필드**: `system` (시스템 프롬프트)
- ❌ **비표준 필드**: `system_prompt`, `react_template` 사용 금지

### 🧠 **Memory 섹션**
- ✅ **표준 필드**: `max_messages` (메시지 개수)
- ❌ **비표준 필드**: `config.k` 방식 사용 금지

### 🔨 **Tools 섹션**
- ✅ **표준 구조**: `config` 객체 내부에 설정
- ✅ **매개변수**: `required_params`, `optional_params` 배열
- ❌ **비표준**: `parameters` 객체 배열 방식 사용 금지

## 파일명 규칙

모든 설정 파일은 일관된 네이밍 규칙을 따릅니다:

### ✅ **표준 파일명 형식**: `*_agent.yaml`
- `valid_agent.yaml` - 표준 유효한 설정
- `invalid_agent.yaml` - 검증 오류 테스트용
- `default_agent.yaml` - 기본 에이전트
- `example_agent.yaml` - 고급 예시 에이전트
- `bedrock_agent.yaml` - AWS Bedrock 에이전트
- `openai_agent.yaml` - OpenAI API 배포 에이전트

### ❌ **비표준 형식 사용 금지**
- `*_config.yaml` - 더 이상 사용하지 않음
- `config_*.yaml` - 접두사 형식 사용 금지
- `*.json` - JSON 형식 지원 중단

## 사용법 예시

### YAML 파일 파싱
```python
from src.core.config_parser import ConfigParser

parser = ConfigParser(schema_path="examples/schemas/example_schema.json")
config = parser.parse_from_file("examples/configs/valid_agent.yaml")

print(f"Agent: {config['metadata']['name']}")
print(f"Model: {config['model']['provider']} - {config['model']['name']}")
```

### 검증 오류 확인
```python
try:
    config = parser.parse_from_file("examples/configs/invalid_agent.yaml")
except ConfigValidationError as e:
    for error in e.errors:
        print(f"Validation error: {error}")
```

## YAML 전용 접근법의 장점

### 1. 개발자 친화성
```yaml
# 주석으로 설정 설명 가능
metadata:
  name: "customer-support-agent"  # 명확한 이름
  description: |
    여러 줄로 된 설명을
    자연스럽게 작성 가능
```

### 2. 가독성과 유지보수성
- **직관적 구조**: 들여쓰기로 계층 구조 표현
- **주석 지원**: 설정의 의도와 맥락을 문서화
- **멀티라인 문자열**: 프롬프트나 설명을 자연스럽게 작성
- **diff 친화적**: 버전 관리 시 변경사항 추적 용이

### 3. 단순함과 일관성
- **하나의 형식**: 팀 전체가 하나의 형식만 학습
- **일관된 스타일**: 모든 설정 파일이 동일한 패턴
- **통일된 용어**: 표준화된 필드명과 구조
- **통일된 파일명**: `*_agent.yaml` 형식으로 일관성

## YAML 모범 사례

### 1. 주석 활용
```yaml
# 에이전트 기본 정보
metadata:
  name: "customer-agent"
  # 버전 관리용 (자동 업데이트됨)
  version: "1.0.0"
```

### 2. 멀티라인 문자열
```yaml
prompt:
  # 리터럴 스타일: 개행 보존
  system: |
    You are a customer support agent.
    Always be polite and helpful.
    Ask clarifying questions when needed.
```

### 3. 구조화된 도구 설정
```yaml
tools:
  - name: "search_knowledge_base"
    type: "api"
    description: "Search internal knowledge base"
    config:
      endpoint: "https://api.company.com/kb/search"
      method: "POST"
      required_params: ["query"]
      optional_params: ["limit"]
```

## 파일 확장자 규칙

ConfigParser는 다음 확장자만 허용합니다:
- ✅ `.yaml` (권장)
- ✅ `.yml` (허용)
- ❌ `.json` (지원 중단)
- ❌ 기타 모든 형식

## 마이그레이션 없음

오픈 전 제품이므로 기존 JSON 파일에서 마이그레이션할 필요가 없습니다. 
모든 새 설정 파일은 처음부터 **통일된 YAML 구조**와 **표준 파일명 형식**으로 작성하세요. 