import streamlit as st
import pandas as pd
import datetime
import json
import os
import altair as alt

st.set_page_config(
    page_title="منظّم حياة الطالب الذكي",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; }
    div[data-testid="stSidebarUserContent"] { direction: rtl; text-align: right; }
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] { text-align: right !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { font-weight: bold; font-size: 16px; }
</style>
""", unsafe_allow_html=True)

DATA_FILE = "student_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"daily_free_hours": 4.0, "schedule": [], "tasks": [], "grades": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def calculate_days_left(due_date_str):
    today = datetime.date.today()
    due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
    return (due_date - today).days

def get_prioritized_tasks(tasks):
    type_weights = {"اختبار": 3.0, "مشروع": 2.5, "واجب": 1.5}
    enriched = []
    for idx, task in enumerate(tasks):
        if task.get("completed", False):
            continue
        days_left = calculate_days_left(task["due_date"])
        weight = type_weights.get(task["type"], 1.0)
        urgency_score = 100.0 if days_left <= 0 else round(50.0 / days_left, 1)
        priority_score = round((weight * 10) + (task["difficulty"] * 5) + urgency_score, 1)

        t_copy = task.copy()
        t_copy["original_index"] = idx
        t_copy["days_left"] = days_left
        t_copy["priority_score"] = priority_score
        enriched.append(t_copy)

    enriched.sort(key=lambda x: (-x["priority_score"], x["days_left"]))
    return enriched

def generate_study_plan(prioritized_tasks, daily_free_hours):
    active_tasks = [t.copy() for t in prioritized_tasks if t["days_left"] >= 0]
    today = datetime.date.today()
    plan_rows = []
    for day_offset in range(14):
        current_date = today + datetime.timedelta(days=day_offset)
        available_hours = daily_free_hours
        for task in active_tasks:
            if task["est_hours"] <= 0:
                continue
            if day_offset <= task["days_left"] and available_hours > 0:
                allocated = min(available_hours, task["est_hours"], 2.5)
                if allocated > 0:
                    task["est_hours"] -= allocated
                    available_hours -= allocated
                    plan_rows.append({
                        "التاريخ": current_date.strftime("%Y-%m-%d"),
                        "اليوم": current_date.strftime("%A"),
                        "المادة": task["subject"],
                        "المهمة": f"{task['type']} - {task['title']}",
                        "الساعات المقترحة": round(allocated, 1),
                        "مؤشر الأولوية": task["priority_score"]
                    })
    return pd.DataFrame(plan_rows)

def load_sample_data():
    today = datetime.date.today()
    sample = {
        "daily_free_hours": 4.5,
        "schedule": [
            {"day": "الأحد", "subject": "برمجة بايثون", "start_time": "08:00", "end_time": "10:00"},
            {"day": "الإثنين", "subject": "قواعد البيانات SQL", "start_time": "10:00", "end_time": "12:00"},
            {"day": "الثلاثاء", "subject": "الإحصاء والاحتمالات", "start_time": "09:00", "end_time": "11:00"},
            {"day": "الأربعاء", "subject": "الذكاء الاصطناعي", "start_time": "11:00", "end_time": "13:00"}
        ],
        "tasks": [
            {"title": "الاختبار النصفي", "subject": "الإحصاء والاحتمالات", "type": "اختبار", "due_date": (today + datetime.timedelta(days=2)).strftime("%Y-%m-%d"), "est_hours": 6.0, "difficulty": 5, "completed": False},
            {"title": "تصميم قاعدة بيانات", "subject": "قواعد البيانات SQL", "type": "مشروع", "due_date": (today + datetime.timedelta(days=5)).strftime("%Y-%m-%d"), "est_hours": 5.0, "difficulty": 4, "completed": False},
            {"title": "تحليل البيانات بـ Pandas", "subject": "برمجة بايثون", "type": "واجب", "due_date": (today + datetime.timedelta(days=7)).strftime("%Y-%m-%d"), "est_hours": 3.0, "difficulty": 3, "completed": False},
            {"title": "اختبار قصير (Quiz 2)", "subject": "الذكاء الاصطناعي", "type": "اختبار", "due_date": (today + datetime.timedelta(days=10)).strftime("%Y-%m-%d"), "est_hours": 4.0, "difficulty": 4, "completed": False}
        ],
        "grades": [
            {"subject": "برمجة بايثون", "assessment": "الاختبار الأول", "score": 19.0, "max_score": 20.0, "percentage": 95.0},
            {"subject": "قواعد البيانات SQL", "assessment": "الاختبار الأول", "score": 17.5, "max_score": 20.0, "percentage": 87.5},
            {"subject": "الإحصاء والاحتمالات", "assessment": "الاختبار الأول", "score": 15.0, "max_score": 20.0, "percentage": 75.0},
            {"subject": "الذكاء الاصطناعي", "assessment": "واجب عملي", "score": 9.0, "max_score": 10.0, "percentage": 90.0}
        ]
    }
    save_data(sample)
    st.session_state.data = sample

if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

with st.sidebar:
    st.title("⚙️ إعدادات المنظّم")
    new_free_hours = st.slider("⏳ ساعات الفراغ المتاحة يومياً:", 1.0, 12.0, float(data.get("daily_free_hours", 4.0)), 0.5)
    if new_free_hours != data.get("daily_free_hours"):
        data["daily_free_hours"] = new_free_hours
        save_data(data)

    st.divider()
    if st.button("📥 تحميل بيانات تجريبية جاهزة", use_container_width=True, type="primary"):
        load_sample_data()
        st.rerun()

    if st.button("🗑️ مسح جميع البيانات", use_container_width=True):
        empty_data = {"daily_free_hours": 4.0, "schedule": [], "tasks": [], "grades": []}
        save_data(empty_data)
        st.session_state.data = empty_data
        st.rerun()

st.title("🎓 منظّم حياة الطالب الذكي")

prioritized_tasks = get_prioritized_tasks(data["tasks"])
total_pending_hours = sum(t["est_hours"] for t in prioritized_tasks)
avg_grade = pd.DataFrame(data["grades"])["percentage"].mean() if data["grades"] else 0.0
nearest_days = min([t["days_left"] for t in prioritized_tasks if t["days_left"] >= 0], default=None)

col1, col2, col3, col4 = st.columns(4)
col1.metric("📌 المهام غير المكتملة", f"{len(prioritized_tasks)} مهام")
col2.metric("⏰ الساعات المطلوبة", f"{total_pending_hours:.1f} ساعة")
col3.metric("🔔 أقرب موعد", f"بعد {nearest_days} يوم" if nearest_days is not None else "لا يوجد")
col4.metric("📊 المعدل العام", f"{avg_grade:.1f}%" if data["grades"] else "غير مسجل")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "🔔 التنبيهات والأولويات",
    "📅 خطة المذاكرة الذكية",
    "➕ إدخال الجدول والمهام",
    "📊 تحليل الأداء والرسوم البيانية"
])

with tab1:
    st.subheader("🔔 مركز التنبيهات والمواعيد القادمة")
    if not prioritized_tasks:
        st.info("🎉 لا توجد مهام معلقة! اضغط على (تحميل بيانات تجريبية جاهزة) من القائمة الجانبية لتجربة النظام.")
    else:
        for t in prioritized_tasks:
            days = t["days_left"]
            msg = f"**[{t['type']}] {t['title']}** — مادة: **{t['subject']}** | الموعد: `{t['due_date']}` | الساعات: `{t['est_hours']}` | الأولوية: `{t['priority_score']}`"
            if days <= 0:
                st.error(f"🚨 عاجل/متأخر — {msg}")
            elif days <= 3:
                st.warning(f"⚠️ عاجل جداً (متبقي {days} أيام) — {msg}")
            elif days <= 7:
                st.info(f"⏳ قريب (متبقي {days} أيام) — {msg}")
            else:
                st.success(f"📅 متبقي {days} يوم — {msg}")

        df_prio = pd.DataFrame(prioritized_tasks)[["title", "subject", "type", "due_date", "days_left", "est_hours", "difficulty", "priority_score"]]
        df_prio.columns = ["المهمة", "المادة", "النوع", "الموعد", "الأيام المتبقية", "الساعات", "الصعوبة", "نقاط الأولوية"]
        st.dataframe(df_prio, use_container_width=True, hide_index=True)

        task_options = {f"{t['type']}: {t['title']} ({t['subject']})": t["original_index"] for t in prioritized_tasks}
        selected_task_label = st.selectbox("اختر مهمة لتمييزها كمكتملة:", list(task_options.keys()))
        if st.button("✔️ تم إنجاز هذه المهمة"):
            data["tasks"][task_options[selected_task_label]]["completed"] = True
            save_data(data)
            st.rerun()

with tab2:
    st.subheader(f"📚 جدول المذاكرة المقترح ({data['daily_free_hours']} ساعات يومياً)")
    df_plan = generate_study_plan(prioritized_tasks, data["daily_free_hours"])
    if df_plan.empty:
        st.info("لا توجد مهام قادمة لجدولتها حالياً.")
    else:
        st.dataframe(df_plan, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🗓️ الجدول الدراسي الأسبوعي")
    if data["schedule"]:
        df_sched = pd.DataFrame(data["schedule"])
        df_sched.columns = ["اليوم", "المادة", "وقت البداية", "وقت النهاية"]
        st.table(df_sched)

with tab3:
    col_form1, col_form2 = st.columns(2)
    with col_form1:
        st.subheader("📝 إضافة اختبار أو واجب")
        with st.form("add_task_form", clear_on_submit=True):
            t_title = st.text_input("عنوان المهمة")
            t_subject = st.text_input("اسم المادة")
            t_type = st.selectbox("النوع", ["اختبار", "مشروع", "واجب"])
            t_due = st.date_input("تاريخ التسليم", min_value=datetime.date.today())
            t_hours = st.number_input("الساعات التقديرية", 0.5, 50.0, 3.0, 0.5)
            t_diff = st.slider("الصعوبة", 1, 5, 3)
            if st.form_submit_button("➕ إضافة المهمة") and t_title and t_subject:
                data["tasks"].append({"title": t_title, "subject": t_subject, "type": t_type, "due_date": t_due.strftime("%Y-%m-%d"), "est_hours": float(t_hours), "difficulty": int(t_diff), "completed": False})
                save_data(data)
                st.rerun()

    with col_form2:
        st.subheader("🏫 إضافة محاضرة للجدول")
        with st.form("add_schedule_form", clear_on_submit=True):
            s_day = st.selectbox("اليوم", ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس"])
            s_subject = st.text_input("اسم المادة")
            s_start = st.time_input("وقت البداية", datetime.time(8, 0))
            s_end = st.time_input("وقت النهاية", datetime.time(10, 0))
            if st.form_submit_button("➕ إضافة للجدول") and s_subject:
                data["schedule"].append({"day": s_day, "subject": s_subject, "start_time": s_start.strftime("%H:%M"), "end_time": s_end.strftime("%H:%M")})
                save_data(data)
                st.rerun()

with tab4:
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("📈 مستوى الأداء في المواد (%)")
        if data["grades"]:
            df_grades = pd.DataFrame(data["grades"])
            avg_by_subj = df_grades.groupby("subject", as_index=False)["percentage"].mean()
            chart_grades = alt.Chart(avg_by_subj).mark_bar().encode(
                x=alt.X("subject:N", title="المادة", sort="-y"),
                y=alt.Y("percentage:Q", title="النسبة (%)", scale=alt.Scale(domain=[0, 100])),
                color=alt.Color("subject:N", legend=None)
            ).properties(height=320)
            st.altair_chart(chart_grades, use_container_width=True)

    with col_chart2:
        st.subheader("⏳ توزيع ساعات المذاكرة")
        if prioritized_tasks:
            df_t = pd.DataFrame(prioritized_tasks)
            hrs_by_subj = df_t.groupby("subject", as_index=False)["est_hours"].sum()
            chart_hours = alt.Chart(hrs_by_subj).mark_arc(innerRadius=45).encode(
                theta=alt.Theta("est_hours:Q"),
                color=alt.Color("subject:N", title="المادة")
            ).properties(height=320)
            st.altair_chart(chart_hours, use_container_width=True)

    st.divider()
    st.subheader("🏅 تسجيل درجة جديدة")
    with st.form("add_grade_form", clear_on_submit=True):
        g1, g2, g3, g4 = st.columns(4)
        g_subject = g1.text_input("المادة")
        g_assess = g2.text_input("التقييم")
        g_score = g3.number_input("درجتك", 0.0, 100.0, 18.0)
        g_max = g4.number_input("الدرجة العظمى", 1.0, 100.0, 20.0)
        if st.form_submit_button("💾 حفظ الدرجة") and g_subject and g_assess:
            pct = round((g_score / g_max) * 100, 2)
            data["grades"].append({"subject": g_subject, "assessment": g_assess, "score": float(g_score), "max_score": float(g_max), "percentage": pct})
            save_data(data)
            st.rerun()