import pandas as pd
from datasets import load_dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import pickle

def train_final_model():
    """
    Train model using FreedomIntelligence/Disease_Database from Hugging Face.
    
    Uses:
    - 'common_symptom' as the symptom input text
    - 'disease' as the label
    - 'treatment' optionally stored but not used for classification
    """
    print("--- Starting the final model training process... ---")
    
    # --- 1. Load the dataset ---
    try:
        dataset = load_dataset("FreedomIntelligence/Disease_Database", "en", split="train")
        df = dataset.to_pandas()
        print("... Dataset downloaded and loaded successfully!")
        print("Columns available:", df.columns.tolist())    
        
    except Exception as e:
        print(f"ERROR: Could not download the dataset. Details: {e}")
        return
    
    # --- 2. Data preparation ---
    # Ensure these columns exist
    required_cols = ['common_symptom', 'disease', 'treatment']
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"Expected column '{col}' not found in dataset. Available: {df.columns.tolist()}")
    
    # Select and drop missing
    df_clean = df[['common_symptom', 'disease', 'treatment']].dropna().reset_index(drop=True)
    
    # Rename for consistency
    df_clean = df_clean.rename(columns={
        'common_symptom': 'Symptoms',
        'disease': 'Disease',
        'treatment': 'Treatment'
    })
    
    print(f"... After cleaning, dataset has {len(df_clean)} records.")
    
    # Rename for consistency
   
    K = 100  # change this to 50, 200, etc. depending on your prototype
    top_diseases = df_clean['Disease'].value_counts().nlargest(K).index
    df_clean = df_clean[df_clean['Disease'].isin(top_diseases)].reset_index(drop=True)
    print(f"... Filtered dataset to Top-{K} diseases, now {len(df_clean)} records remain.")
    
    # --- 3. Feature / Label ---
    X = df_clean['Symptoms']
    y = df_clean['Disease']
    
    # --- 4. Vectorization ---
    vectorizer = TfidfVectorizer(max_features=1500, stop_words='english')
    X_vectorized = vectorizer.fit_transform(X)
    print("... Symptoms have been processed into a numerical format.")
    
    # --- 5. Model training ---
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_vectorized, y)
    print("--- Final Disease Prediction Model has been trained successfully! ---")
    
    # --- 6. Save model, vectorizer, dataset lookup ---
    with open('final_disease_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    print("... Trained model saved to 'final_disease_model.pkl'")
    
    with open('final_vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
    print("... Symptom vectorizer saved to 'final_vectorizer.pkl'")
    
    df_clean.to_csv('final_remedy_dataset.csv', index=False)
    print("... Cleaned dataset saved to 'final_remedy_dataset.csv'")
    

if __name__ == '__main__':
    train_final_model()
