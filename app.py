# app.py - 밥픽 데스크톱 입력기 (PySimpleGUI)
# 기능: 폼 입력 → data/menus.csv 저장, 기본 밸리데이션, 중복 방지

import PySimpleGUI as sg
import pandas as pd
from pathlib import Path

# ----- 고정 리스트 (유효 값) -----
VALID_CUISINES = ["한식","양식","중식","일식","아시아","분식","치킨","피자"]
VALID_TAG_MAIN = ["튀김","국물","볶음","구이","찜","날 것","절임"]
VALID_TAG_SUB  = ["", "밥","빵","면"]   # 빈 값 허용
VALID_TAG_LEVEL= ["상","중","하"]

TASTE_COLS = [
    "taste_sweet","taste_bitter",
    "taste_savory","taste_plain",
    "taste_salty","taste_mild",
    "taste_spicy","taste_acid","taste_nutty"
]

CSV_PATH = Path("data/menus.csv")

def ensure_csv():
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        cols = [
            "id","name","cuisine","tag_main","tag_sub","tag_level",
            "price_low","price_high",
            *TASTE_COLS,
            "notes"
        ]
        pd.DataFrame(columns=cols).to_csv(CSV_PATH, index=False, encoding="utf-8")

def load_df():
    ensure_csv()
    try:
        df = pd.read_csv(CSV_PATH)
    except Exception:
        df = pd.DataFrame()
    return df

def next_id(df: pd.DataFrame) -> int:
    if df.empty or "id" not in df.columns or df["id"].isna().all():
        return 1
    try:
        return int(df["id"].max()) + 1
    except Exception:
        return 1

def is_duplicate(df: pd.DataFrame, row: dict) -> bool:
    if df.empty:
        return False
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
    # 가격
    try:
        pl = int(row["price_low"])
        ph = int(row["price_high"])
        if pl < 0 or ph < 0:
            errs.append("가격은 0 이상이어야 합니다.")
        if pl > ph:
            errs.append("가격 하한이 상한보다 클 수 없습니다.")
    except Exception:
        errs.append("가격 입력이 올바르지 않습니다(정수).")
    # 맛 점수 0~5
    for c in TASTE_COLS:
        v = row[c]
        if not isinstance(v, int) or not (0 <= v <= 5):
            errs.append(f"{c} 값은 0~5의 정수여야 합니다. (현재: {v})")
    return errs

def make_layout():
    sg.theme("SystemDefault")
    left = [
        [sg.Text("🍱 밥픽 | 메뉴 입력기", font=("Malgun Gothic", 14, "bold"))],
        [sg.Text("음식 이름 *"), sg.Input(key="-NAME-", size=(30,1))],
        [sg.Text("대분류 *", size=(12,1)), sg.Combo(VALID_CUISINES, default_value=VALID_CUISINES[0], key="-CUISINE-", readonly=True)],
        [sg.Text("메인 태그 *", size=(12,1)), sg.Combo(VALID_TAG_MAIN, default_value="볶음", key="-TAGMAIN-", readonly=True)],
        [sg.Text("서브 태그", size=(12,1)), sg.Combo(VALID_TAG_SUB, default_value="", key="-TAGSUB-", readonly=True)],
        [sg.Text("레벨 *", size=(12,1)), sg.Combo(VALID_TAG_LEVEL, default_value="중", key="-LEVEL-", readonly=True)],
        [sg.HorizontalSeparator()],
        [sg.Text("가격 하한"), sg.Input("7000", key="-PLOW-", size=(8,1)),
         sg.Text("상한"), sg.Input("9000", key="-PHIGH-", size=(8,1))],
        [sg.HorizontalSeparator()],
        [sg.Text("맛 점수 (0~5 정수)", font=("Malgun Gothic", 10, "bold"))],
        [sg.Text("단맛"), sg.Spin([i for i in range(6)], initial_value=2, key="-T_SWEET-", size=(3,1)),
         sg.Text("쓴맛"), sg.Spin([i for i in range(6)], initial_value=1, key="-T_BITTER-", size=(3,1)),
         sg.Text("매움"), sg.Spin([i for i in range(6)], initial_value=2, key="-T_SPICY-", size=(3,1))],
        [sg.Text("짠맛"), sg.Spin([i for i in range(6)], initial_value=3, key="-T_SALTY-", size=(3,1)),
         sg.Text("심심"), sg.Spin([i for i in range(6)], initial_value=1, key="-T_MILD-", size=(3,1)),
         sg.Text("신맛"), sg.Spin([i for i in range(6)], initial_value=1, key="-T_ACID-", size=(3,1))],
        [sg.Text("느끼"), sg.Spin([i for i in range(6)], initial_value=3, key="-T_SAVORY-", size=(3,1)),
         sg.Text("담백"), sg.Spin([i for i in range(6)], initial_value=1, key="-T_PLAIN-", size=(3,1)),
         sg.Text("고소"), sg.Spin([i for i in range(6)], initial_value=1, key="-T_NUTTY-", size=(3,1))],
        [sg.Text("비고"), sg.Input(key="-NOTES-", size=(40,1), default_text="")],
        [sg.Button("저장", key="-SAVE-", bind_return_key=True), sg.Button("닫기", key="-EXIT-")]
    ]

    right = [
        [sg.Text("최근 등록 (상위 12개)")],
        [sg.Table(values=[],
                  headings=["id","name","cuisine","tag_main","tag_sub","price_low","price_high"],
                  key="-TABLE-",
                  auto_size_columns=True,
                  justification="left",
                  num_rows=12,
                  expand_x=True)]
    ]

    layout = [[sg.Column(left, vertical_alignment="top"), sg.VSeparator(), sg.Column(right, vertical_alignment="top")]]
    return layout

def refresh_table(window):
    df = load_df()
    if df.empty:
        window["-TABLE-"].update(values=[])
        return
    show = df[["id","name","cuisine","tag_main","tag_sub","price_low","price_high"]].sort_values("id", ascending=False).head(12)
    window["-TABLE-"].update(values=show.values.tolist())

def main():
    ensure_csv()
    window = sg.Window("밥픽 입력기", make_layout(), finalize=True)
    refresh_table(window)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "-EXIT-"):
            break
        if event == "-SAVE-":
            # 입력값 수집
            row = {
                "id": None,
                "name": values["-NAME-"].strip(),
                "cuisine": values["-CUISINE-"],
                "tag_main": values["-TAGMAIN-"],
                "tag_sub": values["-TAGSUB-"],
                "tag_level": values["-LEVEL-"],
                "price_low": values["-PLOW-"],
                "price_high": values["-PHIGH-"],
                "taste_sweet": int(values["-T_SWEET-"]),
                "taste_bitter": int(values["-T_BITTER-"]),
                "taste_savory": int(values["-T_SAVORY-"]),
                "taste_plain": int(values["-T_PLAIN-"]),
                "taste_salty": int(values["-T_SALTY-"]),
                "taste_mild": int(values["-T_MILD-"]),
                "taste_spicy": int(values["-T_SPICY-"]),
                "taste_acid": int(values["-T_ACID-"]),
                "taste_nutty": int(values["-T_NUTTY-"]),
                "notes": values["-NOTES-"].strip()
            }
            # 검증
            errs = validate_row(row)
            if errs:
                sg.popup_error("입력 오류:\n- " +    "\n- ".join(errs))
                continue
            # 저장
            df = load_df()
            if is_duplicate(df, row):
                sg.popup("중복 항목입니다. (이름+대분류+메인태그 일치)")
                continue
            row["id"] = next_id(df)
            # 숫자형 변환
            row["price_low"] = int(row["price_low"])
            row["price_high"] = int(row["price_high"])
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df.to_csv(CSV_PATH, index=False, encoding="utf-8")
            sg.popup("저장 완료!")
            refresh_table(window)
            # 일부 필드 초기화
            window["-NAME-"].update("")
            window["-NOTES-"].update("")
    window.close()

if __name__ == "__main__":
    main()
