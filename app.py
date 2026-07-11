
import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Tuple, Set

import streamlit as st


# =========================================================
# 기본 유틸리티
# =========================================================

METHODS = ["정의", "예시", "인과", "분석", "비교와 대조", "분류와 구분"]

METHOD_ALIASES = {
    "정의": {"정의", "뜻", "개념"},
    "예시": {"예시", "예", "사례"},
    "인과": {"인과", "원인과 결과", "원인 결과"},
    "분석": {"분석", "요소", "구성"},
    "비교와 대조": {"비교와 대조", "비교대조", "비교", "대조"},
    "분류와 구분": {"분류와 구분", "분류구분", "분류", "구분"},
}


def normalize(text: str) -> str:
    """한글 유니코드·공백·문장부호를 정규화한다."""
    text = unicodedata.normalize("NFKC", text or "")
    text = text.lower().strip()
    text = re.sub(r"[“”‘’\"']", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def compact(text: str) -> str:
    return re.sub(r"\s+", "", normalize(text))


def contains_any(text: str, expressions: List[str] | Set[str]) -> bool:
    t = compact(text)
    return any(compact(x) in t for x in expressions)


def count_groups(text: str, groups: List[Set[str]]) -> int:
    return sum(1 for group in groups if contains_any(text, group))


def extract_declared_method(text: str) -> str | None:
    """괄호 속 설명 방법을 추출한다."""
    candidates = re.findall(r"\(([^()]*)\)", normalize(text))
    for candidate in reversed(candidates):
        for canonical, aliases in METHOD_ALIASES.items():
            if contains_any(candidate, aliases):
                return canonical
    return None


def remove_method_label(text: str) -> str:
    return re.sub(r"\([^()]*\)\s*$", "", text or "").strip()


def contradiction_found(text: str, contradictions: List[Set[str]]) -> Tuple[bool, str]:
    for group in contradictions:
        if contains_any(text, group):
            return True, next(iter(group))
    return False, ""


# =========================================================
# 설명 방법 탐지
# '용어 없이도 의미가 담기면 인정'하되,
# 학생이 방법명을 적은 경우 실제 문장 구조와 일치해야 한다.
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
    markers = ["예를 들어", "가령", "대표적으로", "예로", "사례로"]
    concrete = [
        "커피숍", "도서관", "공부 모임", "피겨 스케이팅", "올림픽",
        "폭포", "저수지", "댐", "수조", "에드몽 드 벨라미"
    ]
    return contains_any(s, markers) or contains_any(s, concrete)


def detect_cause_effect(sentence: str) -> bool:
    s = normalize(sentence)
    causal_markers = ["때문에", "그러므로", "따라서", "그래서", "결과적으로", "까닭에", "므로", "아서", "어서"]
    has_marker = contains_any(s, causal_markers)
    # 단순 접속어 오탐 방지: 결과 방향 표현도 있어야 한다.
    result_markers = [
        "좋다", "효율적", "위험하지", "예술로 보기 어렵", "예술로 볼 수",
        "강조", "전달", "드러", "감동", "울림", "집중해야"
    ]
    return has_marker and contains_any(s, result_markers)


def detect_analysis(sentence: str) -> bool:
    s = normalize(sentence)
    components = [
        "감정", "철학", "경험", "관점", "환경", "전압", "전하", "위험성",
        "혼자", "집중", "연습", "익숙"
    ]
    component_count = sum(1 for c in components if contains_any(s, {c}))
    structure = contains_any(s, {"이루어", "구성", "요소", "부분", "에는", "특징은", "방법에는"})
    return structure and component_count >= 2


def detect_compare(sentence: str) -> bool:
    s = normalize(sentence)
    markers = ["반면", "하지만", "그러나", "와 달리", "과 달리", "차이", "공통점", "둘 다", "반대로", "지만"]
    domains = [
        ["쉬운 과제", "어려운 과제"],
        ["실생활 전기", "정전기"],
        ["인간", "인공 지능"],
        ["인간의 예술", "인공 지능의 그림"],
        ["인간 선수", "로봇"],
    ]
    has_two_targets = any(all(contains_any(s, {x}) for x in pair) for pair in domains)
    return has_two_targets and contains_any(s, markers)


def detect_classification(sentence: str) -> bool:
    s = normalize(sentence)
    markers = ["나뉘", "나눌 수", "구분", "분류", "묶", "종류"]
    criteria = ["에 따라", "기준", "여부", "난이도", "창작 주체"]
    # 분류 기준 + 두 부류가 모두 있어야 함
    pairs = [
        ["쉬운 과제", "어려운 과제"],
        ["실생활 전기", "정전기"],
        ["인간", "인공 지능"],
    ]
    return (
        contains_any(s, markers)
        and contains_any(s, criteria)
        and any(all(contains_any(s, {x}) for x in pair) for pair in pairs)
    )


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
# 채점 설정
# =========================================================

SETS = {
    "1세트: 사회적 촉진·억제": {
        "q1": {
            "㉠": {
                "required_groups": [
                    {"쉬운 과제", "비교적 쉬운 과제", "어렵지 않은 과제", "큰 노력이 필요하지 않은 과제", "큰 노력이 들지 않는 과제"}
                ],
                "contradictions": [
                    {"어려운 과제", "복잡한 과제", "도전이 필요한 과제"}
                ],
                "model": "비교적 쉽거나 큰 노력을 들일 필요가 없는 과제",
            },
            "㉡": {
                "required_groups": [
                    {"혼자", "혼자서", "개별적으로", "다른 사람 없이"},
                    {"집중", "차분하게", "연습", "반복", "익숙해질 때까지"}
                ],
                "contradictions": [
                    {"함께", "공부 모임", "여럿이"}
                ],
                "model": "충분히 연습하여 익숙해질 때까지 차분하게 혼자 집중함",
            },
            "㉢": {
                "required_groups": [{"사회적 억제"}],
                "contradictions": [{"사회적 촉진"}],
                "model": "사회적 억제",
                "exact_concept": True,
            },
        },
        "q2": {
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
                "비교와 대조 + 인과": [
                    "쉬운 과제는 함께하는 것이 좋지만, 어려운 과제는 혼자 하는 것이 좋다. (비교와 대조)",
                    "어려운 과제는 익숙해질 때까지 충분히 연습해야 하므로 혼자 차분하게 집중하는 것이 좋다. (인과)",
                ],
            },
        },
        "q3": {
            "visual_element_groups": [
                {"혼자", "한 학생", "개별적으로"},
                {"집중", "연습", "반복", "틀린 문제", "다시 확인"}
            ],
            "audio_element_groups": [
                {"조용", "정적", "무음", "말소리 없음", "소리 제거", "잔잔"},
            ],
            "visual_effect_groups": [
                {"혼자", "개별적으로"},
                {"어려운 과제", "도전이 필요한 과제"},
                {"집중", "연습", "익숙해질 때까지", "차분하게"},
            ],
            "audio_effect_groups": [
                {"차분", "조용", "방해가 없", "집중"},
                {"어려운 과제", "도전이 필요한 과제"},
            ],
            "contradictions": [
                {"여럿이 떠들", "친구들과 시끄럽게"},
                {"기억력이 세 배", "도파민", "뇌파"},
            ],
            "models": {
                "시각 요소": "한 학생이 조용한 공간에서 혼자 어려운 문제를 반복해서 풀고 틀린 문제를 다시 확인하는 모습을 보여 준다.",
                "시각 효과": "학생이 혼자 반복해서 연습하는 모습을 통해 어려운 과제는 익숙해질 때까지 차분하게 혼자 집중해야 한다는 점을 전달한다.",
                "청각 요소": "사람들의 말소리와 경쾌한 음악은 없애고, 연필로 문제를 푸는 소리와 책장 넘기는 소리만 작게 들려준다.",
                "청각 효과": "주변 소리를 줄인 차분한 분위기를 통해 어려운 과제는 방해를 받지 않고 혼자 집중해서 연습하는 것이 좋다는 점을 강조한다.",
            },
        },
    },

    "2세트: 정전기": {
        "q1": {
            "㉠": {
                "required_groups": [
                    {"높은 곳", "높은 위치", "위쪽"},
                    {"고여 있는 물", "머물러 있는 물", "흐르지 않는 물", "저장된 물"}
                ],
                "contradictions": [{"흐르는 물", "폭포", "떨어지는 물"}],
                "model": "높은 곳에 고여 있는 물",
            },
            "㉡": {
                "required_groups": [
                    {"전하"},
                    {"이동하지 않", "머물", "정지 상태", "흐르지 않", "제자리에"}
                ],
                "contradictions": [{"전하가 이동", "전하가 흐름", "빠르게 이동"}],
                "model": "전하가 이동하지 않고 머물러 있음",
            },
            "㉢": {
                "required_groups": [
                    {"위험하지 않", "피해가 없", "위험성이 낮", "감전 위험이 없"}
                ],
                "contradictions": [
                    {"매우 위험", "감전 위험이 크"},
                    {"전압이 낮아서"}
                ],
                "model": "전압은 높지만 전하가 이동하지 않아 위험하지 않음",
            },
        },
        "q2": {
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
                "분석 + 인과": [
                    "정전기의 특징은 높은 전압, 전하의 정지 상태, 낮은 위험성으로 나누어 살펴볼 수 있다. (분석)",
                    "전하가 이동하지 않고 머물러 있으므로 정전기는 전압이 높아도 위험하지 않다. (인과)",
                ],
            },
        },
        "q3": {
            "visual_element_groups": [
                {"높은 곳", "높은 절벽", "댐", "저수지", "높은 수조"},
                {"고여", "흐르지 않", "떨어지지 않", "정지"}
            ],
            "audio_element_groups": [
                {"정적", "무음", "고요", "잔잔", "거센 물소리 없음", "폭포 소리 제거"}
            ],
            "visual_effect_groups": [
                {"전하"},
                {"이동하지 않", "머물", "정지 상태"},
                {"위험하지 않", "피해가 없", "전압이 높아도"}
            ],
            "audio_effect_groups": [
                {"전하"},
                {"이동하지 않", "머물", "정지 상태"}
            ],
            "contradictions": [
                {"폭포처럼 쏟아", "물이 세차게 흐르"},
                {"전압이 낮아서", "전압을 낮춘다"}
            ],
            "models": {
                "시각 요소": "높은 절벽 위의 저수지에 많은 물이 고여 있지만 아래로 흐르거나 떨어지지 않는 모습을 보여 준다.",
                "시각 효과": "높은 곳에 물이 고여 움직이지 않는 모습을 통해 정전기는 전압이 높아도 전하가 이동하지 않고 머물러 있어 위험하지 않다는 점을 전달한다.",
                "청각 요소": "폭포처럼 물이 거세게 흐르는 소리는 없애고, 아주 약한 물결 소리만 들려준다.",
                "청각 효과": "거센 물소리가 없는 고요한 상태를 통해 정전기의 전하가 이동하지 않고 머물러 있다는 점을 강조한다.",
            },
        },
    },

    "3세트: 인공 지능 그림": {
        "q1": {
            "㉠": {
                "required_groups": [
                    {"로봇"},
                    {"완벽", "한 번의 실수 없이"},
                    {"피겨 스케이팅", "경기"}
                ],
                "contradictions": [{"인간 선수"}],
                "model": "한 번의 실수 없이 완벽하게 피겨 스케이팅을 하는 로봇",
            },
            "㉡": {
                "required_groups": [
                    {"감정이 없", "감정을 느끼지 못", "철학이 없", "이야기가 없", "경험이 없", "관점이 없"},
                    {"예술로 보기 어렵", "인간의 예술과 같다고 보기 어렵", "예술로 인정하기 어렵"}
                ],
                "contradictions": [
                    {"기술이 부족해서"},
                    {"가격이 낮아서"},
                    {"아무 가치도 없"}
                ],
                "model": "감정도 느끼지 못하고 독자적인 철학이나 이야기가 없으므로 예술로 보기 어렵다.",
            },
            "㉢": {
                "required_groups": [
                    {"미술계에 변화", "미술계의 변화", "예술의 범주를 확장", "예술의 범위를 넓", "새로운 예술 가능성"},
                    {"가치", "의미", "상징적"}
                ],
                "contradictions": [
                    {"아무 가치도 없", "가치가 전혀 없"},
                    {"인간 예술보다 우월", "인간을 완전히 대체"}
                ],
                "model": "기존 미술계에 변화를 가져오고 예술의 범주를 확장할 수 있다는 상징적 가치가 있다.",
            },
        },
        "q2": {
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
                {"예술로 보기 어렵", "인간의 예술과 같다고 보기 어렵", "감동을 주지 못"}
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
                "분석 + 인과": [
                    "인간의 작품에는 작가의 감정, 철학, 경험, 관점, 환경이 담겨 있다. (분석)",
                    "이러한 요소들이 작품에 종합적으로 담겨 있으므로 인간의 작품을 예술로 볼 수 있다. (인과)",
                ],
            },
        },
        "q3": {
            "visual_element_groups": [
                {"화가", "작가", "인간"},
                {"감정", "철학", "경험", "관점", "환경", "과거", "삶"},
            ],
            "audio_element_groups": [
                {"독백", "내레이션", "붓질", "숨소리", "심장 박동", "감정적인 음악", "현악기"}
            ],
            "visual_effect_groups": [
                {"작가", "화가", "인간"},
                {"감정", "철학", "경험", "관점", "환경"},
                {"감동", "마음을 울", "울림", "예술"}
            ],
            "audio_effect_groups": [
                {"감정", "경험", "생각", "철학", "노력"},
                {"감동", "마음을 울", "울림", "예술"}
            ],
            "contradictions": [
                {"로봇의 완벽한 기술만", "기계음만"},
                {"그림 실력이 향상", "집중력이 높아짐"},
                {"아무 가치도 없"}
            ],
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
# 문항별 자동 채점 함수
# =========================================================

@dataclass
class GradeResult:
    passed: bool
    score: float
    max_score: float
    reasons: List[str]


def grade_q1_answer(answer: str, rule: Dict) -> GradeResult:
    reasons = []
    if not normalize(answer):
        return GradeResult(False, 0, 1, ["답안이 비어 있습니다."])

    found, token = contradiction_found(answer, rule.get("contradictions", []))
    if found:
        return GradeResult(False, 0, 1, [f"지문과 반대되거나 다른 개념의 특성이 포함되었습니다: ‘{token}’"])

    required = rule["required_groups"]
    matched = count_groups(answer, required)

    if matched == len(required):
        reasons.append("필수 의미 요소를 모두 포함했습니다.")
        return GradeResult(True, 1, 1, reasons)

    missing = len(required) - matched
    reasons.append(f"필수 의미 요소 {missing}개가 빠졌습니다.")
    return GradeResult(False, 0, 1, reasons)


def passage_based(sentence: str, passage_groups: List[Set[str]], contradictions: List[Set[str]]) -> Tuple[bool, List[str]]:
    reasons = []
    found, token = contradiction_found(sentence, contradictions)
    if found:
        return False, [f"지문 밖 정보 또는 반대 내용이 핵심 주장에 포함되었습니다: ‘{token}’"]

    # 키워드 추출 입력만으로도 판정되도록 최소 1개 지문 개념군과 일치하면 통과
    matched = count_groups(sentence, passage_groups)
    if matched < 1:
        return False, ["지문 핵심 개념이 확인되지 않습니다."]
    reasons.append(f"지문 핵심 개념군 {matched}개와 일치합니다.")
    return True, reasons


def grade_q2(answers: List[str], rule: Dict) -> GradeResult:
    reasons = []
    if len(answers) != 2 or any(not normalize(a) for a in answers):
        return GradeResult(False, 0, 4, ["두 문장을 모두 작성해야 합니다."])

    declared = [extract_declared_method(a) for a in answers]
    detected = [detect_methods(a) for a in answers]

    # 용어를 쓰지 않아도 실제 의미가 드러나면 인정
    # 다만 용어를 쓴 경우 실제 문장 구조와 반드시 일치해야 함
    chosen = []
    for i in range(2):
        if declared[i]:
            if declared[i] not in detected[i]:
                reasons.append(
                    f"({i+1}) 괄호 속 ‘{declared[i]}’와 실제 문장 방식이 일치하지 않습니다. "
                    f"감지된 방식: {', '.join(sorted(detected[i])) or '없음'}"
                )
                return GradeResult(False, 0, 4, reasons)
            chosen.append(declared[i])
        else:
            if not detected[i]:
                reasons.append(f"({i+1}) 설명 방법의 의미 구조가 확인되지 않습니다.")
                return GradeResult(False, 0, 4, reasons)
            # 용어가 없을 때는 가장 분명한 방법 하나를 선택
            priority = ["분류와 구분", "비교와 대조", "인과", "정의", "분석", "예시"]
            chosen.append(next(m for m in priority if m in detected[i]))

    if chosen[0] == chosen[1]:
        return GradeResult(False, 0, 4, [f"두 문장에 같은 설명 방법 ‘{chosen[0]}’이 사용되었습니다."])

    # 지문 내용 활용 확인
    for i, answer in enumerate(answers):
        ok, r = passage_based(answer, rule["passage_groups"], rule["contradictions"])
        reasons.extend([f"({i+1}) {x}" for x in r])
        if not ok:
            return GradeResult(False, 0, 4, reasons)

    # 전체 결론 방향 확인: 두 문장을 합쳐 필요한 결론 요소를 충족해야 함
    combined = " ".join(answers)
    conclusion_match = count_groups(combined, rule["required_conclusion"])
    if conclusion_match < len(rule["required_conclusion"]):
        reasons.append(
            f"요구된 결론 방향의 핵심 요소가 부족합니다 "
            f"({conclusion_match}/{len(rule['required_conclusion'])})."
        )
        return GradeResult(False, 0, 4, reasons)

    reasons.append(f"서로 다른 설명 방법을 사용했습니다: {chosen[0]} / {chosen[1]}")
    reasons.append("괄호 속 명칭과 실제 서술 방식이 일치하거나, 용어 없이도 방법의 의미 구조가 확인됩니다.")
    reasons.append("지문 내용과 결론 방향을 모두 충족했습니다.")
    return GradeResult(True, 4, 4, reasons)


def element_effect_connection(element: str, effect: str) -> bool:
    """요소와 효과 사이의 의미 연결을 거칠게 확인한다."""
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

    # 오개념·다른 개념의 특성 전이 방지
    for answer in answers:
        found, token = contradiction_found(answer, rule["contradictions"])
        if found:
            return GradeResult(False, 0, 6, [f"지문과 반대되거나 다른 개념의 특성이 포함되었습니다: ‘{token}’"])

    score = 0
    reasons = []

    # 시각 요소 1점
    vg = count_groups(visual_element, rule["visual_element_groups"])
    if vg == len(rule["visual_element_groups"]):
        score += 1
        reasons.append("시각 요소: 지문 핵심 특성을 모두 반영함 (1/1)")
    else:
        reasons.append(f"시각 요소: 핵심 특성 부족 ({vg}/{len(rule['visual_element_groups'])}, 0/1)")

    # 시각 효과 2점: 요소 연결 1 + 본문 근거 1
    visual_connected = element_effect_connection(visual_element, visual_effect)
    visual_evidence = count_groups(visual_effect, rule["visual_effect_groups"]) == len(rule["visual_effect_groups"])
    if visual_connected:
        score += 1
        reasons.append("시각 효과: 앞의 시각 요소와 의미상 연결됨 (1/1)")
    else:
        reasons.append("시각 효과: 앞의 시각 요소와의 연결이 확인되지 않음 (0/1)")
    if visual_evidence:
        score += 1
        reasons.append("시각 효과: 지문 근거와 결론 방향을 포함함 (1/1)")
    else:
        reasons.append("시각 효과: 지문 근거 또는 요구 결론이 부족함 (0/1)")

    # 청각 요소 1점
    ag = count_groups(audio_element, rule["audio_element_groups"])
    if ag == len(rule["audio_element_groups"]):
        score += 1
        reasons.append("청각 요소: 지문 핵심 특성을 반영함 (1/1)")
    else:
        reasons.append(f"청각 요소: 핵심 특성 부족 ({ag}/{len(rule['audio_element_groups'])}, 0/1)")

    # 청각 효과 2점
    audio_connected = element_effect_connection(audio_element, audio_effect)
    audio_evidence = count_groups(audio_effect, rule["audio_effect_groups"]) == len(rule["audio_effect_groups"])
    if audio_connected:
        score += 1
        reasons.append("청각 효과: 앞의 청각 요소와 의미상 연결됨 (1/1)")
    else:
        reasons.append("청각 효과: 앞의 청각 요소와의 연결이 확인되지 않음 (0/1)")
    if audio_evidence:
        score += 1
        reasons.append("청각 효과: 지문 근거와 결론 방향을 포함함 (1/1)")
    else:
        reasons.append("청각 효과: 지문 근거 또는 요구 결론이 부족함 (0/1)")

    return GradeResult(score == 6, score, 6, reasons)


# =========================================================
# Streamlit UI
# =========================================================

st.set_page_config(page_title="서·논술형 자동 채점기", page_icon="📝", layout="wide")

st.title("📝 2회 시험 대비 서·논술형 자동 채점기")
st.caption(
    "규칙 기반 1차 채점 도구입니다. 동의어·유사 표현을 허용하지만, "
    "오개념·방법 불일치·결론 방향 오류는 불통과 처리합니다."
)

with st.sidebar:
    st.header("채점 설정")
    selected_set = st.selectbox("문항 세트", list(SETS.keys()))
    question_type = st.radio(
        "문항 유형",
        ["서·논술형 1: 표 빈칸", "서·논술형 2: 설명 방법", "서·논술형 3: 영상 기획안"]
    )
    st.divider()
    st.info(
        "자동 채점 결과는 교사의 최종 판단을 대체하지 않습니다. "
        "새로운 동의어나 창의적인 답안은 수동 검토가 필요할 수 있습니다."
    )

config = SETS[selected_set]

if question_type.startswith("서·논술형 1"):
    st.subheader(f"{selected_set} — 서·논술형 1")
    cols = st.columns(3)
    answers = {}
    for col, blank in zip(cols, ["㉠", "㉡", "㉢"]):
        with col:
            answers[blank] = st.text_area(f"{blank} 답안", height=130)

    if st.button("채점하기", type="primary"):
        total = 0
        for blank in ["㉠", "㉡", "㉢"]:
            result = grade_q1_answer(answers[blank], config["q1"][blank])
            total += result.score
            if result.passed:
                st.success(f"{blank}: 통과 ({result.score:.0f}/{result.max_score:.0f})")
            else:
                st.error(f"{blank}: 불통과 ({result.score:.0f}/{result.max_score:.0f})")
            for reason in result.reasons:
                st.write(f"- {reason}")
            st.caption(f"모범 답안: {config['q1'][blank]['model']}")
        st.metric("총점", f"{total:.0f} / 3")

elif question_type.startswith("서·논술형 2"):
    st.subheader(f"{selected_set} — 서·논술형 2")
    st.write(
        "괄호 속 방법명을 생략해도 실제 문장에 설명 방법의 의미 구조가 드러나면 인정합니다. "
        "방법명을 쓴 경우에는 실제 서술 방식과 일치해야 합니다."
    )
    answer1 = st.text_area("(1) 문장", height=140, placeholder="문장 끝에 (비교와 대조)처럼 적을 수 있습니다.")
    answer2 = st.text_area("(2) 문장", height=140, placeholder="방법명을 쓰지 않아도 구조가 분명하면 판정합니다.")

    if st.button("채점하기", type="primary"):
        result = grade_q2([answer1, answer2], config["q2"])
        if result.passed:
            st.success(f"통과 ({result.score:.0f}/{result.max_score:.0f})")
        else:
            st.error(f"불통과 ({result.score:.0f}/{result.max_score:.0f})")
        for reason in result.reasons:
            st.write(f"- {reason}")

    st.divider()
    st.subheader("선택 가능한 설명 방법 조합별 모범 답안")
    for combo, models in config["q2"]["models"].items():
        with st.expander(combo):
            st.write(f"**(1)** {models[0]}")
            st.write(f"**(2)** {models[1]}")

    st.subheader("설명 방법 판정 기준")
    method_table = {
        "정의": "대상의 뜻·개념을 직접 밝힘",
        "예시": "일반 내용을 뒷받침하는 구체적 사례를 제시함",
        "인과": "원인과 결과 및 둘의 관계가 드러남",
        "분석": "하나의 대상을 둘 이상의 요소·부분으로 나누어 설명함",
        "비교와 대조": "둘 이상의 대상과 그 공통점 또는 차이점이 드러남",
        "분류와 구분": "분류 기준과 둘 이상의 종류가 드러남",
    }
    st.table([{"설명 방법": k, "통과 기준": v} for k, v in method_table.items()])

else:
    st.subheader(f"{selected_set} — 서·논술형 3")
    left, right = st.columns(2)
    with left:
        visual_element = st.text_area("시각 요소 Ⓐ", height=120)
        visual_effect = st.text_area("시각 요소의 효과", height=150)
    with right:
        audio_element = st.text_area("청각 요소 Ⓑ", height=120)
        audio_effect = st.text_area("청각 요소의 효과", height=150)

    if st.button("채점하기", type="primary"):
        result = grade_q3(
            visual_element, visual_effect, audio_element, audio_effect, config["q3"]
        )
        if result.passed:
            st.success(f"통과 ({result.score:.0f}/{result.max_score:.0f})")
        else:
            st.warning(f"부분 점수 또는 불통과 ({result.score:.0f}/{result.max_score:.0f})")
        for reason in result.reasons:
            st.write(f"- {reason}")

    st.divider()
    st.subheader("모범 답안")
    models = config["q3"]["models"]
    st.write(f"**시각 요소:** {models['시각 요소']}")
    st.write(f"**시각 효과:** {models['시각 효과']}")
    st.write(f"**청각 요소:** {models['청각 요소']}")
    st.write(f"**청각 효과:** {models['청각 효과']}")

    st.subheader("부분 점수 기준")
    st.table([
        {"평가 요소": "시각 요소", "배점": 1, "통과 기준": "지문 핵심 특성의 필수 의미군을 모두 포함"},
        {"평가 요소": "시각 효과–요소 연결", "배점": 1, "통과 기준": "앞서 쓴 시각 요소의 특징이 효과 설명에 반영됨"},
        {"평가 요소": "시각 효과–본문 근거", "배점": 1, "통과 기준": "본문의 핵심 개념과 요구 결론을 포함"},
        {"평가 요소": "청각 요소", "배점": 1, "통과 기준": "지문 핵심 특성을 드러내는 구체적 소리를 제시"},
        {"평가 요소": "청각 효과–요소 연결", "배점": 1, "통과 기준": "앞서 쓴 청각 요소의 특징이 효과 설명에 반영됨"},
        {"평가 요소": "청각 효과–본문 근거", "배점": 1, "통과 기준": "본문의 핵심 개념과 요구 결론을 포함"},
    ])

st.divider()
st.caption(
    "설계 원칙: 의미 기반 동의어 허용 / 특정 방법 선택 시 실제 구조 검증 / "
    "다른 개념의 특성 전이 차단 / 요구 결론 방향 확인 / 영상 문항 1-2-1-2점 구조"
)
