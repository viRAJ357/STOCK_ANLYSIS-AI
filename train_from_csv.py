import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import io
import sys

# Windows terminal me unicode errors avoid karne ke liye
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    print("Loading massive dataset (Saara data load ho raha hai)...")
    try:
        df = pd.read_csv('massive_training_dataset.csv')
    except Exception as e:
        print("Dataset nahi mila! Pehle dataset banayein.")
        return
        
    print(f"\nDataset loaded successfully with {len(df)} rows!")
    
    features = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_10', 'SMA_50', 'RSI', 'Return']
    
    # Check if any missing values exist just in case
    df = df.dropna(subset=features + ['Target'])
    
    X = df[features]
    y = df['Target']
    
    # Training on 100% of the data (Poore 2 Lakh+ data points par ek sath)
    print(f"\nModel ko saare {len(X)} data points par ek sath train kiya ja raha hai (100% data)... please wait!")
    
    # Powerful Random Forest for large data
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, max_depth=10)
    model.fit(X, y)
    
    print("\n✅ Training complete on 100% of the massive dataset!")
    
    print("Model ko 'stock_model.pkl' mein overwrite/save kar rahe hain...")
    joblib.dump(model, 'stock_model.pkl')
    print("✅ Naya, zyada powerful Model successfully save ho gaya hai!")

if __name__ == "__main__":
    main()
