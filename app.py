
import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional

import streamlit as st


# =========================================================
# 공통 유틸리티
# =========================================================

METHOD_ALIASES = {
    "정의": {"정의", "뜻", "개념"},
    "예시": {"예시", "예", "사례"},
    "인과": {"인과", "원인과 결과", "원인 결과"},
    "분석": {"분석", "요소", "구성"},
    "비교와 대조": {"비교와 대조", "비교대조", "비교", "대조"},
    "분류와 구분": {"분류와 구분", "분류구분", "분류", "구분"},
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.lower().strip()
    text = re.sub(r"[“”‘’\"']", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def compact(text: str) -> str:
    return re.sub(r"\s+", "", normalize(text))


def contains_any(text: str, expressions: Set[str] | List[str]) -> bool:
    t = compact(text)
    return any(compact(x) in t for x in expressions)


def count_groups(text: str, groups: List[Set[str]]) -> int:
    return sum(1 for group in groups if contains_any(text, group))


def contradiction_found(text: str, contradictions: List[Set[str]]) -> Tuple[bool, str]:
    for group in contradictions:
        if contains_any(text, group):
            return True, sorted(group)[0]
    return False, ""


def extract_declared_method(text: str) -> Optional[str]:
    candidates = re.findall(r"\(([^()]*)\)", normalize(text))
    for candidate in reversed(candidates):
        for canonical, aliases in METHOD_ALIASES.items():
            if contains_any(candidate, aliases):
                return canonical
    return None


def remove_method_label(text: str) -> str:
    return re.sub(r"\([^()]*\)\s*$", "", text or "").strip()


# =========================================================
# 설명 방법 탐지
# =========================================================

def detect_definition(sentence: str) -> bool:
    s = normalize(sentence)
    patterns = [
        r".+(?:이란|란)\s+.+(?:말한다|뜻한다|이다|현상이다|것이다)",
        r".+(?:은|는)\s+.+(?:을|를)\s+말한다",
        r".+(?:은|는)\s+.+(?:인|하는)\s+(?:현상|전기|작품|방법|과제)이다",
    ]
    return any(re.search(p, s) for p in patterns)


def detect_example(sentence: str) -> bool:
    s = normalize(sentence)
    markers = {"예를 들어", "가령", "대표적으로", "예로", "사례로"}
    concrete = {
        "커피숍", "도서관", "공부 모임", "피겨 스케이팅", "올림픽",
        "폭포", "저수지", "댐", "수조", "에드몽 드 벨라미"
    }
    return contains_any(s, markers) or contains_any(s, concrete)


def detect_cause_effect(sentence: str) -> bool:
    s = normalize(sentence)
    causes = {"때문에", "그러므로", "따라서", "그래서", "결과적으로", "므로", "하여", "해서"}
    results = {
        "좋다", "효율적", "위험하지", "예술로 보기 어렵", "예술로 볼 수",
        "강조", "전달", "드러", "감동", "울림", "집중해야"
    }
    return contains_any(s, causes) and contains_any(s, results)


def detect_analysis(sentence: str) -> bool:
    s = normalize(sentence)
    components = {
        "감정", "철학", "경험", "관점", "환경", "전압", "전하", "위험성",
        "혼자", "집중", "연습", "익숙"
    }
    component_count = sum(1 for c in components if contains_any(s, {c}))
    structure = contains_any(s, {"이루어", "구성", "요소", "부분", "에는", "특징은", "방법에는"})
    return structure and component_count >= 2


def detect_compare(sentence: str) -> bool:
    s = normalize(sentence)
    markers = {"반면", "하지만", "그러나", "와 달리", "과 달리", "차이", "공통점", "둘 다", "반대로", "지만"}
    target_pairs = [
        ("쉬운 과제", "어려운 과제"),
        ("실생활 전기", "정전기"),
        ("인간", "인공 지능"),
        ("인간의 예술", "인공 지능의 그림"),
        ("인간 선수", "로봇"),
    ]
    has_pair = any(contains_any(s, {a}) and contains_any(s, {b}) for a, b in target_pairs)
    return has_pair and contains_any(s, markers)


def detect_classification(sentence: str) -> bool:
    s = normalize(sentence)
    markers = {"나뉘", "나눌 수", "구분", "분류", "묶", "종류"}
    criteria = {"에 따라", "기준", "여부", "난이도", "창작 주체"}
    target_pairs = [
        ("쉬운 과제", "어려운 과제"),
        ("실생활 전기", "정전기"),
        ("인간", "인공 지능"),
    ]
    has_pair = any(contains_any(s, {a}) and contains_any(s, {b}) for a, b in target_pairs)
    return contains_any(s, markers) and contains_any(s, criteria) and has_pair


METHOD_DETECTORS = {
    "정의": detect_definition,
    "예시": detect_example,
    "인과": detect_cause_effect,
    "분석": detect_analysis,
    "비교와 대조": detect_compare,
    "분류와 구분": detect_classification,
}


def detect_methods(sentence: str) -> Set[str]:
    body = remove_method_label(sentence)
    return {name for name, detector in METHOD_DETECTORS.items() if detector(body)}


# =========================================================
# 데이터
# =========================================================

SETS = {
    "1세트: 사회적 촉진·억제": {
        "emoji": "🧠",
        "short": "사회적 촉진",
        "title": "과제 난이도와 사회적 촉진/억제",
        "passage": """
[기자] 사회적 촉진과 억제를 일상생활에 어떻게 적용할 수 있을까요?

[전문가] 비교적 쉬운 취미 생활이나 큰 노력을 들일 필요가 없는 과제를 할 때는 커피숍이나 도서관에서 하거나 공부 모임을 만드는 것이 효율적일 수 있습니다. 반대로 지나치게 어렵거나 도전이 필요한 과제는 차분하게 혼자 집중하는 시간을 가지는 것이 좋습니다.
""",
        "guide_boxes": [
            {
                "title": "📚 1. 설명 방법 공식",
                "items": [
                    "정의: ~란 ~를 말한다.",
                    "예시: 예를 들어 ~",
                    "인과: ~ 때문에 ~하다.",
                    "비교와 대조: [공통점] ~와 ~의 공통점은 ~이다. / [차이점] ~는 ~이지만, ~는 ~이다.",
                    "분석: ~는 ~와(과) ~로 이루어져 있다.",
                    "분류와 구분: ~는 ~라는 기준에 따라 ~와(과) ~로 나뉜다.",
                ],
                "tip": "2번 문제 풀이 팁: 위 공식을 활용해 문장을 만드세요! 서로 다른 두 방법을 사용해야 합니다.",
                "tip_color": "#eaf3ff",
            },
            {
                "title": "🎬 2. 영상 매체와 복합양식성",
                "items": [
                    "복합양식성: 문자, 소리, 그림, 사진, 동영상 등 다양한 양식이 결합된 것",
                    "시각 요소: 인물, 표정, 행동, 배경, 색감, 자막 등",
                    "청각 요소: 대사, 내레이션, 효과음, 배경음악, 정적 등",
                ],
                "tip": "3번 문제 풀이 팁: 효과를 쓸 때는 앞에서 쓴 요소가 본문의 어떤 내용을 보여 주는지 연결해서 쓰세요.",
                "tip_color": "#fff6d8",
            },
        ],
        "q1": {
            "button_label": "🖍️ 1번 빈칸 채우기",
            "desc": "[서·논술형 1] 윗글을 요약하여 표로 정리하였다. 빈칸 ㉠~㉢에 들어갈 내용을 찾아 쓰시오.",
            "table_headers": ["과제의 특성", "환경", "현상"],
            "table_rows": [
                ["㉠", "공부 모임 등 여러 명이 함께함", "사회적 촉진"],
                ["어려운 과제", "㉡", "㉢"],
            ],
            "answer_labels": ["(1) ㉠", "(1) ㉡", "(1) ㉢"],
            "rules": {
                "㉠": {
                    "required_groups": [{"쉬운 과제", "비교적 쉬운 과제", "어렵지 않은 과제", "큰 노력이 필요하지 않은 과제", "큰 노력이 들지 않는 과제"}],
                    "contradictions": [{"어려운 과제", "도전이 필요한 과제", "복잡한 과제"}],
                    "model": "비교적 쉽거나 큰 노력을 들일 필요가 없는 과제",
                },
                "㉡": {
                    "required_groups": [{"혼자", "혼자서", "개별적으로", "다른 사람 없이"}, {"집중", "차분하게", "연습", "반복", "익숙해질 때까지"}],
                    "contradictions": [{"함께", "공부 모임", "여럿이"}],
                    "model": "충분히 연습하여 익숙해질 때까지 차분하게 혼자 집중함",
                },
                "㉢": {
                    "required_groups": [{"사회적 억제"}],
                    "contradictions": [{"사회적 촉진"}],
                    "model": "사회적 억제",
                },
            },
        },
        "q2": {
            "button_label": "📘 2번 설명문 쓰기",
            "desc": "[서·논술형 2] 다음 첫 문장에 이어, 윗글의 내용을 바탕으로 서로 다른 설명 방법을 활용한 문장 2개를 쓰시오.",
            "starter": "과제의 특성과 난이도에 따라 우리의 학습 효율을 높이는 방법은 다르게 적용되어야 한다.",
            "conditions": [
                "두 문장은 서로 다른 설명 방법을 사용해야 함",
                "윗글의 내용만 활용할 것",
                "설명 방법을 적는 경우 문장 끝에 괄호로 표시할 것",
            ],
            "passage_groups": [
                {"쉬운 과제", "비교적 쉬운 과제", "친숙한 과목", "좋아하는 과목"},
                {"함께", "다른 사람", "커피숍", "도서관", "공부 모임"},
                {"어려운 과제", "도전이 필요한 과제", "복잡한 과제"},
                {"혼자", "집중", "연습", "익숙해질 때까지", "차분하게"},
            ],
            "contradictions": [
                {"쉬운 과제는 혼자", "쉬운 과제를 혼자"},
                {"어려운 과제는 함께", "어려운 과제를 함께"},
            ],
            "required_conclusion": [
                {"쉬운 과제", "친숙한 과목"},
                {"함께", "다른 사람", "커피숍", "도서관", "공부 모임"},
                {"어려운 과제", "도전이 필요한 과제"},
                {"혼자", "집중", "연습", "익숙해질 때까지"},
            ],
            "models": {
                "비교와 대조 + 예시": [
                    "비교적 쉬운 과제는 다른 사람들과 함께하는 것이 효율적이지만, 지나치게 어렵거나 도전이 필요한 과제는 혼자 집중하는 것이 효율적이다. (비교와 대조)",
                    "예를 들어 친숙하고 좋아하는 과목은 공부 모임을 만들어 다른 사람들과 함께 공부할 수 있다. (예시)",
                ],
                "분류와 구분 + 예시": [
                    "과제는 난이도에 따라 비교적 쉬운 과제와 지나치게 어려운 과제로 나눌 수 있다. (분류와 구분)",
                    "예를 들어 쉬운 과제는 도서관이나 커피숍에서 하고, 어려운 과제는 혼자 연습할 수 있다. (예시)",
                ],
            },
        },
        "q3": {
            "button_label": "🎞️ 3번 영상 기획",
            "desc": "[서·논술형 3] 장면 2를 완성하기 위해 시각 요소와 청각 요소, 그리고 각 요소의 효과를 쓰시오.",
            "plan_title": "영상 매체와 복합양식성",
            "plan": """
**영상 제목:** 과제 난이도에 맞는 학습 전략

**장면 1**  
- 시각: 여러 학생이 함께 공부하는 모습  
- 청각: 밝은 분위기의 배경음악, 책 넘기는 소리

**장면 2**  
- 시각 요소: Ⓐ  
- 청각 요소: Ⓑ
""",
            "visual_element_groups": [
                {"혼자", "한 학생", "개별적으로"},
                {"집중", "연습", "반복", "틀린 문제", "다시 확인"},
            ],
            "audio_element_groups": [{"조용", "정적", "무음", "말소리 없음", "소리 제거", "잔잔"}],
            "visual_effect_groups": [
                {"혼자", "개별적으로"},
                {"어려운 과제", "도전이 필요한 과제"},
                {"집중", "연습", "익숙해질 때까지", "차분하게"},
            ],
            "audio_effect_groups": [
                {"차분", "조용", "방해가 없", "집중"},
                {"어려운 과제", "도전이 필요한 과제"},
            ],
            "contradictions": [{"여럿이 떠들", "친구들과 시끄럽게"}, {"기억력이 세 배", "도파민", "뇌파"}],
            "models": {
                "시각 요소": "한 학생이 조용한 공간에서 혼자 어려운 문제를 반복해서 풀고 틀린 문제를 다시 확인하는 모습을 보여 준다.",
                "시각 효과": "학생이 혼자 반복해서 연습하는 모습을 통해 어려운 과제는 익숙해질 때까지 차분하게 혼자 집중해야 한다는 점을 전달한다.",
                "청각 요소": "사람들의 말소리와 경쾌한 음악은 없애고, 연필로 문제를 푸는 소리와 책장 넘기는 소리만 작게 들려준다.",
                "청각 효과": "주변 소리를 줄인 차분한 분위기를 통해 어려운 과제는 방해를 받지 않고 혼자 집중해서 연습하는 것이 좋다는 점을 강조한다.",
            },
        },
    },

    "2세트: 정전기": {
        "emoji": "⚡",
        "short": "정전기",
        "title": "정전기의 뜻과 특징",
        "passage": """
[기자] 겨울철 불청객인 정전기는 어떤 특징이 있나요?

[전문가] 정전기란 전하가 정지 상태로 있어 그 분포가 시간적으로 변화하지 않는 전기와 그로 인한 전기 현상을 말합니다. 실생활에서 사용하는 전기가 흐르는 물이라면, 정전기는 높은 곳에 고여 있는 물과 같습니다. 정전기의 전압은 높지만 전하가 이동하지 않고 머물러 있어 위험하지는 않습니다.
""",
        "guide_boxes": [
            {
                "title": "📚 1. 설명 방법 공식",
                "items": [
                    "정의: ~란 ~를 말한다.",
                    "비교와 대조: A는 ~이지만 B는 ~이다.",
                    "인과: ~이기 때문에 ~하다.",
                ],
                "tip": "2번 문제 풀이 팁: 정전기의 뜻과 실생활 전기와의 차이를 활용하면 좋습니다.",
                "tip_color": "#eaf3ff",
            },
            {
                "title": "🎬 2. 영상 기획 힌트",
                "items": [
                    "정전기 = 높은 곳에 고여 있는 물",
                    "전하가 이동하지 않고 머무름",
                    "전압은 높지만 위험하지 않음",
                ],
                "tip": "3번 문제 풀이 팁: ‘흐르지 않음’과 ‘고요함’을 시각·청각으로 표현해 보세요.",
                "tip_color": "#fff6d8",
            },
        ],
        "q1": {
            "button_label": "🖍️ 1번 빈칸 채우기",
            "desc": "[서·논술형 1] 윗글을 요약한 표의 빈칸 ㉠~㉢에 들어갈 내용을 쓰시오.",
            "table_headers": ["대상", "물의 상태에 비유", "전하의 상태", "위험성"],
            "table_rows": [
                ["실생활 전기", "흐르는 물", "전하가 이동함", "감전 등의 위험이 있음"],
                ["정전기", "㉠", "㉡", "㉢"],
            ],
            "answer_labels": ["(1) ㉠", "(1) ㉡", "(1) ㉢"],
            "rules": {
                "㉠": {
                    "required_groups": [{"높은 곳", "높은 위치", "위쪽"}, {"고여 있는 물", "머물러 있는 물", "흐르지 않는 물", "저장된 물"}],
                    "contradictions": [{"흐르는 물", "폭포", "떨어지는 물"}],
                    "model": "높은 곳에 고여 있는 물",
                },
                "㉡": {
                    "required_groups": [{"전하"}, {"이동하지 않", "머물", "정지 상태", "흐르지 않", "제자리에"}],
                    "contradictions": [{"전하가 빠르게 이동", "전하가 흐름"}],
                    "model": "전하가 이동하지 않고 머물러 있음",
                },
                "㉢": {
                    "required_groups": [{"위험하지 않", "피해가 없", "위험성이 낮", "감전 위험이 없"}],
                    "contradictions": [{"매우 위험", "감전 위험이 크"}, {"전압이 낮아서"}],
                    "model": "전압은 높지만 전하가 이동하지 않아 위험하지 않음",
                },
            },
        },
        "q2": {
            "button_label": "📘 2번 설명문 쓰기",
            "desc": "[서·논술형 2] 정전기의 특징을 설명하는 두 문장을 서로 다른 설명 방법으로 작성하시오.",
            "starter": "겨울철에 흔히 겪는 정전기는 우리가 평소 집에서 사용하는 전기와는 다른 뚜렷한 특징이 있다.",
            "conditions": [
                "두 문장은 서로 다른 설명 방법을 사용해야 함",
                "윗글의 내용만 활용할 것",
                "두 문장이 이어지도록 쓸 것",
            ],
            "passage_groups": [
                {"정전기", "전하"},
                {"정지 상태", "이동하지 않", "머물", "흐르지 않"},
                {"실생활 전기", "흐르는 물"},
                {"높은 곳에 고여 있는 물", "고여 있는 물"},
                {"위험하지 않", "피해가 없"},
            ],
            "contradictions": [
                {"전압이 낮아서", "전압이 낮기 때문에"},
                {"전하가 빠르게 이동", "전하가 많이 흐름"},
                {"겨울이 건조해서", "수분이 부족해서"},
            ],
            "required_conclusion": [
                {"정전기"},
                {"정지 상태", "이동하지 않", "머물", "흐르지 않"},
                {"위험하지 않", "실생활 전기와 다르", "차이"},
            ],
            "models": {
                "정의 + 비교와 대조": [
                    "정전기란 전하가 정지 상태로 있어 그 분포가 시간적으로 변하지 않는 전기와 그로 인한 전기 현상을 말한다. (정의)",
                    "실생활에서 사용하는 전기는 전하가 이동하지만, 정전기는 전하가 이동하지 않고 머물러 있다는 차이가 있다. (비교와 대조)",
                ],
                "비교와 대조 + 인과": [
                    "실생활 전기가 흐르는 물과 같다면 정전기는 높은 곳에 고여 있는 물과 같다. (비교와 대조)",
                    "정전기는 전하가 이동하지 않기 때문에 전압이 매우 높아도 위험하지 않다. (인과)",
                ],
            },
        },
        "q3": {
            "button_label": "🎞️ 3번 영상 기획",
            "desc": "[서·논술형 3] 정전기의 특성이 드러나도록 장면 2의 시각 요소와 청각 요소, 각 효과를 쓰시오.",
            "plan_title": "영상 매체와 복합양식성",
            "plan": """
**영상 제목:** 전압은 높지만 위험하지 않은 정전기의 비밀

**장면 1**  
- 시각: 거대한 폭포가 쏟아지는 모습  
- 청각: 웅장한 물소리

**장면 2**  
- 시각 요소: Ⓐ  
- 청각 요소: Ⓑ
""",
            "visual_element_groups": [{"높은 곳", "높은 절벽", "댐", "저수지", "높은 수조"}, {"고여", "흐르지 않", "떨어지지 않", "정지"}],
            "audio_element_groups": [{"정적", "무음", "고요", "잔잔", "거센 물소리 없음", "폭포 소리 제거"}],
            "visual_effect_groups": [{"전하"}, {"이동하지 않", "머물", "정지 상태"}, {"위험하지 않", "피해가 없", "전압이 높아도"}],
            "audio_effect_groups": [{"전하"}, {"이동하지 않", "머물", "정지 상태"}],
            "contradictions": [{"폭포처럼 쏟아", "물이 세차게 흐르"}, {"전압이 낮아서", "전압을 낮춘다"}],
            "models": {
                "시각 요소": "높은 절벽 위의 저수지에 많은 물이 고여 있지만 아래로 흐르거나 떨어지지 않는 모습을 보여 준다.",
                "시각 효과": "높은 곳에 물이 고여 움직이지 않는 모습을 통해 정전기는 전압이 높아도 전하가 이동하지 않고 머물러 있어 위험하지 않다는 점을 전달한다.",
                "청각 요소": "폭포처럼 물이 거세게 흐르는 소리는 없애고, 아주 약한 물결 소리만 들려준다.",
                "청각 효과": "거센 물소리가 없는 고요한 상태를 통해 정전기의 전하가 이동하지 않고 머물러 있다는 점을 강조한다.",
            },
        },
    },

    "3세트: 인공 지능 예술": {
        "emoji": "🎨",
        "short": "인공지능 예술",
        "title": "인공 지능이 그린 그림의 예술적 가치",
        "passage": """
우리가 올림픽에 열광하는 이유는 선수들의 노력과 열정을 알기 때문입니다. 반면 로봇이 한 번의 실수 없이 완벽하게 피겨 스케이팅을 하더라도 우리의 마음을 울리지는 못합니다.

인간의 작품에는 작가의 감정과 철학, 삶의 경험, 세상을 바라보는 관점, 주변 환경이 종합적으로 담겨 있으므로 예술로 볼 수 있습니다. 하지만 인공 지능은 감정을 느끼지 못하고 독자적인 철학이나 이야기가 없기 때문에 그 그림을 인간의 예술과 같다고 보기는 어렵습니다.

다만 인공 지능의 그림은 기존 미술계에 큰 변화를 가져왔고, 예술의 범주를 확장할 수 있다는 점에서 상징적인 가치가 있습니다.
""",
        "guide_boxes": [
            {
                "title": "📚 1. 설명 방법 공식",
                "items": [
                    "비교와 대조: 인간 예술과 인공 지능 그림의 차이를 밝힌다.",
                    "인과: ~이기 때문에 ~하다.",
                    "예시: 올림픽 선수와 로봇의 사례를 활용할 수 있다.",
                ],
                "tip": "2번 문제 풀이 팁: 인간 예술의 특성과 인공 지능 그림의 한계를 비교해 보세요.",
                "tip_color": "#eaf3ff",
            },
            {
                "title": "🎬 2. 영상 기획 힌트",
                "items": [
                    "작가의 감정·철학·경험·관점·환경",
                    "감상자에게 주는 감동과 울림",
                    "시각 요소와 청각 요소를 각각 구체적으로 제시",
                ],
                "tip": "3번 문제 풀이 팁: 작가의 내면이 작품에 담기는 장면과 감정적인 소리를 연결하세요.",
                "tip_color": "#fff6d8",
            },
        ],
        "q1": {
            "button_label": "🖍️ 1번 빈칸 채우기",
            "desc": "[서·논술형 1] 인공 지능 예술에 대한 글을 요약한 표의 빈칸 ㉠~㉢을 채우시오.",
            "table_headers": ["대상", "올림픽 경기에 비유", "예술로 볼 수 있는가", "예술로서의 가치"],
            "table_rows": [
                ["인간의 예술", "인간 선수의 노력과 열정이 담긴 경기", "작가의 경험·관점·환경이 담겨 있으므로 예술임", "감상자에게 감동을 줌"],
                ["인공 지능의 예술", "㉠", "㉡", "㉢"],
            ],
            "answer_labels": ["(1) ㉠", "(1) ㉡", "(1) ㉢"],
            "rules": {
                "㉠": {
                    "required_groups": [{"로봇"}, {"완벽", "한 번의 실수 없이"}, {"피겨 스케이팅", "경기"}],
                    "contradictions": [{"인간 선수"}],
                    "model": "한 번의 실수 없이 완벽하게 피겨 스케이팅을 하는 로봇",
                },
                "㉡": {
                    "required_groups": [{"감정이 없", "감정을 느끼지 못", "철학이 없", "이야기가 없", "경험이 없", "관점이 없"}, {"예술로 보기 어렵", "인간의 예술과 같다고 보기 어렵", "예술로 인정하기 어렵"}],
                    "contradictions": [{"기술이 부족해서"}, {"가격이 낮아서"}, {"아무 가치도 없"}],
                    "model": "감정도 느끼지 못하고 독자적인 철학이나 이야기가 없으므로 예술로 보기 어렵다.",
                },
                "㉢": {
                    "required_groups": [{"미술계에 변화", "미술계의 변화", "예술의 범주를 확장", "예술의 범위를 넓", "새로운 예술 가능성"}, {"가치", "의미", "상징적"}],
                    "contradictions": [{"아무 가치도 없", "가치가 전혀 없"}, {"인간 예술보다 우월", "인간을 완전히 대체"}],
                    "model": "기존 미술계에 변화를 가져오고 예술의 범주를 확장할 수 있다는 상징적 가치가 있다.",
                },
            },
        },
        "q2": {
            "button_label": "📘 2번 설명문 쓰기",
            "desc": "[서·논술형 2] 인공 지능 그림을 바라보는 시각을 서로 다른 설명 방법으로 두 문장 작성하시오.",
            "starter": "인공 지능이 그린 그림이 늘어나는 요즘, 우리는 이 작품들을 어떤 눈으로 바라봐야 할지 올바르게 생각해야 한다.",
            "conditions": [
                "두 문장은 서로 다른 설명 방법을 사용해야 함",
                "윗글의 내용만 활용할 것",
                "두 문장이 의미상 이어지도록 쓸 것",
            ],
            "passage_groups": [
                {"인간의 예술", "인간의 작품", "작가"},
                {"감정", "철학", "경험", "관점", "환경"},
                {"인공 지능", "인공지능"},
                {"감정이 없", "철학이 없", "이야기가 없", "경험이 없"},
                {"예술로 보기 어렵", "인간의 예술과 같다고 보기 어렵"},
                {"미술계에 변화", "예술의 범주를 확장", "상징적 가치"},
            ],
            "contradictions": [
                {"인공 지능은 감정이 풍부"},
                {"인공 지능은 독자적인 철학이 있"},
                {"아무 가치도 없", "가치가 전혀 없"},
                {"가격이 비싸서 예술"},
            ],
            "required_conclusion": [
                {"인간의 작품", "인간의 예술", "작가"},
                {"감정", "철학", "경험", "관점", "환경"},
                {"인공 지능", "인공지능"},
                {"예술로 보기 어렵", "인간의 예술과 같다고 보기 어렵", "감동을 주지 못"},
            ],
            "models": {
                "비교와 대조 + 인과": [
                    "인간의 예술에는 작가의 감정과 철학, 삶의 경험과 관점이 담겨 있지만, 인공 지능이 그린 그림에는 이러한 요소가 없다는 차이가 있다. (비교와 대조)",
                    "인공 지능은 감정을 느끼지 못하고 독자적인 철학이나 이야기가 없기 때문에 그 그림을 인간의 예술과 같다고 보기는 어렵다. (인과)",
                ],
                "예시 + 비교와 대조": [
                    "예를 들어 인간 선수의 노력과 열정이 담긴 경기는 감동을 주지만 로봇의 완벽한 경기는 같은 감동을 주지 못한다. (예시)",
                    "이와 마찬가지로 인간의 작품에는 감정과 경험이 담겨 있지만 인공 지능의 그림에는 그러한 요소가 없다. (비교와 대조)",
                ],
            },
        },
        "q3": {
            "button_label": "🎞️ 3번 영상 기획",
            "desc": "[서·논술형 3] 인간 예술의 특성이 드러나는 장면 2의 시각 요소와 청각 요소, 각 효과를 쓰시오. [총 6점]",
            "plan_title": "영상 매체와 복합양식성",
            "plan": """
**영상 제목:** 인간의 감정이 담긴 진정한 예술의 가치

**장면 1**  
- 시각: 로봇이 완벽하게 피겨 스케이팅하는 모습  
- 청각: 기계음과 일정한 박자의 메트로놈 소리

**장면 2**  
- 시각 요소: Ⓐ  
- 청각 요소: Ⓑ
""",
            "visual_element_groups": [{"화가", "작가", "인간"}, {"감정", "철학", "경험", "관점", "환경", "과거", "삶"}],
            "audio_element_groups": [{"독백", "내레이션", "붓질", "숨소리", "심장 박동", "감정적인 음악", "현악기"}],
            "visual_effect_groups": [{"작가", "화가", "인간"}, {"감정", "철학", "경험", "관점", "환경"}, {"감동", "마음을 울", "울림", "예술"}],
            "audio_effect_groups": [{"감정", "경험", "생각", "철학", "노력"}, {"감동", "마음을 울", "울림", "예술"}],
            "contradictions": [{"로봇의 완벽한 기술만", "기계음만"}, {"그림 실력이 향상", "집중력이 높아짐"}, {"아무 가치도 없"}],
            "models": {
                "시각 요소": "한 화가가 자신의 삶의 경험과 감정을 떠올리며 그림을 그리고, 완성된 작품을 본 사람들이 감동하는 모습을 보여 준다.",
                "시각 효과": "작가의 경험과 감정이 작품에 담기고 그 작품이 감상자의 마음을 울리는 모습을 통해 인간 예술의 특성을 전달한다.",
                "청각 요소": "작가가 자신의 경험과 생각을 말하는 독백과 붓질 소리를 들려주고, 작품이 완성될 때 감정이 풍부한 음악을 사용한다.",
                "청각 효과": "독백과 붓질 소리를 통해 작가의 경험과 생각이 작품에 담기는 과정을 보여 주고, 감정적인 음악을 통해 인간의 예술이 감상자에게 울림을 준다는 점을 강조한다.",
            },
        },
    },
}


# =========================================================
# 채점 함수
# =========================================================

@dataclass
class GradeResult:
    passed: bool
    score: float
    max_score: float
    reasons: List[str]


def grade_q1_answer(answer: str, rule: Dict) -> GradeResult:
    if not normalize(answer):
        return GradeResult(False, 0, 1, ["답안이 비어 있습니다."])
    found, token = contradiction_found(answer, rule.get("contradictions", []))
    if found:
        return GradeResult(False, 0, 1, [f"반대 내용 또는 다른 개념의 특성이 포함되었습니다: ‘{token}’"])
    matched = count_groups(answer, rule["required_groups"])
    if matched == len(rule["required_groups"]):
        return GradeResult(True, 1, 1, ["필수 의미 요소를 모두 포함했습니다."])
    return GradeResult(False, 0, 1, [f"필수 의미 요소가 부족합니다: {matched}/{len(rule['required_groups'])}"])


def passage_based(sentence: str, passage_groups: List[Set[str]], contradictions: List[Set[str]]) -> Tuple[bool, List[str]]:
    found, token = contradiction_found(sentence, contradictions)
    if found:
        return False, [f"지문 밖 정보 또는 반대 내용이 포함되었습니다: ‘{token}’"]
    matched = count_groups(sentence, passage_groups)
    if matched < 1:
        return False, ["지문 핵심 개념이 확인되지 않습니다."]
    return True, [f"지문 핵심 개념군 {matched}개와 일치합니다."]


def grade_q2(answer1: str, answer2: str, rule: Dict) -> GradeResult:
    answers = [answer1, answer2]
    if any(not normalize(a) for a in answers):
        return GradeResult(False, 0, 4, ["두 문장을 모두 작성해야 합니다."])

    reasons = []
    chosen_methods: List[str] = []
    priority = ["분류와 구분", "비교와 대조", "인과", "정의", "분석", "예시"]

    for idx, answer in enumerate(answers, start=1):
        declared = extract_declared_method(answer)
        detected = detect_methods(answer)

        if declared:
            if declared not in detected:
                return GradeResult(False, 0, 4, [f"({idx}) 괄호 속 ‘{declared}’와 실제 문장 방식이 일치하지 않습니다. 감지된 방식: {', '.join(sorted(detected)) or '없음'}"])
            chosen_methods.append(declared)
        else:
            if not detected:
                return GradeResult(False, 0, 4, [f"({idx}) 설명 방법의 의미 구조가 확인되지 않습니다."])
            chosen_methods.append(next(m for m in priority if m in detected))

        ok, sub = passage_based(answer, rule["passage_groups"], rule["contradictions"])
        reasons.extend([f"({idx}) {x}" for x in sub])
        if not ok:
            return GradeResult(False, 0, 4, reasons)

    if chosen_methods[0] == chosen_methods[1]:
        return GradeResult(False, 0, 4, [f"두 문장에 같은 설명 방법 ‘{chosen_methods[0]}’이 사용되었습니다."])

    conclusion_match = count_groups(" ".join(answers), rule["required_conclusion"])
    if conclusion_match < len(rule["required_conclusion"]):
        reasons.append(f"요구된 결론 방향의 핵심 요소가 부족합니다: {conclusion_match}/{len(rule['required_conclusion'])}")
        return GradeResult(False, 0, 4, reasons)

    reasons.append(f"서로 다른 설명 방법을 사용했습니다: {chosen_methods[0]} / {chosen_methods[1]}")
    reasons.append("지문 내용과 결론 방향을 충족했습니다.")
    return GradeResult(True, 4, 4, reasons)


def element_effect_connection(element: str, effect: str) -> bool:
    pairs = [
        ({"혼자", "한 학생", "개별"}, {"혼자", "개별", "집중"}),
        ({"조용", "정적", "무음", "잔잔"}, {"차분", "조용", "방해", "집중", "정지"}),
        ({"고여", "흐르지 않", "정지", "떨어지지 않"}, {"이동하지 않", "머물", "정지"}),
        ({"화가", "작가", "경험", "감정", "과거"}, {"작가", "감정", "경험", "철학", "관점", "예술"}),
        ({"독백", "붓질", "숨소리", "감정적인 음악"}, {"감정", "경험", "생각", "울림", "감동"}),
    ]
    return any(contains_any(element, a) and contains_any(effect, b) for a, b in pairs)


def grade_q3(visual_element: str, visual_effect: str, audio_element: str, audio_effect: str, rule: Dict) -> GradeResult:
    answers = [visual_element, visual_effect, audio_element, audio_effect]
    if any(not normalize(a) for a in answers):
        return GradeResult(False, 0, 6, ["시각 요소·시각 효과·청각 요소·청각 효과를 모두 작성해야 합니다."])

    for answer in answers:
        found, token = contradiction_found(answer, rule["contradictions"])
        if found:
            return GradeResult(False, 0, 6, [f"반대 내용 또는 다른 개념의 특성이 포함되었습니다: ‘{token}’"])

    score = 0
    reasons = []

    visual_element_ok = count_groups(visual_element, rule["visual_element_groups"]) == len(rule["visual_element_groups"])
    if visual_element_ok:
        score += 1
        reasons.append("시각 요소: 지문 핵심 특성을 반영함 (1/1)")
    else:
        reasons.append("시각 요소: 지문 핵심 특성이 부족함 (0/1)")

    visual_connected = element_effect_connection(visual_element, visual_effect)
    if visual_connected:
        score += 1
        reasons.append("시각 효과: 앞의 시각 요소와 연결됨 (1/1)")
    else:
        reasons.append("시각 효과: 앞의 시각 요소와의 연결이 부족함 (0/1)")

    visual_evidence = count_groups(visual_effect, rule["visual_effect_groups"]) == len(rule["visual_effect_groups"])
    if visual_evidence:
        score += 1
        reasons.append("시각 효과: 본문 근거와 결론 방향을 포함함 (1/1)")
    else:
        reasons.append("시각 효과: 본문 근거 또는 결론 방향이 부족함 (0/1)")

    audio_element_ok = count_groups(audio_element, rule["audio_element_groups"]) == len(rule["audio_element_groups"])
    if audio_element_ok:
        score += 1
        reasons.append("청각 요소: 지문 핵심 특성을 반영함 (1/1)")
    else:
        reasons.append("청각 요소: 지문 핵심 특성이 부족함 (0/1)")

    audio_connected = element_effect_connection(audio_element, audio_effect)
    if audio_connected:
        score += 1
        reasons.append("청각 효과: 앞의 청각 요소와 연결됨 (1/1)")
    else:
        reasons.append("청각 효과: 앞의 청각 요소와의 연결이 부족함 (0/1)")

    audio_evidence = count_groups(audio_effect, rule["audio_effect_groups"]) == len(rule["audio_effect_groups"])
    if audio_evidence:
        score += 1
        reasons.append("청각 효과: 본문 근거와 결론 방향을 포함함 (1/1)")
    else:
        reasons.append("청각 효과: 본문 근거 또는 결론 방향이 부족함 (0/1)")

    return GradeResult(score == 6, score, 6, reasons)


# =========================================================
# 화면 헬퍼
# =========================================================

def render_box(title: str, body: str, bg: str = "#f6f8fb", border: str = "#d8dee8") -> None:
    st.markdown(
        f"""
        <div style="background:{bg}; border:1px solid {border}; border-radius:12px; padding:16px 18px; margin:8px 0 18px 0;">
            <div style="font-weight:700; font-size:1.02rem; margin-bottom:10px;">{title}</div>
            <div style="line-height:1.75;">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_question_button_bar(current_key: str, qdata: Dict) -> str:
    mapping = {"q1": qdata["q1"]["button_label"], "q2": qdata["q2"]["button_label"], "q3": qdata["q3"]["button_label"]}
    options = ["q1", "q2", "q3"]
    return st.radio(
        "문항 선택",
        options=options,
        format_func=lambda x: mapping[x],
        horizontal=True,
        label_visibility="collapsed",
        index=options.index(current_key),
        key=f"question_nav_{st.session_state['current_set']}",
    )


# =========================================================
# Streamlit UI
# =========================================================

st.set_page_config(page_title="2회 시험 대비 서·논술형 자동 채점기", page_icon="📝", layout="wide")

st.markdown(
    """
    <style>
    .block-container {max-width: 1360px; padding-top: 1.2rem; padding-bottom: 3rem;}
    [data-testid="stSidebar"] {background: #f7f9fc;}
    .set-title {font-size: 2rem; font-weight: 800; color:#1f3556; margin: 0.4rem 0 0.8rem 0;}
    .small-note {font-size: 0.92rem; color:#6b7280;}
    div[data-testid="stTextArea"] textarea {
        font-size: 1rem !important;
        line-height: 1.6 !important;
        border-radius: 10px !important;
    }
    div[role="radiogroup"] > label {
        padding-right: 1rem !important;
    }
    .soft-panel {
        background:#eaf1fb;
        border-radius:14px;
        padding:18px 20px;
        line-height:1.9;
        border:1px solid #d7e1f3;
        margin-bottom: 14px;
    }
    .question-section-title {
        font-size:1.25rem;
        font-weight:800;
        color:#25364f;
        margin: 1rem 0 .6rem 0;
    }
    .subtle-card {
        background:#ffffff;
        border:1px solid #e4e9f0;
        border-radius:12px;
        padding:14px 16px;
        margin-top: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 상태 초기화
if "current_set" not in st.session_state:
    st.session_state["current_set"] = list(SETS.keys())[0]

# 사이드바
with st.sidebar:
    st.markdown("## 📖 개념 길잡이")
    current_sidebar_set = st.session_state["current_set"]
    for box in SETS[current_sidebar_set]["guide_boxes"]:
        with st.expander(box["title"], expanded=True):
            for item in box["items"]:
                st.markdown(f"- {item}")
            st.markdown(
                f"""
                <div style="background:{box['tip_color']}; border-radius:12px; padding:14px 14px; margin-top:12px; line-height:1.7;">
                    💡 {box['tip']}
                </div>
                """,
                unsafe_allow_html=True,
            )

# 상단 세트 탭
set_options = list(SETS.keys())
selected_set = st.radio(
    "세트 선택",
    options=set_options,
    horizontal=True,
    format_func=lambda x: f"{SETS[x]['emoji']} {SETS[x]['short']}",
    label_visibility="collapsed",
    index=set_options.index(st.session_state["current_set"]),
)
st.session_state["current_set"] = selected_set
data = SETS[selected_set]

st.markdown(f"<div class='set-title'>💡 [실전 적용] {data['title']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='soft-panel'>{data['passage'].replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

# 문항 탭
question_key = render_question_button_bar("q1" if "current_question" not in st.session_state else st.session_state["current_question"], data)
st.session_state["current_question"] = question_key

st.divider()

# Q1
if question_key == "q1":
    q = data["q1"]
    st.markdown(f"### {q['desc']}")
    table_data = [q["table_headers"]] + q["table_rows"]
    st.table(table_data)

    st.markdown("<div class='question-section-title'>답안 작성</div>", unsafe_allow_html=True)
    cols = st.columns(3)
    blanks = ["㉠", "㉡", "㉢"]
    answers = {}
    for idx, (col, blank) in enumerate(zip(cols, blanks)):
        with col:
            answers[blank] = st.text_area(
                q["answer_labels"][idx],
                placeholder="내용을 입력하세요.",
                height=110,
                key=f"{selected_set}_q1_{blank}",
            )

    if st.button("채점하기", type="primary", key=f"{selected_set}_q1_grade"):
        total = 0
        st.markdown("### 채점 결과")
        result_cols = st.columns(3)
        for col, blank in zip(result_cols, blanks):
            with col:
                result = grade_q1_answer(answers[blank], q["rules"][blank])
                total += result.score
                if result.passed:
                    st.success(f"{blank} 통과 ({result.score:.0f}/1)")
                else:
                    st.error(f"{blank} 불통과 ({result.score:.0f}/1)")
                for reason in result.reasons:
                    st.markdown(f"- {reason}")
                st.caption(f"모범 답안: {q['rules'][blank]['model']}")
        st.metric("총점", f"{total:.0f} / 3")

# Q2
elif question_key == "q2":
    q = data["q2"]
    st.markdown(f"### {q['desc']}")
    render_box("첫 문장", q["starter"], bg="#f7fafc", border="#e2e8f0")
    cond_body = "<br>".join([f"• {c}" for c in q["conditions"]])
    render_box("작성 조건", cond_body, bg="#fffdf2", border="#efe6b1")

    c1, c2 = st.columns(2)
    with c1:
        answer1 = st.text_area("(1) 첫 번째 문장", placeholder="내용을 입력하세요. 예: ... (비교와 대조)", height=160, key=f"{selected_set}_q2_1")
    with c2:
        answer2 = st.text_area("(2) 두 번째 문장", placeholder="내용을 입력하세요. 예: ... (예시)", height=160, key=f"{selected_set}_q2_2")

    if st.button("채점하기", type="primary", key=f"{selected_set}_q2_grade"):
        result = grade_q2(answer1, answer2, q)
        st.markdown("### 채점 결과")
        if result.passed:
            st.success(f"통과 ({result.score:.0f}/{result.max_score:.0f})")
        else:
            st.error(f"불통과 ({result.score:.0f}/{result.max_score:.0f})")
        for reason in result.reasons:
            st.markdown(f"- {reason}")

    with st.expander("모범 답안 예시 보기", expanded=False):
        for combo, models in q["models"].items():
            st.markdown(f"**{combo}**")
            st.markdown(f"- (1) {models[0]}")
            st.markdown(f"- (2) {models[1]}")
            st.divider()

# Q3
else:
    q = data["q3"]
    st.markdown(f"### {q['desc']}")
    render_box(q["plan_title"], q["plan"].replace("\n", "<br>"), bg="#f7fafc", border="#e2e8f0")
    cond_body = "<br>".join([f"• {c}" for c in q["conditions"]])
    render_box("작성 조건", cond_body, bg="#fffdf2", border="#efe6b1")

    left, right = st.columns(2)
    with left:
        visual_element = st.text_area("Ⓐ 시각 요소", placeholder="화면에 무엇이 보이는지 구체적으로 쓰세요.", height=120, key=f"{selected_set}_q3_ve")
        visual_effect = st.text_area("시각 요소의 효과", placeholder="이 시각 요소가 무엇을 전달하는지 쓰세요.", height=150, key=f"{selected_set}_q3_vf")
    with right:
        audio_element = st.text_area("Ⓑ 청각 요소", placeholder="어떤 소리가 들리는지 구체적으로 쓰세요.", height=120, key=f"{selected_set}_q3_ae")
        audio_effect = st.text_area("청각 요소의 효과", placeholder="이 청각 요소가 무엇을 전달하는지 쓰세요.", height=150, key=f"{selected_set}_q3_af")

    with st.expander("6점 배점 기준 보기", expanded=False):
        st.table([
            {"평가 요소": "시각 요소", "배점": 1, "설명": "지문 핵심 특성이 화면에 드러나는가"},
            {"평가 요소": "시각 효과-요소 연결", "배점": 1, "설명": "효과 설명이 앞의 시각 요소와 연결되는가"},
            {"평가 요소": "시각 효과-본문 근거", "배점": 1, "설명": "효과 설명에 본문 근거가 있는가"},
            {"평가 요소": "청각 요소", "배점": 1, "설명": "지문 핵심 특성이 소리로 드러나는가"},
            {"평가 요소": "청각 효과-요소 연결", "배점": 1, "설명": "효과 설명이 앞의 청각 요소와 연결되는가"},
            {"평가 요소": "청각 효과-본문 근거", "배점": 1, "설명": "효과 설명에 본문 근거가 있는가"},
        ])

    if st.button("채점하기", type="primary", key=f"{selected_set}_q3_grade"):
        result = grade_q3(visual_element, visual_effect, audio_element, audio_effect, q)
        st.markdown("### 채점 결과")
        if result.passed:
            st.success(f"통과 ({result.score:.0f}/{result.max_score:.0f})")
        else:
            st.warning(f"부분 점수 또는 불통과 ({result.score:.0f}/{result.max_score:.0f})")
        for reason in result.reasons:
            st.markdown(f"- {reason}")

    with st.expander("모범 답안 예시 보기", expanded=False):
        models = q["models"]
        st.markdown(f"- **시각 요소:** {models['시각 요소']}")
        st.markdown(f"- **시각 효과:** {models['시각 효과']}")
        st.markdown(f"- **청각 요소:** {models['청각 요소']}")
        st.markdown(f"- **청각 효과:** {models['청각 효과']}")

st.divider()
st.caption("이 앱은 규칙 기반 1차 채점 도구입니다. 새로운 동의어나 창의적인 답안은 교사의 최종 검토가 필요합니다.")
