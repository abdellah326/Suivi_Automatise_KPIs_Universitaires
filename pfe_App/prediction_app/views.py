from django.shortcuts import render
import pandas as pd
from django.http import HttpResponse
import json


def dashboard_view(request):
    # 1. البزطام (Context) خاوي في الأول
    context = {
        'total_etudiants': "--", 'sans_internet': "--", 'extra_activites': "--", 'filles': "--", 'garcons': "--",
        'gpa_labels': "[]", 'gpa_data': "[]",
        'parent_edu_labels': "[]", 'parent_edu_data': "[]",
        'internet_oui': "[]", 'internet_non': "[]",
        'evo_t1': "[]", 'evo_t2': "[]",
    }

    if request.method == 'POST' and request.FILES.get('fichier_etudiants'):
        fichier = request.FILES['fichier_etudiants']
        df = pd.read_csv(fichier)
        
        # --- حساب الـ KPIs لي ديجا خدامين عندك ---
        context['total_etudiants'] = len(df)
        context['sans_internet'] = len(df[df['has_internet_access'].astype(str).str.strip().str.lower() == 'no'])
        context['extra_activites'] = len(df[df['has_extracurricular'].astype(str).str.strip().str.lower() == 'yes'])
        context['filles'] = len(df[df['Sex'].astype(str).str.strip().str.upper().str.startswith('F')])
        context['garcons'] = len(df[df['Sex'].astype(str).str.strip().str.upper().str.startswith('M')])

        # --- داتا ديال المبيان 1: GPA ---
        if 'gpa_range' in df.columns:
            gpa_counts = df['gpa_range'].value_counts()
            context['gpa_labels'] = json.dumps(gpa_counts.index.tolist())
            context['gpa_data'] = json.dumps(gpa_counts.values.tolist())

        # --- داتا ديال المبيان 2: تعليم الآباء ---
        if 'parent_education' in df.columns:
            edu_counts = df['parent_education'].value_counts()
            context['parent_edu_labels'] = json.dumps(edu_counts.index.tolist())
            context['parent_edu_data'] = json.dumps(edu_counts.values.tolist())

        # --- داتا ديال المبيان 3: تأثير الأنترنيت ---
        df_oui = df[df['has_internet_access'].astype(str).str.strip().str.lower() == 'yes']
        df_non = df[df['has_internet_access'].astype(str).str.strip().str.lower() == 'no']
        
        # كنحسبو المعدل ديال المواد
        context['internet_oui'] = json.dumps([
            round(df_oui['Math1'].mean(), 2) if 'Math1' in df_oui else 0,
            round(df_oui['Phy1'].mean(), 2) if 'Phy1' in df_oui else 0,
            round(df_oui['Eng1'].mean(), 2) if 'Eng1' in df_oui else 0
        ])
        context['internet_non'] = json.dumps([
            round(df_non['Math1'].mean(), 2) if 'Math1' in df_non else 0,
            round(df_non['Phy1'].mean(), 2) if 'Phy1' in df_non else 0,
            round(df_non['Eng1'].mean(), 2) if 'Eng1' in df_non else 0
        ])

        # --- داتا ديال المبيان 4: التطور بين الدورة 1 و 2 ---
        t1_cols = ['Math1', 'Phy1', 'Chem1', 'Eng1', 'Bio1']
        t2_cols = ['Math2', 'Phy2', 'Chem2', 'Eng2', 'Bio2']
        
        context['evo_t1'] = json.dumps([round(df[col].mean(), 2) for col in t1_cols if col in df.columns])
        context['evo_t2'] = json.dumps([round(df[col].mean(), 2) for col in t2_cols if col in df.columns])

    return render(request, 'index.html', context)