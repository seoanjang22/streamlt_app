import streamlit as st
import random

st.set_page_config(
    page_title="오늘의 날씨 음식 추천",
    page_icon="🍽️",
    layout="centered"
)

st.title("🍽️ 오늘의 날씨 음식 추천")
st.write("오늘의 날씨를 선택하면 어울리는 음식을 추천해드립니다.")

weather = st.selectbox(
    "오늘의 날씨",
    ["맑음", "비", "눈", "흐림", "더움", "추움"]
)

foods = {
    "맑음": [
        {
            "name": "샌드위치",
            "image": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af",
            "calorie": "420 kcal",
            "nutrition": {
                "탄수화물": "42 g",
                "단백질": "18 g",
                "지방": "16 g"
            }
        },
        {
            "name": "샐러드",
            "image": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c",
            "calorie": "280 kcal",
            "nutrition": {
                "탄수화물": "18 g",
                "단백질": "12 g",
                "지방": "14 g"
            }
        }
    ],

    "비": [
        {
            "name": "김치전",
            "image": "https://images.unsplash.com/photo-1604908176997-4316fdb17f97",
            "calorie": "520 kcal",
            "nutrition": {
                "탄수화물": "48 g",
                "단백질": "11 g",
                "지방": "30 g"
            }
        },
        {
            "name": "칼국수",
            "image": "https://images.unsplash.com/photo-1617093727343-374698b1b08d",
            "calorie": "610 kcal",
            "nutrition": {
                "탄수화물": "82 g",
                "단백질": "22 g",
                "지방": "15 g"
            }
        }
    ],

    "눈": [
        {
            "name": "떡국",
            "image": "https://images.unsplash.com/photo-1555126634-323283e090fa",
            "calorie": "470 kcal",
            "nutrition": {
                "탄수화물": "63 g",
                "단백질": "20 g",
                "지방": "12 g"
            }
        },
        {
            "name": "우동",
            "image": "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841",
            "calorie": "540 kcal",
            "nutrition": {
                "탄수화물": "75 g",
                "단백질": "18 g",
                "지방": "16 g"
            }
        }
    ],

    "흐림": [
        {
            "name": "비빔밥",
            "image": "https://images.unsplash.com/photo-1590301157890-4810ed352733",
            "calorie": "620 kcal",
            "nutrition": {
                "탄수화물": "73 g",
                "단백질": "22 g",
                "지방": "20 g"
            }
        },
        {
            "name": "볶음밥",
            "image": "https://images.unsplash.com/photo-1603133872878-684f208fb84b",
            "calorie": "590 kcal",
            "nutrition": {
                "탄수화물": "78 g",
                "단백질": "16 g",
                "지방": "18 g"
            }
        }
    ],

    "더움": [
        {
            "name": "냉면",
            "image": "https://images.unsplash.com/photo-1627308595229-7830a5c91f9f",
            "calorie": "480 kcal",
            "nutrition": {
                "탄수화물": "72 g",
                "단백질": "18 g",
                "지방": "8 g"
            }
        },
        {
            "name": "빙수",
            "image": "https://images.unsplash.com/photo-1563805042-7684c019e1cb",
            "calorie": "390 kcal",
            "nutrition": {
                "탄수화물": "70 g",
                "단백질": "6 g",
                "지방": "7 g"
            }
        }
    ],

    "추움": [
        {
            "name": "삼계탕",
            "image": "https://images.unsplash.com/photo-1544025162-d76694265947",
            "calorie": "720 kcal",
            "nutrition": {
                "탄수화물": "35 g",
                "단백질": "48 g",
                "지방": "30 g"
            }
        },
        {
            "name": "부대찌개",
            "image": "https://images.unsplash.com/photo-1547592180-85f173990554",
            "calorie": "680 kcal",
            "nutrition": {
                "탄수화물": "40 g",
                "단백질": "35 g",
                "지방": "38 g"
            }
        }
    ]
}

if st.button("🍴 음식 추천받기"):

    food = random.choice(foods[weather])

    st.header(food["name"])

    st.image(food["image"], use_container_width=True)

    st.subheader("🔥 칼로리")
    st.write(food["calorie"])

    st.subheader("🥗 영양성분")

    col1, col2, col3 = st.columns(3)

    col1.metric("탄수화물", food["nutrition"]["탄수화물"])
    col2.metric("단백질", food["nutrition"]["단백질"])
    col3.metric("지방", food["nutrition"]["지방"])
