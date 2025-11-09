# app_input.py
from pathlib import Path
import pandas as pd
import streamlit as st

# ====== 기본 설정 ======
st.set_page_config(page_title="밥픽 | 메뉴 입력", page_icon="🍱", layout="centered")
CSV_PATH = Path("data/menus.csv")
CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

VALID_CUISINES = ["한식","양식","중식","일식","아시아","분식","치킨","피자"]
VALID_TAG_MAIN = ["튀김","국물","볶음","구이","찜","날 것","절임"]
VALID_TAG_SUB  = ["", "밥","빵","면"]         # 빈 값 허용
VALID_TAG_LEVEL= ["상","중","하"]
TASTE_COLS = [
    "taste_sweet","taste_bitter",
    "taste_savory","taste_plain",
    "taste_salty","taste_mild",
    "taste_spicy","taste_acid","taste_nutty"
]

def ensure_csv():
    if not CSV_PATH.exists():
        cols = ["id","name","cuisine","tag_main","tag_sub","tag_level",
                "price_low","price_high", *TASTE_COLS, "notes"]
        pd.DataFrame(columns=cols).to_csv(CSV_PATH, index=False, encoding="utf-8")

def load_df():
    ensure_csv()
    df = pd.read_csv(CSV_PATH)

    expected = [
        "id","name","cuisine","tag_main","tag_sub","tag_level",
        "price_low","price_high",
        "taste_sweet","taste_bitter","taste_savory","taste_plain",
        "taste_salty","taste_mild","taste_spicy","taste_acid","taste_nutty",
        "notes"
    ]

    # 1) 누락 컬럼을 행 수만큼 NA로 추가 (길이 불일치 방지)
    for c in expected:
        if c not in df.columns:
            if c == "id":
                df[c] = pd.Series([pd.NA]*len(df), dtype="Int64")
            else:
                df[c] = pd.Series([pd.NA]*len(df), dtype="object")

    # 2) 자료형 보정 (가능하면 숫자형으로)
    num_cols = ["price_low","price_high",
                "taste_sweet","taste_bitter","taste_savory","taste_plain",
                "taste_salty","taste_mild","taste_spicy","taste_acid","taste_nutty"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")  # 숫자 아닌 건 NaN

    if "id" in df.columns:
        # id는 정수 NA 허용
        try:
            df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
        except Exception:
            df["id"] = pd.Series([pd.NA]*len(df), dtype="Int64")

    # 3) 컬럼 순서 정렬
    df = df[expected]

    return df

def next_id(df: pd.DataFrame) -> int:
    if df.empty or df["id"].isna().all():
        return 1
    return int(df["id"].max()) + 1

def is_duplicate(df: pd.DataFrame, row: dict) -> bool:
    if df.empty: return False
    mask = (
        (df["name"] == row["name"]) &
        (df["cuisine"] == row["cuisine"]) &
        (df["tag_main"] == row["tag_main"])
    )
    return mask.any()

def validate_row(row: dict) -> list:
    errs = []
    if not row["name"]:
        errs.append("음식 이름은 필수입니다.")
    if row["cuisine"] not in VALID_CUISINES:
        errs.append(f"대분류(cuisine) 값이 유효하지 않습니다: {row['cuisine']}")
    if row["tag_main"] not in VALID_TAG_MAIN:
        errs.append(f"메인태그(tag_main) 값이 유효하지 않습니다: {row['tag_main']}")
    if row["tag_sub"] not in VALID_TAG_SUB:
        errs.append(f"서브태그(tag_sub) 값이 유효하지 않습니다: {row['tag_sub']}")
    if row["tag_level"] not in VALID_TAG_LEVEL:
        errs.append(f"레벨(tag_level) 값이 유효하지 않습니다: {row['tag_level']}")
    try:
        pl = int(row["price_low"]); ph = int(row["price_high"])
        if pl < 0 or ph < 0: errs.append("가격은 0 이상이어야 합니다.")
        if pl > ph: errs.append("가격 하한이 상한보다 클 수 없습니다.")
    except Exception:
        errs.append("가격 입력이 올바르지 않습니다(정수).")
    for c in TASTE_COLS:
        v = row[c]
        if not isinstance(v, int) or not (0 <= v <= 5):
            errs.append(f"{c} 값은 0~5의 정수여야 합니다. (현재: {v})")
    return errs

# ====== UI ======
st.title("🍱 밥픽 | 메뉴 입력 (Streamlit MVP)")

with st.expander("입력 가이드", expanded=False):
    st.markdown("""
- **대분류**: 한식/양식/중식/일식/아시아/분식/치킨/피자  
- **메인 태그**: 튀김/국물/볶음/구이/찜/날 것/절임  
- **서브 태그**: 밥/빵/면 (없으면 빈 값)  
- **레벨**: 상(든든/고칼), 중(일반), 하(가벼움)  
- **맛 점수(0~5)**: 팀 기준표에 맞춰 정수 입력 (예: 불닭=매움5)
""")

c1, c2 = st.columns([1.15, 1])

with c1:
    st.subheader("새 메뉴 등록")
    name = st.text_input("음식 이름 *", placeholder="예: 김치볶음밥")
    cuisine = st.selectbox("대분류(국가/계열) *", VALID_CUISINES, index=0)
    tag_main = st.selectbox("메인 태그(조리방식) *", VALID_TAG_MAIN, index=2)   # 볶음
    tag_sub  = st.selectbox("서브 태그(주식/빵/면)", VALID_TAG_SUB, index=0)     # ""
    tag_level= st.selectbox("레벨(상/중/하) *", VALID_TAG_LEVEL, index=1)

    c3, c4 = st.columns(2)
    with c3:
        price_low  = st.number_input("가격 하한(원)", min_value=0, step=100, value=7000)
    with c4:
        price_high = st.number_input("가격 상한(원)", min_value=0, step=100, value=9000)

    st.markdown("**맛 점수 (0~5)**")
    r1, r2, r3 = st.columns(3)
    with r1:
        taste_sweet  = st.slider("단맛", 0, 5, 2)
        taste_savory = st.slider("느끼/기름짐", 0, 5, 3)
        taste_salty  = st.slider("짠맛", 0, 5, 3)
    with r2:
        taste_bitter = st.slider("쓴맛", 0, 5, 1)
        taste_plain  = st.slider("담백", 0, 5, 1)
        taste_mild   = st.slider("심심/저염", 0, 5, 1)
    with r3:
        taste_spicy  = st.slider("매움", 0, 5, 2)
        taste_acid   = st.slider("신맛", 0, 5, 1)
        taste_nutty  = st.slider("고소", 0, 5, 1)

    notes = st.text_input("비고", placeholder="예: 김치 산미 약간, 기본형")

    if st.button("💾 저장", use_container_width=True):
        df = load_df()
        row = {
            "id": next_id(df),
            "name": name.strip(),
            "cuisine": cuisine,
            "tag_main": tag_main,
            "tag_sub": tag_sub,
            "tag_level": tag_level,
            "price_low": int(price_low),
            "price_high": int(price_high),
            "taste_sweet": int(taste_sweet),
            "taste_bitter": int(taste_bitter),
            "taste_savory": int(taste_savory),
            "taste_plain": int(taste_plain),
            "taste_salty": int(taste_salty),
            "taste_mild": int(taste_mild),
            "taste_spicy": int(taste_spicy),
            "taste_acid": int(taste_acid),
            "taste_nutty": int(taste_nutty),
            "notes": notes.strip()
        }

        errors = validate_row(row)
        if errors:
            st.error("입력 오류가 있습니다:")
            for e in errors:
                st.write("- " + e)
        elif is_duplicate(df, row):
            st.warning("중복 항목으로 판단되어 저장하지 않았습니다. (이름+대분류+메인태그 일치)")
        else:
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df.to_csv(CSV_PATH, index=False, encoding="utf-8")
            st.success("저장 완료!")
            st.balloons()

with c2:
    st.subheader("최근 등록 미리보기")
    df = load_df()
    st.caption(f"총 {len(df)}개 등록됨")
    if df.empty:
        st.info("아직 등록된 메뉴가 없습니다.")
    else:
        st.dataframe(
            df.sort_values("id", ascending=False).head(12)[
                ["id","name","cuisine","tag_main","tag_sub","price_low","price_high"]
            ],
            use_container_width=True
        )

# 데모 프리셋 (선택)
st.divider()
with st.expander("🧪 프리셋 3개 추가(데모용)"):
    if st.button("프리셋 추가"):
        base = load_df()
        start_id = next_id(base)
        presets = [
            {
                "id": start_id, "name":"김치볶음밥","cuisine":"한식","tag_main":"볶음","tag_sub":"밥","tag_level":"중",
                "price_low":7000,"price_high":9000,
                "taste_sweet":2,"taste_bitter":1,"taste_savory":3,"taste_plain":1,"taste_salty":3,"taste_mild":1,"taste_spicy":2,"taste_acid":1,"taste_nutty":1,
                "notes":"김치 산미 약간, 기본형"
            },
            {
                "id": start_id+1, "name":"부대찌개","cuisine":"한식","tag_main":"국물","tag_sub":"밥","tag_level":"상",
                "price_low":7000,"price_high":10000,
                "taste_sweet":1,"taste_bitter":0,"taste_savory":3,"taste_plain":1,"taste_salty":3,"taste_mild":1,"taste_spicy":2,"taste_acid":1,"taste_nutty":0,
                "notes":"국물/든든/매콤"
            },
            {
                "id": start_id+2, "name":"치즈버거","cuisine":"양식","tag_main":"구이","tag_sub":"빵","tag_level":"중",
                "price_low":5000,"price_high":8000,
                "taste_sweet":1,"taste_bitter":0,"taste_savory":3,"taste_plain":0,"taste_salty":2,"taste_mild":1,"taste_spicy":0,"taste_acid":0,"taste_nutty":2,
                "notes":"빵/패티/치즈"
            },
        ]
        combined = pd.concat([base, pd.DataFrame(presets)], ignore_index=True)
        combined.to_csv(CSV_PATH, index=False, encoding="utf-8")
        st.success("프리셋 추가 완료. 위 미리보기에서 확인하세요.")
