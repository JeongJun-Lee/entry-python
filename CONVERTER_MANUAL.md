# GitBook to PDF 원클릭 통합 컨버터 사용 설명서 (User Manual)

본 문서는 깃북(GitBook) 마크다운 프로젝트를 **한 번의 명령어 실행으로 출판물 품질의 단일 완성형 PDF 전자책으로 변환**해 주는 전용 컨버터(`convert_gitbook_to_pdf.py`)의 공식 사용 매뉴얼입니다.

---

## 1. 개요 (Overview)

기존에는 깃북 전용 문법(`{% tabs %}`, `{% hint %}`, `:1234:` 등)의 호환성 문제로 인해 다음과 같은 번거로운 3단계 수작업을 거쳐야 했습니다:
1. GitBook 전용 MD를 일반 MD로 1차 수동 변환 (`pub/` 디렉터리)
2. VS Code 확장 도구 등을 통해 챕터별 개별 PDF 수동 출력
3. 파이썬 스크립트로 개별 PDF들을 번호 순서대로 다시 병합

**본 컨버터는 이 모든 과정을 1회성 명령어로 완전 자동화**하여, `SUMMARY.md` 목차 트리와 원본 에셋(`.gitbook/assets/`)을 직접 읽어와 표지, 목차, 본문 챕터, 뒷표지까지 완벽하게 정돈된 고품질 PDF를 생성합니다.

---

## 2. 사전 요구사항 및 설치 (Installation)

### 1) 파이썬 환경
* Python 3.9 이상 권장

### 2) 필수 패키지 설치
프로젝트 루트 디렉터리에서 `requirements.txt`를 통해 필요한 라이브러리를 설치합니다:

```bash
pip install -r requirements.txt
```

#### `requirements.txt` 구성 패키지
* `weasyprint>=60.0`: W3C Paged Media 표준 기반 고품질 PDF 렌더링 엔진
* `markdown>=3.5`: Python-Markdown 파서 및 확장 모듈
* `pygments>=2.15`: 코드 블록 구문 강조(Syntax Highlighting) 엔진
* `pypdf>=5.0`: 생성된 PDF 검증 및 메타데이터 추출

> **참고 (macOS 시스템 라이브러리):**
> WeasyPrint가 내부적으로 사용하는 Pango/Cairo 라이브러리가 필요합니다. Homebrew가 설치된 Mac 환경에서는 아래 명령어로 설치할 수 있습니다:
> ```bash
> brew install pango cairo gdk-pixbuf libffi
> ```

---

## 3. 빠른 시작 (Quick Start)

터미널에서 프로젝트 루트 디렉터리로 이동한 후, 아래 명령어를 실행하면 즉시 전체 책 PDF가 빌드됩니다:

```bash
python3 convert_gitbook_to_pdf.py
```

* **기본 출력 경로**: `pub/pdf/Entry-Python_by_JJ.pdf`
* **소요 시간**: 약 15초 내외 (총 60페이지 기준)

---

## 4. CLI 명령어 옵션 안내 (CLI Options Reference)

다양한 출판 요구사항(표지 제외 인쇄용, 브라우저 미리보기, 맞춤 메타데이터 등)을 위해 다음과 같은 옵션을 지원합니다:

| 옵션 플래그 | 형태 | 기본값 | 설명 |
| :--- | :--- | :--- | :--- |
| `--summary` | 경로 문자열 | `SUMMARY.md` | 목차 구성을 파싱할 `SUMMARY.md` 파일 경로 |
| `--output` | 경로 문자열 | `pub/pdf/Entry-Python_by_JJ.pdf` | 생성될 PDF 파일의 저장 경로 |
| `--title` | 문자열 | `엔트리로 파이썬 기초 입문하기` | 도서 앞표지 및 메타데이터 제목 |
| `--subtitle` | 문자열 | `블록 코딩에서 텍스트 코딩으로의...` | 도서 앞표지 부제 |
| `--author` | 문자열 | `JJ (comseong@gmail.com)` | 저자 및 연락처 정보 |
| **`--no-cover`** | 플래그 | `False` | **앞표지와 뒷표지를 모두 제외** (본문 및 목차만 출력) |
| **`--no-front-cover`** | 플래그 | `False` | **앞표지만 제외** |
| **`--no-back-cover`** | 플래그 | `False` | **뒷표지만 제외** |
| `--keep-html` | 플래그 | `False` | PDF 생성 후 중간 생성된 HTML 파일도 함께 보존 |
| `--html-only` | 플래그 | `False` | PDF 렌더링 없이 브라우저 검수용 HTML 파일만 즉시 생성 |

---

## 5. 대표 사용 예제 (Usage Examples)

### 1) 앞/뒤 표지 모두 포함하여 기본 완성본 빌드
```bash
python3 convert_gitbook_to_pdf.py
```
> 앞표지(1p) + 목차(2p) + 본문(56p) + 뒷표지(1p) = 총 60페이지 완성본이 생성됩니다.

### 2) 표지 없이 본문/목차만 출력 (기존 인쇄용/외주 표지 결합용)
```bash
python3 convert_gitbook_to_pdf.py --no-cover --output pub/pdf/Entry-Python_inside_only.pdf
```
> 표지 2장이 제외된 58페이지 분량의 내지 전용 PDF가 생성됩니다.

### 3) 앞표지만 넣고 뒷표지는 제외할 때
```bash
python3 convert_gitbook_to_pdf.py --no-back-cover
```

### 4) 브라우저에서 HTML로 빠르게 디자인/내용만 검수할 때
```bash
python3 convert_gitbook_to_pdf.py --html-only
```
> `pub/pdf/Entry-Python_by_JJ.html`이 1초 내에 생성되어 웹 브라우저에서 즉시 열어볼 수 있습니다.

### 5) 저자명이나 도서 제목을 변경하여 빌드할 때
```bash
python3 convert_gitbook_to_pdf.py \
  --title "엔트리 파이썬 마스터" \
  --subtitle "한 권으로 끝내는 텍스트 코딩 입문" \
  --author "홍길동 (dev@example.com)" \
  --output pub/pdf/custom_book.pdf
```

---

## 6. 주요 기능 및 변환 규칙 상세

### 1) `SUMMARY.md` 기반 자동화
* 책의 전체 목차 계층(1단계 대분류, 2단계 챕터)을 자동으로 읽어와 순서대로 본문을 조립합니다.
* 링크된 마크다운 파일들의 상대 경로 에셋도 실제 파일 위치를 기준으로 오차 없이 찾아냅니다.

### 2) 목차(Table of Contents) 실시간 연동
* CSS Paged Media의 `target-counter(attr(href), page)` 및 `leader('.')` 속성을 사용하여, 본문 페이지 번호가 변경되더라도 목차의 점선 리더와 페이지 번호가 자동으로 100% 동기화됩니다.

### 3) 깃북 전용 문법 변환
* **탭(`{% tabs %}`)**: 인쇄 매체 특성에 맞추어 상단에 탭 식별 뱃지(`실행결과`, `블록코딩`, `엔트리-파이썬`)가 달린 세로형 비교 카드(`gb-tabs-card`)로 통합 렌더링되며, 탭 헤더만 다음 장으로 넘어가는 현상을 원천 방지(`page-break-inside: avoid`)합니다.
* **콜아웃 힌트(`{% hint %}`)**: 정보(`info`), 주의(`warning`), 위험(`danger`), 성공(`success`) 4가지 테마에 맞는 전용 박스와 깨짐 없는 벡터 SVG 아이콘을 제공합니다.
* **코드 라인 분석 기호(`:1234:`)**: 원형 코드 태그(`< / >`) 벡터 블루 뱃지로 치환되어 본문 가독성을 극대화합니다.
* **취소선 회피 역슬래시(`\~`)**: `8\~17번`과 같은 문구를 깔끔한 `8~17번`으로 자동 정규화합니다.

### 4) 고가독성 코드 블록
* Pygments 기반의 고대비 라이트 테마(`vs`)를 적용하여 소프트 화이트(`#f8fafc`) 배경 위에 선명한 색상으로 키워드, 함수명, 주석을 표현합니다.
* 좌측 라인 넘버(`linenos`)와 본문 코드의 행간(`line-height: 16pt`)을 1:1로 일치시켜 줄 번호가 어긋나지 않습니다.
* HTML `<pre class="language-python">` 형태로 작성된 블록도 표준 구문 강조 블록으로 자동 승격 변환합니다.

### 5) 에셋 및 표(Table) 최적화
* 파일명에 공백이나 괄호(`(8).png`)가 포함된 마크다운 이미지 URL(`![](<path>)`)도 빠짐없이 절대 경로로 변환합니다.
* 표 내부 이미지의 경우 적정 높이(`max-height: 42px`)와 상하 중앙 정렬을 적용하여 표 형태가 무너지지 않도록 보호합니다.
* 볼드(`**...**`) 서식이 적용된 하이퍼링크도 링크 고유의 파란색과 밑줄을 정상적으로 유지합니다.

---

## 7. 문제 해결 (Troubleshooting)

### Q1. WeasyPrint 라이브러리 관련 에러가 발생할 때
* `dlopen()` 또는 `cairo / pango` 관련 에러가 발생한다면 운영체제 라이브러리가 미설치된 상태일 수 있습니다.
  * Mac: `brew install pango cairo gdk-pixbuf`
  * Ubuntu/Debian: `sudo apt-get install libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0`

### Q2. 폰트가 깨지거나 네모 박스로 보일 때
* 컨버터는 기본적으로 Google Web Fonts의 `Noto Sans KR`과 코딩용 고정폭 글꼴 `JetBrains Mono`를 임베드합니다. 인터넷이 연결된 환경에서 최초 빌드 시 글꼴을 자동으로 다운로드하여 적용합니다.

---

## 8. 라이선스 및 문의
* **저자**: JJ ([comseong@gmail.com](mailto:comseong@gmail.com))
* **라이선스**: Creative Commons BY-NC-SA 4.0
