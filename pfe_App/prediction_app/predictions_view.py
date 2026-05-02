import json
import pandas as pd
import numpy as np 
from django.shortcuts import render
import joblib 
from sklearn.decomposition import PCA
import os
from django.conf import settings
from sklearn.preprocessing import StandardScaler


def predictions_view(request):
    context = {
        'risk_data': "[]", 'scatter_c0': "[]", 'scatter_c1': "[]", 'scatter_c2': "[]", 'etudiants': []
    }

    if request.method == 'POST' and request.FILES.get('fichier_etudiants'):
        df = pd.read_csv(request.FILES['fichier_etudiants'])
        
        path_ann = os.path.abspath(os.path.join(settings.BASE_DIR,'..', 'ML_model', 'ann_model_risque.joblib'))
        path_kmeans = os.path.abspath(os.path.join(settings.BASE_DIR,'..', 'ML_model', 'kmeans_model.joblib'))
        
        ann_model = joblib.load(path_ann)
        kmeans_model = joblib.load(path_kmeans)
        
        df['family_income_num'] = df['family_income'].map({'Less Than 5000': 1 , '5000-10000': 2 , '10000-20000': 3, 'More Than 20000':4})
        df['Internet_Access_num']= df['has_internet_access'].map({'Yes': 1, 'No':0})

        X_ann = df[['Eng1', 'Math1', 'Phy1', 'Chem1', 'Bio1', 'Eng2', 'Math2', 'Phy2', 'Chem2', 'Bio2', 'Internet_Access_num','family_income_num']]
        X_kmeans= df[['Eng1', 'Math1', 'Phy1', 'Chem1', 'Bio1', 'Eng2', 'Math2', 'Phy2', 'Chem2', 'Bio2', 'Eng3', 'Math3', 'Phy3', 'Chem3','Bio3' , 'Internet_Access_num']] 
        

        scaler = StandardScaler()
        X_scaler_ann = scaler.fit_transform(X_ann)

        scaler_clustring=StandardScaler()
        x_scaler_clustring = scaler_clustring.fit_transform(X_kmeans)
        df['Groupe_Soutien'] = kmeans_model.predict(x_scaler_clustring).astype(int)
        
        df['Moyenne_Generale_Test'] = df[['Math1', 'Phy1', 'Eng1', 'Math2', 'Phy2', 'Eng2']].mean(axis=1)
        cluster_means = df.groupby('Groupe_Soutien')['Moyenne_Generale_Test'].mean().to_dict()
        sorted_clusters = sorted(cluster_means.items(), key=lambda item: item[1])

        cluster_faible = sorted_clusters[0][0]  
        cluster_moyen = sorted_clusters[1][0]  
        cluster_fort = sorted_clusters[2][0]    

        context['cluster_faible'] = cluster_faible
        context['cluster_moyen'] = cluster_moyen
        context['cluster_fort'] = cluster_fort

        raw_predictions = ann_model.predict(X_scaler_ann)
        if len(raw_predictions.shape) > 1 and raw_predictions.shape[1] == 1:
            df['Target_Risk'] = (raw_predictions > 0.5).astype(int).flatten()
        else:
            df['Target_Risk'] = raw_predictions.astype(int)

        pca = PCA(n_components=2)
        df['PCA1'] = pca.fit_transform(x_scaler_clustring)[:, 0].astype(float)
        df['PCA2'] = pca.fit_transform(x_scaler_clustring)[:, 1].astype(float)


        if 'ID_Etudiant' not in df.columns:
            df['ID_Etudiant'] = [str(i+1) for i in range(len(df))]

        safe_count = int(len(df[df['Target_Risk'] == 0]))
        danger_count = int(len(df[df['Target_Risk'] == 1]))
        context['risk_data'] = json.dumps([safe_count, danger_count])

        def safe_scatter(cluster_id):
            subset = df[df['Groupe_Soutien'] == cluster_id]
            return [{'x': float(row['PCA1']), 'y': float(row['PCA2'])} for _, row in subset.iterrows()]

        context['scatter_c0'] = json.dumps(safe_scatter(0))
        context['scatter_c1'] = json.dumps(safe_scatter(1))
        context['scatter_c2'] = json.dumps(safe_scatter(2))

        if 'gpa_range' not in df.columns:
            df['gpa_range'] = "Inconnu" 
            
        etudiants_list = df[['ID_Etudiant', 'gpa_range', 'has_internet_access', 'Groupe_Soutien', 'Target_Risk']].to_dict('records')
        context['etudiants'] = etudiants_list

    return render(request, 'predictions.html', context)