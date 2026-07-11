from pathlib import Path
import zipfile
import textwrap

app_path = Path("/mnt/data/essay_grader_streamlit/app.py")
code = app_path.read_text(encoding="utf-8")

marker = "# =========================================================\n# Streamlit UI\n# =========================================================\n"
head = code.split(marker)[0]

new_ui = r'''
# =========================================================
# 화면에 제시할 지문·문항·조건
# =========================================================

DISPLAY_CONTENT = {
    "1세트: 사회적 촉진·억제": {
        "passage_title": "사회적 촉진과 사회적 억제를 활용한 학습 방법",
        "passage": """
**기자:** 심리학 용어인 ‘사회적 촉진’과 ‘사회적 억제’를 일상생활, 특히 우리의 학습에 어떻게 적용할 수 있을까요?

**전문가:** 이 두 가지 개념을 알면 상황에 맞춰 유용하게 활용할 수 있습니다. 비교적 쉬운 취미 생활이나 큰 노력을 들일 필요가 없는 과제는 집에서 혼자 하는 것보다 커피숍이나 도서관에서 하거나, 친숙하고 좋아하는 과목이라면 공부 모임을 만들어 다른 사람들과 함께 공부하는 것이 더 효율적일 수 있습니다.

반면 지나치게 어렵거나 도전이 필요한 과제는 충분히 연습하며 익숙해질 때까지 차분하게 혼자 집중하는 시간을 가지는 것이 좋습니다.
""",
        "q1": {
            "title": "글의 핵심 내용을 표로 정리하기",
            "prompt": "윗글을 요약한 표의 ㉠~㉢에 들어갈 내용을 찾아 쓰세요.",
            "table": [
                ["과제의 특성", "효율적인 환경 및 방법", "관련된 심리 현상"],
                ["㉠", "커피숍·도서관에서 하거나 다른 사람과 함께함", "사회적 촉진"],
                ["지나치게 어렵거나 도전이 필요한 과제", "㉡", "㉢"],
            ],
            "guide": [
                "㉠에는 어떤 특성의 과제인지 씁니다.",
                "㉡에는 그 과제를 수행하는 환경과 방법을 씁니다.",
                "㉢에는 해당 심리 현상의 이름을 씁니다.",
            ],
        },
        "q2": {
            "title": "서로 다른 설명 방법으로 문장 쓰기",
            "prompt": "‘과제 난이도에 따른 효율적인 학습 전략’을 설명하는 글의 첫 문장에 이어질 두 문장을 작성하세요.",
            "starter": "과제의 특성과 난이도에 따라 우리의 학습 효율을 높이는 방법은 다르게 적용되어야 한다.",
            "conditions": [
                "(1), (2)에 문장을 하나씩 작성합니다.",
                "두 문장은 서로 다른 설명 방법을 사용해야 합니다.",
                "윗글에 나온 내용만 활용합니다.",
                "설명 방법명을 쓰는 경우 문장 끝에 괄호로 표시합니다.",
            ],
            "hints": "쉬운 과제와 어려운 과제를 어떻게 다르게 해야 하는지 생각해 보세요.",
        },
        "q3": {
            "title": "어려운 과제 장면의 영상 기획안 완성하기",
            "prompt": "장면 2의 시각 요소와 청각 요소를 정하고, 각각의 효과를 설명하세요.",
            "plan": """
**영상 주제:** 사회적 촉진과 억제를 활용한 스마트한 공부법

**장면 1 — 쉬운 과제를 할 때**  
- 시각: 밝은 도서관에서 친구들과 공부하는 모습  
- 청각: 경쾌한 음악, 발소리, 책장 넘기는 소리

**장면 2 — 어려운 과제를 할 때**  
- 시각 요소: Ⓐ  
- 청각 요소: Ⓑ
""",
            "conditions": [
                "어려운 과제를 할 때 필요한 환경의 특성이 드러나야 합니다.",
                "시각·청각 요소를 각각 구체적으로 씁니다.",
                "각 효과에는 앞에서 쓴 요소와의 연결이 있어야 합니다.",
                "효과의 근거는 반드시 윗글의 내용에서 가져옵니다.",
            ],
        },
    },

    "2세트: 정전기": {
        "passage_title": "정전기의 뜻과 특징",
        "passage": """
**기자:** 겨울철 불청객인 ‘정전기’란 정확히 무엇인가요?

**전문가:** 정전기란 전하가 정지 상태로 있어 그 분포가 시간적으로 변화하지 않는 전기와 그로 인한 전기 현상을 말합니다. 쉽게 말하면 흐르지 않고 머물러 있는 전기입니다.

우리가 실생활에서 쓰는 전기가 ‘흐르는 물’이라면, 정전기는 ‘높은 곳에 고여 있는 물’이라고 할 수 있습니다. 정전기의 전압은 매우 높지만 전하가 이동하지 않고 머물러 있어 위험하지는 않습니다. 어마어마하게 높은 곳에 고여 있는 물이 떨어지지 않고 있어서 별 피해가 없는 것과 같습니다.
""",
        "q1": {
            "title": "정전기의 특징을 표로 정리하기",
            "prompt": "윗글을 요약한 표의 ㉠~㉢에 들어갈 내용을 찾아 쓰세요.",
            "table": [
                ["대상", "물의 상태에 비유", "전하의 상태", "위험성"],
                ["실생활 전기", "흐르는 물", "전하가 이동함", "감전 등의 위험이 있음"],
                ["정전기", "㉠", "㉡", "㉢"],
            ],
            "guide": [
                "㉠에는 정전기를 비유한 물의 상태를 씁니다.",
                "㉡에는 전하가 어떤 상태인지 씁니다.",
                "㉢에는 위험성을 씁니다.",
            ],
        },
        "q2": {
            "title": "정전기의 특징을 두 가지 설명 방법으로 쓰기",
            "prompt": "‘정전기의 특징’을 설명하는 글의 첫 문장에 이어질 두 문장을 작성하세요.",
            "starter": "겨울철에 흔히 겪는 정전기는 우리가 평소 집에서 사용하는 전기와는 다른 뚜렷한 특징이 있다.",
            "conditions": [
                "(1), (2)에 문장을 하나씩 작성합니다.",
                "두 문장은 서로 다른 설명 방법을 사용해야 합니다.",
                "윗글에 제시된 내용만 활용합니다.",
                "두 문장이 의미상 이어지도록 씁니다.",
                "설명 방법명을 쓰는 경우 문장 끝에 괄호로 표시합니다.",
            ],
            "hints": "정전기의 뜻, 실생활 전기와의 차이, 전하의 상태, 위험성을 활용할 수 있습니다.",
        },
        "q3": {
            "title": "정전기 장면의 영상 기획안 완성하기",
            "prompt": "장면 2의 시각 요소와 청각 요소를 정하고, 각각의 효과를 설명하세요.",
            "plan": """
**영상 주제:** 전압은 높지만 위험하지 않은 정전기의 비밀

**장면 1 — 실생활 전기(흐르는 물)**  
- 시각: 거대한 폭포가 쏟아져 물레방아를 돌리는 모습  
- 청각: 물이 거세게 부딪히는 크고 웅장한 소리

**장면 2 — 정전기(고여 있는 물)**  
- 시각 요소: Ⓐ  
- 청각 요소: Ⓑ
""",
            "conditions": [
                "정전기가 ‘높은 곳에 고여 있는 물’과 같다는 특징이 드러나야 합니다.",
                "전하가 이동하지 않고 머무는 상태가 표현되어야 합니다.",
                "각 효과에는 앞에서 쓴 요소와의 연결이 있어야 합니다.",
                "효과의 근거는 반드시 윗글에서 가져옵니다.",
            ],
        },
    },

    "3세트: 인공 지능 그림": {
        "passage_title": "인공 지능이 그린 그림의 예술적 가치",
        "passage": """
생성형 인공 지능이 그린 대표적 작품으로 「에드몽 드 벨라미」가 있습니다. 이 그림은 많은 초상화 자료를 토대로 알고리즘과 데이터를 사용해 만들어졌고 높은 가격에 판매되었습니다.

우리가 올림픽에 열광하는 이유는 선수들의 노력과 열정을 알기 때문입니다. 반면 로봇이 한 번의 실수 없이 완벽하게 피겨 스케이팅을 하더라도 우리의 마음을 울리지는 못합니다.

인간의 작품에는 작가의 감정과 철학, 삶의 경험, 세상을 바라보는 관점, 주변 환경이 종합적으로 담겨 있으므로 예술로 볼 수 있습니다. 하지만 인공 지능은 감정을 느끼지 못하고 독자적인 철학이나 이야기가 없기 때문에 그 그림을 인간의 예술과 같다고 보기는 어렵습니다.

다만 인공 지능의 그림은 기존 미술계에 큰 변화를 가져왔고, 예술의 범주를 확장할 수 있다는 점에서 상징적인 가치가 있습니다.
""",
        "q1": {
            "title": "인간 예술과 인공 지능 그림을 표로 비교하기",
            "prompt": "윗글을 요약한 표의 ㉠~㉢에 들어갈 내용을 찾아 쓰세요.",
            "table": [
                ["대상", "올림픽 경기에 비유", "예술로 볼 수 있는가", "예술로서의 가치"],
                ["인간의 예술", "인간 선수의 노력과 열정이 담긴 경기", "작가의 경험·관점·환경이 담겨 있으므로 예술임", "감상자에게 감동을 줌"],
                ["인공 지능의 예술", "㉠", "㉡", "㉢"],
            ],
            "guide": [
                "㉠에는 인공 지능 그림과 대응되는 로봇 경기의 모습을 씁니다.",
                "㉡에는 예술로 보기 어려운 근거와 결론을 함께 씁니다.",
                "㉢에는 인공 지능 그림이 지닌 가치나 의미를 씁니다.",
            ],
        },
        "q2": {
            "title": "인공 지능 그림을 바라보는 시각 설명하기",
            "prompt": "첫 문장에 이어질 두 문장을 서로 다른 설명 방법으로 작성하세요.",
            "starter": "인공 지능이 그린 그림이 늘어나는 요즘, 우리는 이 작품들을 어떤 눈으로 바라봐야 할지 올바르게 생각해야 한다.",
            "conditions": [
                "(1), (2)에 문장을 하나씩 작성합니다.",
                "두 문장은 서로 다른 설명 방법을 사용해야 합니다.",
                "윗글에 제시된 내용만 활용합니다.",
                "두 문장이 의미상 이어지도록 씁니다.",
                "설명 방법명을 쓰는 경우 문장 끝에 괄호로 표시합니다.",
            ],
            "hints": "인간 예술과 인공 지능 그림의 차이, 예술로 보기 어려운 이유, 상징적 가치를 활용할 수 있습니다.",
        },
        "q3": {
            "title": "인간 예술의 특성을 보여 주는 영상 기획안 완성하기",
            "prompt": "장면 2의 시각 요소와 청각 요소를 정하고, 각각의 효과를 설명하세요. [총 6점]",
            "plan": """
**영상 주제:** 인간의 감정이 담긴 진정한 예술의 가치

**장면 1 — 감정이 없는 완벽한 기술**  
- 시각: 로봇이 실수 없이 완벽하게 피겨 스케이팅하는 모습  
- 청각: 기계음과 일정한 박자의 메트로놈 소리

**장면 2 — 마음에 울림을 주는 인간의 예술**  
- 시각 요소: Ⓐ  
- 청각 요소: Ⓑ
""",
            "conditions": [
                "인간 작품에 작가의 감정·철학·경험·관점·환경이 담긴다는 점이 드러나야 합니다.",
                "작품이 감상자에게 감동이나 울림을 줄 수 있다는 점을 활용할 수 있습니다.",
                "각 효과에는 앞에서 쓴 요소와의 연결이 있어야 합니다.",
                "효과의 근거는 반드시 윗글에서 가져옵니다.",
            ],
        },
    },
}


def render_passage_card(content: Dict):
    st.markdown(f"### 📖 읽을 글: {content['passage_title']}")
    with st.container(border=True):
        st.markdown(content["passage"])


def render_question_header(question: Dict):
    st.markdown(f"## {question['title']}")
    st.info(question["prompt"])


def render_conditions(items: List[str]):
    with st.container(border=True):
        st.markdown("#### ✅ 작성 조건")
        for item in items:
            st.markdown(f"- {item}")


def render_answer_feedback(title: str, result: GradeResult, model: str | None = None):
    with st.container(border=True):
        if result.passed:
            st.success(f"{title}: 통과 ({result.score:.0f}/{result.max_score:.0f})")
        else:
            st.error(f"{title}: 불통과 ({result.score:.0f}/{result.max_score:.0f})")
        for reason in result.reasons:
            st.markdown(f"- {reason}")
        if model:
            st.markdown(f"**모범 답안:** {model}")


# =========================================================
# Streamlit UI
# =========================================================

st.set_page_config(page_title="서·논술형 자동 채점기", page_icon="📝", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1180px; padding-top: 2rem; padding-bottom: 4rem;}
[data-testid="stSidebar"] {min-width: 300px; max-width: 300px;}
div[data-testid="stTextArea"] textarea {font-size: 1.02rem; line-height: 1.65;}
.question-label {font-weight: 700; margin-bottom: .2rem;}
.small-guide {color: #666; font-size: .95rem;}
</style>
""", unsafe_allow_html=True)

st.title("📝 2회 시험 대비 서·논술형 자동 채점기")
st.caption(
    "먼저 글과 문제를 읽고 답을 작성하세요. 채점기는 동의어·유사 표현을 인정하지만, "
    "오개념·설명 방법 불일치·결론 방향 오류는 잡아냅니다."
)

with st.sidebar:
    st.header("채점 설정")
    selected_set = st.selectbox("문항 세트", list(SETS.keys()))
    question_type = st.radio(
        "문항 유형",
        ["서·논술형 1: 표 빈칸", "서·논술형 2: 설명 방법", "서·논술형 3: 영상 기획안"]
    )
    st.divider()
    st.markdown("#### 이용 순서")
    st.markdown("1. 읽을 글 확인\n2. 문제와 조건 확인\n3. 답안 작성\n4. 채점 결과 확인")
    st.divider()
    st.info(
        "새로운 동의어나 창의적인 답안은 자동 채점에서 놓칠 수 있으므로 "
        "교사가 최종 확인해야 합니다."
    )

config = SETS[selected_set]
display = DISPLAY_CONTENT[selected_set]

render_passage_card(display)

st.divider()

if question_type.startswith("서·논술형 1"):
    q = display["q1"]
    render_question_header(q)

    st.markdown("#### 📊 요약 표")
    st.table(q["table"])

    with st.container(border=True):
        st.markdown("#### ✍️ 무엇을 써야 하나요?")
        for item in q["guide"]:
            st.markdown(f"- {item}")

    st.markdown("### 답안 작성")
    cols = st.columns(3)
    answers = {}
    placeholders = {
        "㉠": "㉠에 들어갈 내용을 문장이나 구로 쓰세요.",
        "㉡": "㉡에 들어갈 핵심 내용을 쓰세요.",
        "㉢": "㉢에 들어갈 개념이나 결론을 쓰세요.",
    }
    for col, blank in zip(cols, ["㉠", "㉡", "㉢"]):
        with col:
            answers[blank] = st.text_area(
                f"{blank} 답안",
                height=130,
                placeholder=placeholders[blank],
                key=f"{selected_set}_{blank}",
            )

    if st.button("채점하기", type="primary", use_container_width=True):
        total = 0
        st.markdown("### 채점 결과")
        for blank in ["㉠", "㉡", "㉢"]:
            result = grade_q1_answer(answers[blank], config["q1"][blank])
            total += result.score
            render_answer_feedback(blank, result, config["q1"][blank]["model"])
        st.metric("총점", f"{total:.0f} / 3")

elif question_type.startswith("서·논술형 2"):
    q = display["q2"]
    render_question_header(q)

    with st.container(border=True):
        st.markdown("#### 🧩 주어진 첫 문장")
        st.markdown(f"> {q['starter']}")

    render_conditions(q["conditions"])
    st.caption(f"💡 생각 도움: {q['hints']}")

    with st.expander("설명 방법 6가지 빠르게 확인하기"):
        st.table([
            {"방법": "정의", "어떻게 쓰나요?": "대상의 뜻이나 개념을 밝힙니다.", "표지 예": "~란, ~을 말한다"},
            {"방법": "예시", "어떻게 쓰나요?": "구체적인 사례를 듭니다.", "표지 예": "예를 들어, 가령"},
            {"방법": "인과", "어떻게 쓰나요?": "원인과 결과를 연결합니다.", "표지 예": "~때문에, 따라서"},
            {"방법": "분석", "어떻게 쓰나요?": "대상을 둘 이상의 요소로 나눕니다.", "표지 예": "~에는 A, B, C가 있다"},
            {"방법": "비교와 대조", "어떻게 쓰나요?": "두 대상의 공통점이나 차이점을 밝힙니다.", "표지 예": "반면, ~와 달리"},
            {"방법": "분류와 구분", "어떻게 쓰나요?": "기준에 따라 종류를 나눕니다.", "표지 예": "~에 따라 ~로 나뉜다"},
        ])

    st.markdown("### 답안 작성")
    c1, c2 = st.columns(2)
    with c1:
        answer1 = st.text_area(
            "(1) 첫 번째 문장",
            height=165,
            placeholder="지문의 내용을 활용해 한 문장을 쓰세요. 예: 문장 끝에 (비교와 대조)",
            key=f"{selected_set}_q2_1",
        )
    with c2:
        answer2 = st.text_area(
            "(2) 두 번째 문장",
            height=165,
            placeholder="첫 문장과 다른 설명 방법으로 한 문장을 쓰세요.",
            key=f"{selected_set}_q2_2",
        )

    if st.button("채점하기", type="primary", use_container_width=True):
        result = grade_q2([answer1, answer2], config["q2"])
        st.markdown("### 채점 결과")
        if result.passed:
            st.success(f"통과 ({result.score:.0f}/{result.max_score:.0f})")
        else:
            st.error(f"불통과 ({result.score:.0f}/{result.max_score:.0f})")
        for reason in result.reasons:
            st.markdown(f"- {reason}")

    st.divider()
    with st.expander("선택 가능한 설명 방법 조합별 모범 답안 보기"):
        for combo, models in config["q2"]["models"].items():
            st.markdown(f"#### {combo}")
            st.markdown(f"**(1)** {models[0]}")
            st.markdown(f"**(2)** {models[1]}")
            st.divider()

else:
    q = display["q3"]
    render_question_header(q)

    with st.container(border=True):
        st.markdown("#### 🎬 영상 기획안")
        st.markdown(q["plan"])

    render_conditions(q["conditions"])

    st.markdown("### 답안 작성")
    left, right = st.columns(2)
    with left:
        st.markdown("#### 👀 시각 요소")
        visual_element = st.text_area(
            "Ⓐ 화면에 무엇을 보여 줄까요?",
            height=125,
            placeholder="인물, 장소, 행동, 화면 분위기를 구체적으로 쓰세요.",
            key=f"{selected_set}_visual_element",
        )
        visual_effect = st.text_area(
            "이 시각 요소는 어떤 내용을 전달하나요?",
            height=155,
            placeholder="앞에서 쓴 화면이 지문의 어떤 내용을 보여 주는지 설명하세요.",
            key=f"{selected_set}_visual_effect",
        )
    with right:
        st.markdown("#### 🔊 청각 요소")
        audio_element = st.text_area(
            "Ⓑ 어떤 소리를 들려줄까요?",
            height=125,
            placeholder="배경음악, 효과음, 목소리, 정적 등을 구체적으로 쓰세요.",
            key=f"{selected_set}_audio_element",
        )
        audio_effect = st.text_area(
            "이 청각 요소는 어떤 내용을 전달하나요?",
            height=155,
            placeholder="앞에서 쓴 소리가 지문의 어떤 내용을 강조하는지 설명하세요.",
            key=f"{selected_set}_audio_effect",
        )

    with st.expander("6점 배점 기준 확인하기"):
        st.table([
            {"평가 요소": "시각 요소", "배점": 1, "확인 내용": "지문 핵심 특성을 화면으로 표현했는가"},
            {"평가 요소": "시각 효과–요소 연결", "배점": 1, "확인 내용": "앞에서 쓴 화면과 효과 설명이 연결되는가"},
            {"평가 요소": "시각 효과–본문 근거", "배점": 1, "확인 내용": "효과에 지문의 핵심 내용이 들어 있는가"},
            {"평가 요소": "청각 요소", "배점": 1, "확인 내용": "지문 핵심 특성을 소리로 표현했는가"},
            {"평가 요소": "청각 효과–요소 연결", "배점": 1, "확인 내용": "앞에서 쓴 소리와 효과 설명이 연결되는가"},
            {"평가 요소": "청각 효과–본문 근거", "배점": 1, "확인 내용": "효과에 지문의 핵심 내용이 들어 있는가"},
        ])

    if st.button("채점하기", type="primary", use_container_width=True):
        result = grade_q3(
            visual_element, visual_effect, audio_element, audio_effect, config["q3"]
        )
        st.markdown("### 채점 결과")
        if result.passed:
            st.success(f"통과 ({result.score:.0f}/{result.max_score:.0f})")
        else:
            st.warning(f"부분 점수 또는 불통과 ({result.score:.0f}/{result.max_score:.0f})")
        for reason in result.reasons:
            st.markdown(f"- {reason}")

        with st.expander("모범 답안 확인하기"):
            models = config["q3"]["models"]
            st.markdown(f"**시각 요소:** {models['시각 요소']}")
            st.markdown(f"**시각 효과:** {models['시각 효과']}")
            st.markdown(f"**청각 요소:** {models['청각 요소']}")
            st.markdown(f"**청각 효과:** {models['청각 효과']}")

st.divider()
st.caption(
    "설계 원칙: 문제·지문·작성 조건을 화면에 함께 제시 / 의미 기반 동의어 허용 / "
    "설명 방법 실제 구조 검증 / 다른 개념의 특성 전이 차단 / 요구 결론 방향 확인"
)
'''

new_code = head + marker + new_ui
app_path.write_text(new_code, encoding="utf-8")

# Syntax check
compile(new_code, str(app_path), "exec")

# README update
readme_path = Path("/mnt/data/essay_grader_streamlit/README.md")
readme = readme_path.read_text(encoding="utf-8")
readme += """

## 화면 개선 사항

- 각 세트의 읽을 글을 앱 화면에 함께 제시
- 문항의 발문, 표, 첫 문장, 영상 기획안 표시
- 학생이 무엇을 써야 하는지 답란별 안내 제공
- 작성 조건과 설명 방법 도움말 제공
- 모범 답안은 답안 작성 뒤 확인할 수 있도록 접기 영역으로 배치
"""
readme_path.write_text(readme, encoding="utf-8")

zip_path = Path("/mnt/data/essay_grader_streamlit_ui_improved.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for p in Path("/mnt/data/essay_grader_streamlit").iterdir():
        z.write(p, arcname=p.name)

print(zip_path)
